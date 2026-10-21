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
| ovn.kubernetes.io/ip_family | `ipv4` or `ipv6` | 双栈子网中为 Pod 主网卡选择单一 IP 协议族，未设置时保持双栈分配 |
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
| ovn.kubernetes.io/ingress_burst | Int | Pod 主网卡流入方向 burst 上限 |
| ovn.kubernetes.io/egress_burst | Int | Pod 主网卡流出方向 burst 上限 |
| ovn.kubernetes.io/routed_subnet | `true` or `false` | 标识该 Pod 所在子网处于路由子网模式（/32 或 /128 主机路由，同网段强走网关路由） |
| ovn.kubernetes.io/pod_nic_type | `standard`, `dpdk`, `vhost-user` | Pod 主网卡接口类型 |
| ovn.kubernetes.io/dhcp-v4-options | String | Pod 级别的 DHCPv4 选项 UUID，可覆盖所属子网配置 |
| ovn.kubernetes.io/dhcp-v6-options | String | Pod 级别的 DHCPv6 选项 UUID，可覆盖所属子网配置 |
| ovn.kubernetes.io/ip_reserved | `true` or `false` | Pod 分配的 IP 是否已标记为保留地址 |
| ovn.kubernetes.io/port_vips | VIP 列表，逗号分隔 | Pod 主网卡额外绑定的虚拟 IP 列表 |
| ovn.kubernetes.io/vpc_nat_gw | String | VPC NAT Gateway Pod 标识，由控制器写入 |
| ovn.kubernetes.io/vpc_nat_gw_init | `true` or `false` | VPC NAT Gateway Pod 内部初始化是否完成 |
| ovn.kubernetes.io/vpc_nat_gw_init_instance | String | 记录网关初始化命令成功执行的容器实例 ID，当容器重启或替换时重新触发初始化 |
| ovn.kubernetes.io/vpc_nat_gw_container_restarted | `true` or `false` | VPC NAT Gateway 主容器是否重启过，触发规则下发 |
| ovn.kubernetes.io/vpc_nat_gw_activated | `true` or `false` | VPC NAT Gateway 是否已被激活并接管流量 |
| ovn.kubernetes.io/vpc_eips | String | VPC NAT 网关 Pod 上同步的 EIP 列表 MD5 哈希值，由控制器维护 |
| ovn.kubernetes.io/vpc_floating_ips | String | VPC NAT 网关 Pod 上同步的 Floating IP 列表 MD5 哈希值，由控制器维护 |
| ovn.kubernetes.io/vpc_dnat_md5 | String | VPC NAT 网关 Pod 上同步的 DNAT 规则列表 MD5 哈希值，由控制器维护 |
| ovn.kubernetes.io/vpc_snat_md5 | String | VPC NAT 网关 Pod 上同步的 SNAT 规则列表 MD5 哈希值，由控制器维护 |
| ovn.kubernetes.io/vpc_cidrs | String | VPC NAT 网关 Pod 上引流的内部 CIDR 规则配置列表 |
| \<provider\>.kubernetes.io/ip_pool | IP 列表，逗号间隔 | 多网卡场景下指定指定 provider 的 IP 池 |
| \<provider\>.kubernetes.io/ip_family | `ipv4` or `ipv6` | 双栈子网中为指定 provider 的网卡选择单一 IP 协议族 |
| \<provider\>.kubernetes.io/port_vips | VIP 列表，逗号分隔 | 多网卡场景下指定 provider 网卡额外绑定的虚拟 IP 列表 |
| \<provider\>.kubernetes.io/vpc_cidrs | String | 多网卡场景下指定 provider 引流的内部 CIDR 规则配置列表 |
| \<provider\>.kubernetes.io/dhcp-v4-options | String | 多网卡场景下指定 provider 的 DHCPv4 选项 |
| \<provider\>.kubernetes.io/dhcp-v6-options | String | 多网卡场景下指定 provider 的 DHCPv6 选项 |
| \<provider\>.kubernetes.io/port_security | `true` or `false` | 多网卡场景下指定 provider 的端口安全开关 |
| \<provider\>.kubernetes.io/ingress_rate | Int | 多网卡场景下指定 provider 网卡的流入限速（Mbits/s） |
| \<provider\>.kubernetes.io/egress_rate | Int | 多网卡场景下指定 provider 网卡的流出限速（Mbits/s） |
| \<provider\>.kubernetes.io/ingress_burst | Int | 多网卡场景下指定 provider 网卡的流入 burst 上限 |
| \<provider\>.kubernetes.io/egress_burst | Int | 多网卡场景下指定 provider 网卡的流出 burst 上限 |
| \<provider\>.kubernetes.io/routed_subnet | `true` or `false` | 多网卡场景下指定 provider 网卡是否使用路由子网 |
| \<provider\>.kubernetes.io/latency | Int | 多网卡场景下指定 provider 网卡注入的时延（ms） |
| \<provider\>.kubernetes.io/limit | Int | 多网卡场景下指定 provider 网卡 qdisc 队列大小 |
| \<provider\>.kubernetes.io/loss | Float | 多网卡场景下指定 provider 网卡模拟丢包率 |
| \<provider\>.kubernetes.io/jitter | Int | 多网卡场景下指定 provider 网卡注入抖动（ms） |
| \<provider\>.kubernetes.io/vf_representor | String | 多网卡 SR-IOV 场景下指定 VF representor 接口名称 |
| \<provider\>.kubernetes.io/vf | String | 多网卡 SR-IOV 场景下分配的 VF 物理设备接口名称 |

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
| ovn.kubernetes.io/node_networks | String | 节点上为 Pod 提供 attachment networks 的 NetworkAttachmentDefinition 列表 |
| ovn.kubernetes.io/ovs_dp_type | `kernel` or `userspace` | 节点上 OVS 数据面类型，`userspace` 表示运行 OVS-DPDK |
| \<provider\>.provider-network.kubernetes.io/ready | `true` or `false` | 标识该 ProviderNetwork 在当前节点是否已成功初始化就绪 |
| \<provider\>.provider-network.kubernetes.io/interface | String | 当前节点映射到该 ProviderNetwork 的实际物理网卡接口名 |
| \<provider\>.provider-network.kubernetes.io/mtu | Int | 当前节点 ProviderNetwork 物理网卡的 MTU 大小 |
| \<provider\>.provider-network.kubernetes.io/vlan_interfaces | String | 自动在当前节点上为该 ProviderNetwork 创建的 VLAN 子接口列表 |
| \<provider\>.provider-network.kubernetes.io/err_mesg | String | 当前节点初始化该 ProviderNetwork 时的错误或异常信息 |
| \<provider\>.provider-network.kubernetes.io/exclude | String | 指定在当前节点排除接入该 ProviderNetwork 的网卡名称列表 |

## Namespace Annotation

| Key | Value | Description |
| ----------------------------- | ------------------------- | ------------------------------------ |
| ovn.kubernetes.io/cidr | CIDR 列表，逗号分隔 | 该 Namespace 所绑定子网的 CIDR |
| ovn.kubernetes.io/exclude_ips | excludeIPs 列表，分号分隔 | 该 Namespace 所绑定子网的 excludeIPs |

## Subnet Annotation

| Key | Value | Description |
| --------------------- | ----------------- | ----------------------------- |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | 是否对外通过 BGP 发布子网地址 |
| ovn.kubernetes.io/vpc | String | 子网所属的 VPC（控制器维护，便于按 VPC 过滤） |

## Service Annotation

| Key | Value | Description |
| -------------------------------------------- | ------------------------- | ----------------------------------------- |
| ovn.kubernetes.io/service-cidr-hash | String | 记录并校验当前集群 Service CIDR 的 Hash 校验和，防止 Service CIDR 变更导致 OVN 内置路由规则冲突 |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | 是否对外通过 BGP 发布 Service 地址（仅 ClusterIP Service 生效，取值与 Pod/Subnet 一致） |
| ovn.kubernetes.io/switch_lb_vip | String | Service 在 Kube-OVN 中额外分配的 VIP 地址 |
| ovn.kubernetes.io/vpc | String | Service 所属的 VPC |
| ovn.kubernetes.io/service_external_ip_from_subnet | `true` or `false` | Service 外部 IP 是否从子网分配 |
| ovn.kubernetes.io/service_health_check | `true` or `false` | Service 是否启用健康检查 |
| ovn.kubernetes.io/lb_svc_img | String | 负载均衡服务使用的镜像 |
| ovn.kubernetes.io/router_lb_vip | String | 关联的 RouterLBRule VIP 地址 |
| ovn.kubernetes.io/nftable-lb-svc-managed | `true` or `false` | 标识该 Service 是否由基于 nftables 的共享 DNAT/LB 控制器管理 |
| ovn.kubernetes.io/nftable-lb-svc-name | String | 关联管理的 nftable LB Service 名称 |
| ovn.kubernetes.io/nftable-lb-svc-ns | String | 关联管理的 nftable LB Service 命名空间 |

## Networkpolicy Annotation

| Key | Value | Description |
| ---------------------------- | ----------------- | --------------------------- |
| ovn.kubernetes.io/enable_log | `true` or `false` | 是否开启 NetworkPolicy 日志 |
| ovn.kubernetes.io/log_acl_actions | "allow,drop,pass" 其中一个或多个组合 | 打印匹配 Action ACL 的日志 |
| ovn.kubernetes.io/acl_log_meter_rate | Int | NetworkPolicy 日志输出的速率限制，单位为条/秒 |
| ovn.kubernetes.io/network_policy_enforcement | `standard` or `lax` | 单个 NetworkPolicy 的执行模式，覆盖控制器默认 |
| ovn.kubernetes.io/network_policy_for | String | 指定该 NetworkPolicy 作用于的多网卡 provider（格式 `<nadName>.<nadNamespace>.ovn`） |
| ovn.kubernetes.io/policy-for | String | 指定该 NetworkPolicy 作用于的多网络 Pod 的 Provider / NAD 名称（官方标准注解） |

## VIP Annotation

| Key | Value | Description |
| ------------------------------------------- | ----------------- | ----------------------------------------------------- |
| ovn.kubernetes.io/vip-last-attach-subnets | String | 记录 VIP 上一次附加关联的子网名称列表，便于子网解绑或资源释放时的正确清理 |
