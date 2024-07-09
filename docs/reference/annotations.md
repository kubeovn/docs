# Annotation 使用说明

Kube-OVN 使用了大量的 Pod 和 Node Annotation 进行功能设置和信息传递，用户可以通过本文档了解各个 Annotation 的使用，方便问题排查和信息获取。

> 注意：部分 Annotation 可能会随着代码调整而进行变化。

## Pod Annotation

| Key                                    | Value                     | Description                                                                     |
| -------------------------------------- | ------------------------- | ------------------------------------------------------------------------------- |
| ovn.kubernetes.io/allocated            | `true` or `false`         | Pod 主网卡是否已被分配地址                                                      |
| ovn.kubernetes.io/routed               | `true` or `false`         | Pod 主网卡在 OVN 内的路由是否设置完成                                           |
| ovn.kubernetes.io/mac_address          | String                    | Pod 主网卡所分配到的 Mac 地址，创建 Pod 时可通过该 Annotation 设置固定 Mac 地址 |
| ovn.kubernetes.io/ip_address           | String                    | Pod 主网卡所分配到的 IP 地址，创建 Pod 时可通过该 Annotation 设置固定 IP 地址   |
| ovn.kubernetes.io/cidr                 | String                    | Pod 主网卡所属子网的 CIDR                                                       |
| ovn.kubernetes.io/gateway              | String                    | Pod 主网卡所属子网的 Gateway 地址                                               |
| ovn.kubernetes.io/ip_pool              | IP 列表，逗号间隔            | Pod 主网卡地址将从列表中选择，适用于 Workload 固定 IP 场景                      |
| ovn.kubernetes.io/bgp                  | `true`, `cluster`, `local`         | 是否对外通过 BGP 发布 Pod 地址                                                  |
| ovn.kubernetes.io/snat                 | String                    | Pod 访问集群外使用的 SNAT 地址                                                  |
| ovn.kubernetes.io/eip                  | String                    | Pod 访问集群外部和被集群外部访问所使用的 EIP 地址                               |
| ovn.kubernetes.io/vip                  | String                    | Pod 主网卡使用的预留 VIP，可通过该 Annotation 使用预先创建的 VIP 资源           |
| ovn.kubernetes.io/virtualmachine       | String                    | Pod 主网卡所属的 VirtualMachineInstance                                         |
| ovn.kubernetes.io/logical_router       | String                    | Pod 主网卡所属的 VPC                                                            |
| ovn.kubernetes.io/layer2_forward       | `true` or `false`         | Pod 主网卡在 OVN LSP 中是否增加 `unknown` 地址                                  |
| ovn.kubernetes.io/port_security        | `true` or `false`         | Pod 主网卡对应端口是否开启 Port Security                                        |
| ovn.kubernetes.io/logical_switch       | String                    | Pod 主网卡所属的 Subnet                                                         |
| ovn.kubernetes.io/vlan_id              | Int                       | Pod 主网卡所属 Subnet 的 Vlan ID                                                |
| ovn.kubernetes.io/ingress_rate         | Int                       | Pod 主网卡流入方向限速，单位为 Mbits/s                                          |
| ovn.kubernetes.io/egress_rate          | Int                       | Pod 主网卡流出方向限速，单位为 Mbits/s                                          |
| ovn.kubernetes.io/security_groups      | String 列表，使用逗号分隔    | Pod 主网卡所属的 Security Group                                                 |
| ovn.kubernetes.io/allow_live_migration | `true` or `false`         | Pod 主网卡是否允许 live migration，用于 kubevirt 场景                           |
| ovn.kubernetes.io/default_route        | `true` or `false`         | 是否将主网卡设置为默认路由网卡                                                  |
| ovn.kubernetes.io/provider_network     | String                    | Pod 主网卡所属的 ProviderNetwork                                                |
| ovn.kubernetes.io/mirror               | `true` or `false`         | Pod 主网卡是否做流量镜像                                                        |
| ovn.kubernetes.io/logical_switch       | String                    | Pod 主网卡所属 Subnet                                                           |
| ovn.kubernetes.io/latency              | Int                       | Pod 主网卡注入的延迟，单位为 ms                                                 |
| ovn.kubernetes.io/limit                | Int                       | Pod 主网卡 qdisc 队列可容纳的最大数据包数                                       |
| ovn.kubernetes.io/loss                 | Float                     | Pod 主网卡报文丢包概率                                                          |
| ovn.kubernetes.io/jitter               | Int                       | Pod 主网卡注入抖动延迟，单位为 ms                                             |

## Node Annotation

| Key                                | Value             | Description                                       |
| ---------------------------------- | ----------------- | ------------------------------------------------- |
| ovn.kubernetes.io/allocated        | `true` or `false` | 节点的 `ovn0` 网卡是否已被分配 `join` 子网地址    |
| ovn.kubernetes.io/mac_address      | String            | Node `ovn0` 网卡分配到的 Mac 地址                 |
| ovn.kubernetes.io/ip_address       | String            | Node `ovn0` 网卡所分配到的 IP 地址                |
| ovn.kubernetes.io/cidr             | String            | Node `ovn0` 网卡所属 `join` 子网的 CIDR           |
| ovn.kubernetes.io/gateway          | String            | Node `ovn0` 网卡所属 `join` 子网的 Gateway 地址   |
| ovn.kubernetes.io/chassis          | String            | Node 在 OVN-SouthBoundDB 中的 Chassis ID          |
| ovn.kubernetes.io/port_name        | String            | Node `ovn0` 网卡在 OVN-NorthboundDB 中 LSP 的名称 |
| ovn.kubernetes.io/logical_switch   | String            | Node `ovn0` 网卡所属 Subnet                       |
| ovn.kubernetes.io/tunnel_interface | String            | 隧道封装使用的网卡                                |

## Namespace Annotation

| Key                           | Value                     | Description                          |
| ----------------------------- | ------------------------- | ------------------------------------ |
| ovn.kubernetes.io/cidr        | CIDR 列表，逗号分隔       | 该 Namespace 所绑定子网的 CIDR       |
| ovn.kubernetes.io/exclude_ips | excludeIPs 列表，分号分割 | 该 Namespace 所绑定子网的 excludeIPs |

## Subnet Annotation

| Key                   | Value             | Description                   |
| --------------------- | ----------------- | ----------------------------- |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | 是否对外通过 BGP 发布子网地址 |

## Service Annotation

| Key                             | Value                     | Description                               |
| ------------------------------- | ------------------------- | ----------------------------------------- |
| ovn.kubernetes.io/bgp           | `true` or `false`         | 是否对外通过 BGP 发布 Service 地址        |
| ovn.kubernetes.io/switch_lb_vip | String                    | Service 在 Kube-OVN 中额外分配的 VIP 地址 |
| ovn.kubernetes.io/vpc           | String                    | Service 所属的 VPC                        |

## Networkpolicy Annotation

| Key                          | Value             | Description                 |
| ---------------------------- | ----------------- | --------------------------- |
| ovn.kubernetes.io/enable_log | `true` or `false` | 是否开启 NetworkPolicy 日志 |
