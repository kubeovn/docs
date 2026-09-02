# 路由子网模式

在 `Subnet` 上设置 `spec.routed: true`，可以让 Pod 使用主机地址掩码（IPv4 为 `/32`，IPv6 为 `/128`），并通过子网网关转发所有流量。这样，子网不再作为共享的二层广播域，同一子网内 Pod 之间的流量也会经过 OVN 逻辑路由器。

## 创建路由子网

下面的示例创建一个 Overlay IPv4 路由子网：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: routed-subnet
spec:
  cidrBlock: 10.0.0.0/16
  gateway: 10.0.0.1
  protocol: IPv4
  provider: ovn
  routed: true
```

`spec.cidrBlock` 仍然用于 IPAM 地址分配，`routed` 只改变 Pod 网卡的地址掩码和路由。以地址 `10.0.0.5` 的 Pod 为例，CNI 会配置：

```text
ip addr add 10.0.0.5/32 dev eth0
ip route add 10.0.0.1/32 dev eth0
ip route add default via 10.0.0.1
```

IPv6 Pod 使用 `/128` 地址和对应的 IPv6 网关主机路由。

## 流量隔离行为

同一子网内的东西向流量会经过 OVN 逻辑路由器 hairpin，而不是在逻辑交换机上直接进行二层转发。路由子网的 OVN ACL 使用允许列表和默认拒绝策略：

- 只允许针对子网网关的 ARP/ND；
- 在两个 ACL 方向允许发往逻辑路由器端口 MAC 的 IP 帧；
- 允许从逻辑路由器端口 MAC 发出的 IP 帧；`from-lport` 方向还会校验数据包确实来自逻辑路由器端口，防止 Pod 伪造网关 MAC；
- 其他 IP、ARP 和 ND 流量均被拒绝。

当 `private: true` 时，经逻辑路由器进入子网的流量还会限制为本子网 hairpin、节点 Join CIDR 和 `allowSubnets` 中声明的网段。

## 路由注解

非 DPDK 网卡支持 Provider 路由注解（例如 `ovn.kubernetes.io/routes`）。在路由子网中，每条注解路由的下一跳必须是子网网关；使用 U2O 互联时，可以使用对应的 U2O 互联 IP。路由目的地址必须是合法的 CIDR，路由无法解析或安装时 CNI ADD 会失败。

由于路由子网只允许 Pod 解析子网网关，其他下一跳会被拒绝。`ovn.kubernetes.io/routed` 是另一个独立的 Pod 注解，仅表示 OVN 路由已经为 Pod 准备完成，不用于开启路由子网模式。

## 使用限制

- 仅支持 OVN Provider 子网；Overlay 子网可以直接使用，Underlay 子网必须启用 `logicalGateway` 或 `u2oInterconnection`，以提供 OVN 逻辑路由器端口。
- 不支持 `enableDHCP`、`enableIPv6RA`、`enableMulticastSnoop`、mac-only/BYO-DHCP 子网或自定义 `spec.acls`。
- 不支持 DPDK/vhost-user 网卡；这类网卡也不支持路由注解。
- 开启或关闭 `routed` 不会重新配置已有 Pod。修改后必须重新创建 Pod，才能应用新的地址掩码和路由。
