# DualStack

Kube-OVN 中不同的子网可以支持不同的协议，一个集群内可以同时存在 IPv4，IPv6 和双栈类型的子网。
我们推荐一个集群内使用统一的协议类型以简化使用和维护。

为了支持双栈，需要主机网络满足双栈幽囚，同时需要对 Kubernetes 相关参数做调整，
请参考 Kubernetes 的[双栈官方指导](https://kubernetes.io/docs/concepts/services-networking/dual-stack)。

## 创建双栈子网

在配置双栈时，只需要设置对应子网 CIDR 格式为 `cidr=<IPv4 CIDR>,<IPv6 CIDR>` 即可。
CIDR 顺序要求 IPv4 在前，IPv6 在后，如下所示：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata: 
  name: ovn-test
spec:
  cidrBlock: 10.16.0.0/16,fd00:10:16::/64
  excludeIps:
  - 10.16.0.1
  - fd00:10:16::1
  gateway: 10.16.0.1,fd00:10:16::1
```

如果需要在安装时默认子网使用双栈，需要在安装脚本中修改如下参数：

```bash
POD_CIDR="10.16.0.0/16,fd00:10:16::/64"
JOIN_CIDR="100.64.0.0/16,fd00:100:64::/64"
```

## 查看 Pod 地址

配置双栈网络的 Pod 将会从该子网同时分配 IPv4 和 IPv6 的地址，分配结果会显示在 Pod 的 annotation 中:
```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/allocated: "true"
    ovn.kubernetes.io/cidr: 10.16.0.0/16,fd00:10:16::/64
    ovn.kubernetes.io/gateway: 10.16.0.1,fd00:10:16::1
    ovn.kubernetes.io/ip_address: 10.16.0.9,fd00:10:16::9
    ovn.kubernetes.io/logical_switch: ovn-default
    ovn.kubernetes.io/mac_address: 00:00:00:14:88:09
    ovn.kubernetes.io/network_types: geneve
    ovn.kubernetes.io/routed: "true"
...
podIP: 10.16.0.9
  podIPs:
  - ip: 10.16.0.9
  - ip: fd00:10:16::9
```
