# 中科驭数网卡 Offload 支持

!!! note
  本文所述方案在 2024 年经过验证，但目前硬件网卡可能已经有了新的特性，当时的一些限制也可能已经被解决。请咨询您的硬件供应商，了解最新的技术限制和能力。

## 前置条件

- 中科驭数 2200E 系列智能网卡
- 中科驭数 HADOS 敏捷异构软件开发平台
- BIOS 开启 SR-IOV

## 安装流程

### 配置 SR-IOV

1. 根据中科驭数 2200E 网卡的 vendor ID（1f47），找到本网卡在主机上的设备 ID，以下为（00:0a.0）和（00:0b.0），分别对应 2200E 上的两个光口，可以根据和光纤连接情况选用。

```bash
lspci | grep 1f47
00:0a.0 Ethernet controller: Device 1f47:1001 (rev 10)
00:0b.0 Ethernet controller: Device 1f47:1001 (rev 10)
```

2. 查看每一个总线对应的设备最大可分配的 VF 数量：

``` bash
cat /sys/bus/pci/devices/0000\:00\:0a.0/sriov_totalvfs
256
```

3. 按需创建 VF，总数不要超过上述查询的 VF 数量：

```bash
echo 7 > /sys/bus/pci/devices/0000\:00\:0a.0/sriov_numvfs
```

4. 确认 VF 创建情况

```bash
lspci | grep 1f47
00:0a.0 Ethernet controller: Device 1f47:1001 (rev 10)
00:0a.1 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.2 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.3 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.4 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.5 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.6 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.7 Ethernet controller: Device 1f47:110f (rev 10)
00:0b.0 Ethernet controller: Device 1f47:1001 (rev 10)
```

### 安装并运行 SR-IOV Device Plugin

1. 创建 SR-IOV 相关 Configmap，便于后续安装的 SR-IOV Device Plugin 根据该配置找到节点上的 VF 资源并提供给 Pod 使用：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sriovdp-config
  namespace: kube-system
data:
  config.json: |
    {
        "resourceList": [{
                "resourceName": "sriov_dpu",
                "resourcePrefix": "yusur.tech",
                "selectors": {
                    "vendors": ["1f47"],
                    "devices": ["110f"]
                }}
        ]
    }
 
```

2. 安装并运行 SR-IOV Device Plugin

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/sriov-network-device-plugin/v3.6.2/deployments/sriovdp-daemonset.yaml
```

3. 检查 SR-IOV 资源是否已经被注册到 kubernetes Node 的资源池中：

```bash
kubectl describe node node1 | grep yusur
  yusur.tech/sriov_dpu:  7
  yusur.tech/sriov_dpu:  7
  yusur.tech/sriov_dpu  0           0
```

## 安装 Multus-CNI

安装 Multus-CNI，负责为 Kube-OCN 传递选定 SRIOV 设备的 Device ID：

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/v4.0.2/deployments/multus-daemonset-thick.yml
```

创建 `NetworkAttachmentDefinition`：

```yaml
apiVersion:
  "k8s.cni.cncf.io/v1"
kind:
  NetworkAttachmentDefinition
metadata:
  name: test
  namespace: kube-system
  annotations:
    k8s.v1.cni.cncf.io/resourceName: yusur.tech/sriov_dpu
spec:
  config: '{
    "cniVersion": "0.3.1",
    "name": "kube-ovn",
    "plugins":[
        {
            "type":"kube-ovn",
            "server_socket":"/run/openvswitch/kube-ovn-daemon.sock",
            "provider": "test.kube-system.ovn"
        },
        {
            "type":"portmap",
            "capabilities":{
                "portMappings":true
            }
        }
    ]
}
```

- `provider`: 格式为当前 NetworkAttachmentDefinition 的 `{name}.{namespace}.ovn`。

## Kube-OVN 中开启卸载模式

1. 下载 安装脚本

```bash
wget https://github.com/kubeovn/kube-ovn/blob/release-1.12/dist/images/install.sh
```

2. 修改相关参数，IFACE 需要为物理网卡名，该网卡需要有可路由 IP：

```bash
ENABLE_MIRROR=${ENABLE_MIRROR:-false}
HW_OFFLOAD=${HW_OFFLOAD:-true}
ENABLE_LB=${ENABLE_LB:-false}
IFACE="p0"
```

3. 安装 kube-ovn

```bash
bash install.sh
```

### 创建使用 VF 网卡的 pod

可以使用如下 yaml 格式创建使用 VF 进行网络卸载加速的 Pod：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  namespace: default
  annotations:
    v1.multus-cni.io/default-network: kube-system/test
spec:
  containers:
    - name: nginx
      image: docker.io/library/nginx:alpine
      resources:
        requests:
          yusur.tech/sriov_dpu: '1'
        limits:
          yusur.tech/sriov_dpu: '1'
```

- `v1.multus-cni.io/default-network`: 为上一步骤中 `NetworkAttachmentDefinition` 的 `{namespace}/{name}`。

### Offload 验证

可通过在 Pod 运行节点的 `ovs-ovn` 容器中运行下面的命令观察卸载是否成功：

```bash
# ovs-appctl dpctl/dump-flows -m type=offloaded
ufid:67c2e10f-92d4-4574-be70-d072815ff166, skb_priority(0/0),skb_mark(0/0),ct_state(0/0x23),ct_zone(0/0),ct_mark(0/0),ct_label(0/0),recirc_id(0),dp_hash(0/0),in_port(d85b161b6840_h),packet_type(ns=0/0,id=0/0),eth(src=0a:c9:1c:70:01:09,dst=8a:18:a4:22:b7:7d),eth_type(0x0800),ipv4(src=10.0.1.10,dst=10.0.1.6,proto=6,tos=0/0x3,ttl=0/0,frag=no),tcp(src=60774,dst=9001), packets:75021, bytes:109521630, offload_packets:75019, offload_bytes:109521498, used:3.990s,offloaded:yes,dp:tc, actions:set(tunnel(tun_id=0x5,dst=192.168.201.12,ttl=64,tp_dst=6081,geneve({class=0x102,type=0x80,len=4,0xa0006}),flags(csum|key))),genev_sys_6081
ufid:7940666e-a0bd-42a5-8116-1e84e81bb338, skb_priority(0/0),tunnel(tun_id=0x5,src=192.168.201.12,dst=192.168.201.11,ttl=0/0,tp_dst=6081,geneve({class=0x102,type=0x80,len=4,0x6000a}),flags(+key)),skb_mark(0/0),ct_state(0/0),ct_zone(0/0),ct_mark(0/0),ct_label(0/0),recirc_id(0),dp_hash(0/0),in_port(genev_sys_6081),packet_type(ns=0/0,id=0/0),eth(src=8a:18:a4:22:b7:7d,dst=0a:c9:1c:70:01:09),eth_type(0x0800),ipv4(src=10.0.1.6,dst=10.0.1.10,proto=6,tos=0/0,ttl=0/0,frag=no),tcp(src=9001,dst=60774), packets:6946, bytes:459664, offload_packets:6944, offload_bytes:459532, used:4.170s, dp:tc,offloaded:yes,actions:d85b161b6840_h
```
