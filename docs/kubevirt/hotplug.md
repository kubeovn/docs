# 网卡热插拔

Kube-OVN 和 [Multus Dynamic Networks Controller](https://github.com/k8snetworkplumbingwg/multus-dynamic-networks-controller) 共同协作可实现 KubeVirt 在 v1.4.0 支持的[网卡热插拔](https://kubevirt.io/user-guide/network/hotplug_interfaces/)功能，在无需重启 VM 的情况下对附属网卡进行添加或删除。

## 准备工作

以 [Thick 模式](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/thick-plugin.md)安装 Multus：

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/refs/heads/master/deployments/multus-daemonset-thick.yml
```

安装 [Multus Dynamic Networks Controller](https://github.com/k8snetworkplumbingwg/multus-dynamic-networks-controller)：

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-dynamic-networks-controller/refs/heads/main/manifests/dynamic-networks-controller.yaml
```

## 创建附属网络

### 创建 NetworkAttachmentDefinition

将 `provider` 的后缀设置为 `ovn`：

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: attachnet
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "attachnet.default.ovn"
    }'
```

- `spec.config.type`: 设置为 `kube-ovn` 来触发 CNI 插件使用 Kube-OVN 子网。
- `server_socket`: Kube-OVN 通信使用的 socket 文件。 默认位置为 `/run/openvswitch/kube-ovn-daemon.sock`。
- `provider`: 当前 NetworkAttachmentDefinition 的 `<name>.<namespace>.ovn` , Kube-OVN 将会使用这些信息找到对应的 Subnet 资源，注意后缀需要设置为 ovn。

### 创建一个 Kube-OVN Subnet

如果以 Kube-OVN 作为附加网卡，则 `provider` 应该设置为对应的 NetworkAttachmentDefinition 的 `<name>.<namespace>.ovn`，并要以 `ovn` 作为后缀结束。
用 Kube-OVN 提供附加网卡，创建 Subnet 示例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: attachnet
spec:
  protocol: IPv4
  provider: attachnet.default.ovn
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  excludeIps:
  - 172.17.0.0..172.17.0.10
```

## 调整 VM 网络

使用下面的 yaml 创建 VM：

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-fedora
spec:
  runStrategy: Always
  template:
    spec:
      domain:
        devices:
          disks:
          - disk:
              bus: virtio
            name: containerdisk
          interfaces:
          - masquerade: {}
            name: defaultnetwork
          rng: {}
        resources:
          requests:
            memory: 1024M
      networks:
      - name: defaultnetwork
        pod: {}
      terminationGracePeriodSeconds: 0
      volumes:
      - containerDisk:
          image: quay.io/kubevirt/fedora-with-test-tooling-container-disk:devel
        name: containerdisk
```

### 新增网卡

修改 VM 的 Spec 增加新的网卡字段：

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-fedora
template:
  spec:
    domain:
      devices:
        interfaces:
        - name: defaultnetwork
          masquerade: {}
          # new interface
        - name: dyniface1
          bridge: {}
    networks:
    - name: defaultnetwork
      pod: {}
      # new network
    - name: dyniface1
      multus:
        networkName: attachnet
```

### 删除网卡

通过将 `interface` 的 `state` 设置为 `absent` 可以动态删除网卡：

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-fedora
template:
  spec:
    domain:
      devices:
        interfaces:
          - name: defaultnetwork
            masquerade: {}
          # set the interface state to absent 
          - name: dyniface1
            state: absent
            bridge: {}
    networks:
      - name: defaultnetwork
        pod: {}
      - name: dyniface1
        multus:
          networkName: attachnet
```
