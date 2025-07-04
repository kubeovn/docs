# 节点本地 DNS 缓存和 Kube-OVN 适配

NodeLocal DNSCache 是通过集群节点上作为 DaemonSet 运行 DNS 缓存来提高集群 DNS 性能，该功能也可以和 Kube-OVN 适配。

## 节点本地 DNS 缓存部署

### 部署 Kubernetes 的节点本地 DNS 缓存

该步骤参考 Kubernetes 官网配置 [Nodelocaldnscache](https://kubernetes.io/zh-cn/docs/tasks/administer-cluster/nodelocaldns/)。

使用以下脚本部署：

```bash
#!bin/bash

localdns=169.254.20.10
domain=cluster.local
kubedns=10.96.0.10

wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml
sed -i "s/__PILLAR__LOCAL__DNS__/$localdns/g; s/__PILLAR__DNS__DOMAIN__/$domain/g; s/,__PILLAR__DNS__SERVER__//g; s/__PILLAR__CLUSTER__DNS__/$kubedns/g" nodelocaldns.yaml

kubectl apply -f nodelocaldns.yaml
```

修改每个节点上的 kubelet 配置文件，将 `/var/lib/kubelet/config.yaml` 中的 clusterDNS 字段修改为本地 DNS IP 169.254.20.10，然后重启 kubelet 服务。

### Kube-OVN 相应 DNS 配置

部署好 Kubernetes 的 Nodelocal DNScache 组件后，Kube-OVN 需要做出下面修改：

#### Underlay Subnet 开启 U2O 开关

如果是 Underlay Subnet 需要使用本地 DNS 功能，需要开启 U2O 功能，即在 `kubectl edit subnet {your subnet}` 中配置 `spec.u2oInterconnection = true` , 如果是 Overlay Subnet 则不需要这步操作。

#### 给 Kube-ovn-controller 指定对应的本地 DNS IP

```bash
kubectl edit deployment kube-ovn-controller -n kube-system
```

给 `spec.template.spec.containers.args` 增加字段 `--node-local-dns-ip=169.254.20.10`

#### 重建已经创建的 Pod

这步原因是让 Pod 重新生成 `/etc/resolv.conf` 让 nameserver 指向本地 DNS IP，如果没有重建 Pod 的 nameserver 将仍然使用集群的 DNS ClusterIP。同时 u2o 开关如果开启也需要重建 Pod 来重新生成 Pod 网关。

## 验证节点本地 DNS 缓存功能

以上配置完成后可以找到 Pod 验证如下，可以看到 Pod 的 DNS 服务器是指向本地 169.254.20.10，并成功解析域名：

```bash
# kubectl exec -it pod1 -- nslookup github.com
Server:         169.254.20.10
Address:        169.254.20.10:53


Name:   github.com
Address: 20.205.243.166
```

也可以在节点抓包验证如下，可以看到 DNS 查询报文通过 ovn0 网卡到达本地的 DNS 服务，DNS 响应报文原路返回：

```bash
# tcpdump -i any port 53

06:20:00.441889 659246098c56_h P   ifindex 17 00:00:00:73:f1:06 ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1291+ A? baidu.com. (27)
06:20:00.441889 ovn0  In  ifindex 7 00:00:00:50:32:cd ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1291+ A? baidu.com. (27)
06:20:00.441950 659246098c56_h P   ifindex 17 00:00:00:73:f1:06 ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1611+ AAAA? baidu.com. (27)
06:20:00.441950 ovn0  In  ifindex 7 00:00:00:50:32:cd ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1611+ AAAA? baidu.com. (27)
06:20:00.442203 ovn0  Out ifindex 7 00:00:00:52:99:d8 ethertype IPv4 (0x0800), length 145: 169.254.20.10.53 > 10.16.0.2.40230: 1611* 0/1/0 (97)
06:20:00.442219 659246098c56_h Out ifindex 17 00:00:00:ea:b3:5e ethertype IPv4 (0x0800), length 145: 169.254.20.10.53 > 10.16.0.2.40230: 1611* 0/1/0 (97)
06:20:00.442273 ovn0  Out ifindex 7 00:00:00:52:99:d8 ethertype IPv4 (0x0800), length 125: 169.254.20.10.53 > 10.16.0.2.40230: 1291* 2/0/0 A 39.156.66.10, A 110.242.68.66 (77)
06:20:00.442278 659246098c56_h Out ifindex 17 00:00:00:ea:b3:5e ethertype IPv4 (0x0800), length 125: 169.254.20.10.53 > 10.16.0.2.40230: 1291* 2/0/0 A 39.156.66.10, A 110.242.68.66 (77)
```

## 注意事项

**⚠️ 注意：**  
如果环境中配置了 NetworkPolicy，需要确保在 NetworkPolicy 中额外放行本地 DNS IP（如 169.254.20.10）和节点的 CIDR，以避免 NetworkPolicy 拦截 DNS 请求和响应流量，导致 Pod 无法正常解析域名。

### NetworkPolicy 配置示例

以下是一个允许 Pod 访问本地 DNS 缓存和节点网络的 NetworkPolicy 配置示例：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-local-dns-and-node-cidr
  namespace: default  # 根据实际需要修改命名空间
spec:
  podSelector: {}  # 应用到所有 Pod，可根据需要添加标签选择器
  policyTypes:
  - Ingress
  - Egress
  egress:
  # 允许访问本地 DNS 缓存
  - to:
    - ipBlock:
        cidr: 169.254.20.10/32
  # 允许访问节点 CIDR（请根据实际节点网络 CIDR 修改）
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8  # 示例节点 CIDR，请根据实际情况修改
  ingress:
  # 允许来自本地 DNS 缓存的响应
  - from:
    - ipBlock:
        cidr: 169.254.20.10/32
  # 允许来自节点 CIDR 的流量（请根据实际节点网络 CIDR 修改）
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8  # 示例节点 CIDR，请根据实际情况修改
```

**配置说明：**

- `169.254.20.10/32`：本地 DNS 缓存的 IP 地址
- `10.0.0.0/8`：示例节点 CIDR，请根据实际的节点网络段进行修改
