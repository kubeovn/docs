# Overlay 下路由方式网络打通

在一些场景下，网络环境不支持 Underlay 模式，但是依然需要 Pod 能和外部设施直接通过 IP 进行互访，
这时候可以使用路由方式将容器网络和外部联通。

> 路由模式只支持默认 VPC 下的 Overlay 网络和外部打通，在这种情况下，Pod IP 会直接进入底层网络，底层网络需要放开关于源地址和目地址的 IP 检查。

## 前提条件

- 此模式下，主机需要开放 `ip_forward`。
- 检查主机 iptables 规则中是否在 forward 链中是否有 Drop 规则，需要放行容器相关流量。
- 由于可能存在非对称路由的情况，主机需放行 ct 状态为 `INVALID` 的数据包。

## 设置步骤

对于需要对外直接路由的子网，需要将子网的 `natOutgoing` 设置为 `false`，关闭 nat 映射，使得 Pod IP 可以直接进入外部网络。

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: routed
spec:
  protocol: IPv4
  cidrBlock: 10.166.0.0/16
  default: false
  excludeIps:
  - 10.166.0.1
  gateway: 10.166.0.1
  gatewayType: distributed
  natOutgoing: false
```

此时，Pod 的数据包可以通过主机路由到达对端节点，但是对端节点还不知道回程数据包应该发送到哪里，需要添加回程路由。

如果对端主机和容器所在宿主机在同一个二层网络，我们可以直接在对端主机添加静态路由将容器网络的下一跳指向 Kubernetes 集群内的任意一台机器。

```bash
ip route add 10.166.0.0/16 via 192.168.2.10 dev eth0
```

`10.166.0.0/16` 为容器子网网段，`192.168.2.10` 为 Kubernetes 集群内任意一个节点。

若对端主机和容器所在宿主机不在同一个二层网络，则需要在路由器上配置相应的规则，通过路由器进行打通。

*注意*： 指定某个节点 IP 存在单点故障的可能，如果希望做到快速的故障切换可以通过 Keepalived 给多个节点设置 VIP，同时将路由的下一跳指向 VIP。

在一些虚拟化环境中，虚拟网络会将非对称流量识别为非法流量并丢弃。
此时需要将 Subnet 的 `gatewayType` 调整为 `centralized`，并在路由设置时将下一跳设置为 `gatewayNode` 节点的 IP。

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: routed
spec:
  protocol: IPv4
  cidrBlock: 10.166.0.0/16
  default: false
  excludeIps:
  - 10.166.0.1
  gateway: 10.166.0.1
  gatewayType: centralized
  gatewayNode: "node1"
  natOutgoing: false
```

如果对于部分流量（如访问外网的流量）仍然希望进行 nat 处理，请参考[默认 VPC NAT 策略规则](../advance/nat-policy-rule.en.md)。
