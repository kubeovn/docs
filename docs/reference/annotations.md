# Annotation 使用说明

Kube-OVN 使用了大量的 Pod 和 Node Annotation 进行功能设置和信息传递，用户可以通过本文档了解各个 Annotation 的使用，方便问题排查和信息获取。

> 注意：部分 Annotation 可能会随着代码调整而进行变化。

## Pod Annotation

| Key | Value | Description |
| -------------------------------------- | ------------------------- | ------------------------------------------------------------------------------- |
| ovn.kubernetes.io/allocated | `true` or `false` | Pod 主网卡是否已被分配地址 |
| ovn.kubernetes.io/routed | `true` or `false` | Pod 主网卡在 OVN 内的路由是否设置完成 |
| ovn.kubernetes.io/routes | String | Pod 主网卡的路由信息 |
| ovn.kubernetes.io/mac_address | String | Pod 主网卡所分配到的 Mac 地址，创建 Pod 时可通过该 Annotation 设置固定 Mac 地址 |
| ovn.kubernetes.io/ip_address | String | Pod 主网卡所分配到的 IP 地址，创建 Pod 时可通过该 Annotation 设置固定 IP 地址 |
| \<nadName\>.\<nadNamespace\>.kubernetes.io/ip_address.\<interfaceName\> | String | 同一交换机下多网卡时，按网卡指定该接口的固定 IP（interfaceName 与 Multus 中该挂载的 interface 一致）。未设置时仍可使用 ovn.kubernetes.io/ip_address 作为回退 |
| \<nadName\>.\<nadNamespace\>.kubernetes.io/mac_address.\<interfaceName\> | String | 同一交换机下多网卡时，按网卡指定该接口的固定 MAC（interfaceName 与 Multus 中该挂载的 interface 一致） |
| ovn.kubernetes.io/cidr | String | Pod 主网卡所属子网的 CIDR |
| ovn.kubernetes.io/gateway | String | Pod 主网卡所属子网的 Gateway 地址 |
| ovn.kubernetes.io/ip_pool | IP 列表，逗号间隔 | Pod 主网卡地址将从列表中选择，适用于 Workload 固定 IP 场景 |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | 是否对外通过 BGP 发布 Pod 地址 |
| ovn.kubernetes.io/snat | String | Pod 访问集群外使用的 SNAT 地址 |
| ovn.kubernetes.io/eip | String | Pod 访问集群外部和被集群外部访问所使用的 EIP 地址 |
| ovn.kubernetes.io/vip | String | Pod 主网卡使用的预留 VIP，可通过该 Annotation 使用预先创建的 VIP 资源 |
| ovn.kubernetes.io/aaps | String | Pod 主网卡的 AAPs (Additional Allowed Addresses Pairs) 配置 |
| ovn.kubernetes.io/virtualmachine | String | Pod 主网卡所属的 VirtualMachineInstance |
| ovn.kubernetes.io/activation_strategy | String | Pod 主网卡的激活策略 |
| ovn.kubernetes.io/logical_router | String | Pod 主网卡所属的 VPC |
| ovn.kubernetes.io/layer2_forward | `true` or `false` | Pod 主网卡在 OVN LSP 中是否增加 `unknown` 地址 |
| ovn.kubernetes.io/port_security | `true` or `false` | Pod 主网卡对应端口是否开启 Port Security |
| ovn.kubernetes.io/logical_switch | String | Pod 主网卡所属的子网 |
| ovn.kubernetes.io/vlan_id | Int | Pod 主网卡所属子网的 Vlan ID |
| ovn.kubernetes.io/ingress_rate | Int | Pod 主网卡流入方向限速，单位为 Mbits/s |
| ovn.kubernetes.io/egress_rate | Int | Pod 主网卡流出方向限速，单位为 Mbits/s |
| ovn.kubernetes.io/security_groups | String 列表，使用逗号分隔 | Pod 主网卡所属的 Security Group |
| ovn.kubernetes.io/default_route | `true` or `false` | 是否将主网卡设置为默认路由网卡 |
| ovn.kubernetes.io/provider_network | String | Pod 主网卡所属的 ProviderNetwork |
| ovn.kubernetes.io/mirror | `true` or `false` | Pod 主网卡是否做流量镜像 |
| ovn.kubernetes.io/north_gateway | String | Pod 主网卡的北向网关配置 |
| ovn.kubernetes.io/latency | Int | Pod 主网卡注入的延迟，单位为 ms |
| ovn.kubernetes.io/limit | Int | Pod 主网卡 qdisc 队列可容纳的最大数据包数 |
| ovn.kubernetes.io/loss | Float | Pod 主网卡报文丢包概率 |
| ovn.kubernetes.io/jitter | Int | Pod 主网卡注入抖动延迟，单位为 ms |
| ovn.kubernetes.io/generate-hash | `true` or `false` | 是否为 Pod 生成哈希值 |
| ovn.kubernetes.io/attachmentprovider | String | Pod 的附件提供者 |

## Node Annotation

| Key | Value | Description |
| ---------------------------------- | ----------------- | ------------------------------------------------- |
| ovn.kubernetes.io/allocated | `true` or `false` | 节点的 `ovn0` 网卡是否已被分配 `join` 子网地址 |
| ovn.kubernetes.io/mac_address | String | Node `ovn0` 网卡分配到的 Mac 地址 |
| ovn.kubernetes.io/ip_address | String | Node `ovn0` 网卡所分配到的 IP 地址 |
| ovn.kubernetes.io/cidr | String | Node `ovn0` 网卡所属 `join` 子网的 CIDR |
| ovn.kubernetes.io/gateway | String | Node `ovn0` 网卡所属 `join` 子网的 Gateway 地址 |
| ovn.kubernetes.io/chassis | String | Node 在 OVN-SouthBoundDB 中的 Chassis ID |
| ovn.kubernetes.io/port_name | String | Node `ovn0` 网卡在 OVN-NorthboundDB 中 LSP 的名称 |
| ovn.kubernetes.io/logical_switch | String | Node `ovn0` 网卡所属子网 |
| ovn.kubernetes.io/tunnel_interface | String | 隧道封装使用的网卡 |

## Namespace Annotation

| Key | Value | Description |
| ----------------------------- | ------------------------- | ------------------------------------ |
| ovn.kubernetes.io/cidr | CIDR 列表，逗号分隔 | 该 Namespace 所绑定子网的 CIDR |
| ovn.kubernetes.io/exclude_ips | excludeIPs 列表，分号分隔 | 该 Namespace 所绑定子网的 excludeIPs |

## Subnet Annotation

| Key | Value | Description |
| --------------------- | ----------------- | ----------------------------- |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | 是否对外通过 BGP 发布子网地址 |

## Service Annotation

| Key | Value | Description |
| -------------------------------------------- | ------------------------- | ----------------------------------------- |
| ovn.kubernetes.io/bgp | `true` or `false` | 是否对外通过 BGP 发布 Service 地址 |
| ovn.kubernetes.io/switch_lb_vip | String | Service 在 Kube-OVN 中额外分配的 VIP 地址 |
| ovn.kubernetes.io/vpc | String | Service 所属的 VPC |
| ovn.kubernetes.io/service_external_ip_from_subnet | `true` or `false` | Service 外部 IP 是否从子网分配 |
| ovn.kubernetes.io/service_health_check | `true` or `false` | Service 是否启用健康检查 |
| ovn.kubernetes.io/lb_svc_img | String | 负载均衡服务使用的镜像 |

## Networkpolicy Annotation

| Key | Value | Description |
| ---------------------------- | ----------------- | --------------------------- |
| ovn.kubernetes.io/enable_log | `true` or `false` | 是否开启 NetworkPolicy 日志 |
| ovn.kubernetes.io/log_acl_actions | "allow,drop,pass" 其中一个或多个组合 | 打印匹配 Action ACL 的日志 |
| ovn.kubernetes.io/acl_log_meter_rate | Int | NetworkPolicy 日志输出的速率限制，单位为条/秒 |
