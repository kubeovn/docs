# Egress Gateway BGP 和 EVPN 支持

!!! warning "实验性功能"

    BGP 和 EVPN 支持目前为实验性功能，后续版本可能会发生变更。我们欢迎更多的使用和意见来完善这个功能。

    当前存在以下限制：

    - 仅实现了 L3VPN，尚不支持 L2VPN
    - 不支持 FRR 热重载（配置变更需要重启 Pod）
    - 不支持 BGP BFD

## 概述

[VPC Egress Gateway](./vpc-egress-gateway.md) 支持通过 BGP 和 EVPN/VXLAN 与外部网络建立动态路由。其主要架构为在 Egress Gateway Pod 内运行 FRR（Free Range Routing）容器来处理 BGP 和 EVPN 的控制面与数据面。Gateway 的 init 容器会根据 BgpConf 和 EvpnConf 资源自动渲染 FRR 配置。

启用 BGP 时，Egress Gateway 会通过 BGP 协议与外部路由器建立邻居关系，通告和学习路由。启用 EVPN 时，init 脚本会在 Pod 内创建 Linux VRF、bridge 和 VXLAN 设备，使用 L2VPN EVPN 地址族进行路由交换。VXLAN 封装仅发生在 Egress Gateway Pod 内，Kubernetes 节点间的网络仍然使用 Geneve。

> 此功能与[高级功能中的 BGP 支持](../advance/with-bgp.md)不同，后者使用 kube-ovn-speaker 实现 Pod/子网/Service 路由通告。

## 使用要求

使用 BGP/EVPN 功能前，请确保已满足 [VPC Egress Gateway](./vpc-egress-gateway.md) 的使用要求，包括 [Multus-CNI](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/quickstart.md){: target="_blank" } 的部署。

此外，还需要一个支持 BGP（以及可选的 EVPN）的外部路由器或网络设备作为 BGP 邻居。

## 使用方法

### 创建 BgpConf 资源

BgpConf 是一个集群级别的资源，用于定义 BGP 配置。示例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: BgpConf
metadata:
  name: bgp-conf-6502
spec:
  localASN: 65002
  peerASN: 65001
  neighbours:
    - 10.0.1.1
  holdTime: 90s
  keepaliveTime: 30s
  connectTime: 10s
  ebgpMultiHop: true
```

上述资源定义了一个本地 AS 号为 65002、对端 AS 号为 65001 的 BGP 配置，邻居地址为 10.0.1.1，并启用了 EBGP Multi-Hop。

### 创建 EvpnConf 资源

EvpnConf 是一个集群级别的资源，用于定义 EVPN 配置。EvpnConf 需要与 BgpConf 配合使用，不可单独使用。示例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: EvpnConf
metadata:
  name: evpn-conf-1016
spec:
  vni: 1016
  routeTargets:
    - "65000:1016"
```

上述资源定义了一个 VNI 为 1016 的 EVPN 配置，Route Target 为 `65000:1016`。

### 创建启用 BGP/EVPN 的 VPC Egress Gateway

首先按照 [VPC Egress Gateway](./vpc-egress-gateway.md) 文档创建 NetworkAttachmentDefinition 和对应的子网。

然后在 VpcEgressGateway 的 `.spec` 中通过 `bgpConf` 和 `evpnConf` 字段引用对应的配置资源。示例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: VpcEgressGateway
metadata:
  name: gateway1
  namespace: default
spec:
  vpc: ovn-cluster
  replicas: 1
  externalIPs:
    - 10.0.1.13
  internalIPs:
    - 10.16.0.13
  externalSubnet: macvlan1
  bgpConf: bgp-conf-6502
  evpnConf: evpn-conf-1016
  policies:
    - snat: false
      subnets:
        - ovn-default
    - snat: false
      ipBlocks:
        - 10.17.0.0/16
```

上述资源会创建一个启用了 BGP 和 EVPN 的 VPC Egress Gateway。Gateway Pod 内会运行 FRR 容器，通过 BGP EVPN 与外部路由器交换路由信息，并通过 VXLAN 隧道转发流量。由于路由由 BGP/EVPN 管理，策略中的 `snat` 设置为 `false`。

### 仅使用 BGP（不启用 EVPN）

如果仅需使用 BGP 进行路由通告而不使用 EVPN/VXLAN，只需设置 `bgpConf` 字段而不设置 `evpnConf` 字段。此模式下 FRR 将运行纯 BGP IPv4 Unicast 地址族。示例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: VpcEgressGateway
metadata:
  name: gateway-bgp-only
  namespace: default
spec:
  vpc: ovn-cluster
  replicas: 1
  externalSubnet: macvlan1
  bgpConf: bgp-conf-6502
  policies:
    - snat: true
      subnets:
        - ovn-default
```

## 配置参数

### BgpConf

| 字段 | 类型 | 可选 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `localASN` | `uint32` | 否 | - | 本地 AS 号。 | `65002` |
| `peerASN` | `uint32` | 否 | - | 对端 AS 号。 | `65001` |
| `routerId` | `string` | 是 | Pod IP | BGP Router ID。 | `10.0.1.13` |
| `neighbours` | `string array` | 否 | - | BGP 邻居 IP 地址列表。 | `10.0.1.1` |
| `password` | `string` | 是 | - | BGP 认证密码。 | `secret` |
| `holdTime` | `string (duration)` | 是 | - | BGP Hold 时间。 | `90s` |
| `keepaliveTime` | `string (duration)` | 是 | - | BGP Keepalive 时间。 | `30s` |
| `connectTime` | `string (duration)` | 是 | - | BGP 连接计时器。 | `10s` |
| `ebgpMultiHop` | `boolean` | 是 | `false` | 是否启用 EBGP Multi-Hop。 | `true` |

### EvpnConf

| 字段 | 类型 | 可选 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `vni` | `uint32` | 否 | - | VXLAN Network Identifier。 | `1016` |
| `routeTargets` | `string array` | 否 | - | 用于导入和导出的 Route Target 列表。 | `65000:1016` |

### VpcEgressGateway 新增字段

以下字段为 VpcEgressGateway `.spec` 中新增的 BGP/EVPN 相关字段，完整的 VpcEgressGateway 配置参数请参考 [Egress Gateway](./vpc-egress-gateway.md) 文档中的配置参数章节。

| 字段 | 类型 | 可选 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bgpConf` | `string` | 是 | - | 引用的 BgpConf 资源名称。设置后将在 Egress Gateway 中启用 BGP。 | `bgp-conf-6502` |
| `evpnConf` | `string` | 是 | - | 引用的 EvpnConf 资源名称。需要同时设置 `bgpConf`。设置后将在 Egress Gateway 中启用 EVPN/VXLAN。 | `evpn-conf-1016` |
