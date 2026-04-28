# Kube-OVN 接口规范

基于 Kube-OVN 最新版本，整理了 Kube-OVN 支持的 CRD 资源列表，列出 CRD 定义各字段的取值类型和含义，以供参考。

## 通用的 Condition 定义

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| type | String | 状态类型 |
| status | String | 状态值，取值为 `True`，`False` 或 `Unknown` |
| reason | String | 状态变化的原因 |
| message | String | 状态变化的具体信息 |
| observedGeneration | Int64 | 观察到的资源版本 |
| lastUpdateTime | Time | 上次状态更新时间 |
| lastTransitionTime | Time | 上次状态类型发生变化的时间 |

在各 CRD 的定义中，Status 中的 Condition 字段，都遵循上述格式，因此提前进行说明。

## 核心网络资源

### Subnet 定义

#### Subnet

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Subnet` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | SubnetSpec | Subnet 具体配置信息字段 |
| status | SubnetStatus | Subnet 状态信息字段 |

##### SubnetSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| default | Bool | 该子网是否为默认子网 |
| vpc | String | 子网所属 VPC，默认为 ovn-cluster |
| protocol | String | IP 协议，取值可以为 `IPv4`，`IPv6` 或 `Dual` |
| namespaces | []String | 该子网所绑定的 namespace 列表 |
| cidrBlock | String | 子网的网段范围，如 10.16.0.0/16 |
| gateway | String | 子网网关地址，默认为该子网 CIDRBlock 下的第一个可用地址 |
| excludeIps | []String | 该子网下不会被自动分配的地址范围 |
| provider | String | 默认为 OVN。多网卡情况下可以配置取值为 NetworkAttachmentDefinition 的 <name>.<namespace>，Kube-OVN 将会使用这些信息找到对应的 Subnet 资源 |
| gatewayType | String | Overlay 模式下的网关类型，取值可以为 `distributed` 或 `centralized` |
| gatewayNode | String | 当网关模式为 centralized 时的网关节点，可以为逗号分隔的多个节点 |
| natOutgoing | Bool | 出网流量是否进行 NAT。该参数和 `externalEgressGateway` 参数不能同时设置。 |
| externalEgressGateway | String | 外部网关地址。需要和子网网关节点在同一个二层可达域，该参数和 `natOutgoing` 参数不能同时设置 |
| policyRoutingPriority | Uint32 | 策略路由优先级。添加策略路由使用参数，控制流量经子网网关之后，转发到外部网关地址 |
| policyRoutingTableID | Uint32 | 使用的本地策略路由表的 TableID，每个子网均需不同以避免冲突 |
| mtu | Uint32 | 子网的 MTU 大小 |
| private | Bool | 标识该子网是否为私有子网，私有子网默认拒绝子网外的地址访问 |
| allowSubnets | []String | 子网为私有子网的情况下，允许访问该子网地址的集合 |
| vlan | String | 子网绑定的 Vlan 名称 |
| vips | []String | 子网下 virtual 类型 lsp 的 virtual-ip 参数信息 |
| logicalGateway | Bool | 是否启用逻辑网关 |
| disableGatewayCheck | Bool | 创建 Pod 时是否跳过网关联通性检查 |
| disableInterConnection | Bool | 控制是否开启子网跨集群互联 |
| enableDHCP | Bool | 控制是否配置子网下 lsp 的 dhcp 配置选项 |
| dhcpV4Options | String | 子网下 lsp dhcpv4_options 关联的 DHCP_Options 记录 |
| dhcpV6Options | String | 子网下 lsp dhcpv6_options 关联的 DHCP_Options 记录 |
| enableIPv6RA | Bool | 控制子网连接路由器的 lrp 端口，是否配置 ipv6_ra_configs 参数 |
| ipv6RAConfigs | String | 子网连接路由器的 lrp 端口，ipv6_ra_configs 参数配置信息 |
| acls | []Acl | 子网对应 logical-switch 关联的 acls 记录 |
| allowEWTraffic | Bool | 是否允许东西向流量 |
| natOutgoingPolicyRules | []NatOutgoingPolicyRule | NAT 出网策略规则 |
| u2oInterconnectionIP | String | Underlay/Overlay 互联使用的 IP 地址 |
| u2oInterconnection | Bool | 是否开启 Overlay/Underlay 的互联模式 |
| enableLb | *Bool | 控制子网对应的 logical-switch 是否关联 load-balancer 记录 |
| enableEcmp | Bool | 集中式网关，是否开启 ECMP 路由 |
| enableMulticastSnoop | Bool | 是否启用组播侦听 |
| enableExternalLBAddress | Bool | 是否启用外部负载均衡器地址 |
| routeTable | String | 路由表名称 |
| namespaceSelectors | []LabelSelector | 命名空间选择器 |

###### Acl

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| direction | String | Acl 限制方向，取值为 `from-lport` 或者 `to-lport` |
| priority | Int | Acl 优先级，取值范围 0 到 32767 |
| match | String | Acl 规则匹配表达式 |
| action | String | Acl 规则动作，取值为 `allow-related`、`allow-stateless`、`allow`、`drop`、`reject` 其中一个 |

###### NatOutgoingPolicyRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| match | NatOutGoingPolicyMatch | 匹配条件 |
| action | String | 动作 |

###### NatOutGoingPolicyMatch

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| srcIPs | String | 源 IP 地址范围 |
| dstIPs | String | 目标 IP 地址范围 |

##### SubnetStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []SubnetCondition | 子网状态变化信息，具体字段参考文档开头 Condition 定义 |
| v4availableIPs | BigInt | 子网现在可用的 IPv4 IP 地址数量（大整数，支持 IPv6 大网段下超过 float64 精度的计数） |
| v4availableIPrange | String | 子网现在可用的 IPv4 地址范围 |
| v4usingIPs | BigInt | 子网现在已用的 IPv4 IP 地址数量 |
| v4usingIPrange | String | 子网现在已用的 IPv4 地址范围 |
| v6availableIPs | BigInt | 子网现在可用的 IPv6 IP 地址数量 |
| v6availableIPrange | String | 子网现在可用的 IPv6 地址范围 |
| v6usingIPs | BigInt | 子网现在已用的 IPv6 IP 地址数量 |
| v6usingIPrange | String | 子网现在已用的 IPv6 地址范围 |
| activateGateway | String | 集中式子网，主备模式下当前正在工作的网关节点 |
| dhcpV4OptionsUUID | String | 子网下 lsp dhcpv4_options 关联的 DHCP_Options 记录标识 |
| dhcpV6OptionsUUID | String | 子网下 lsp dhcpv6_options 关联的 DHCP_Options 记录标识 |
| u2oInterconnectionIP | String | 开启 Overlay/Underlay 互联模式后，所占用的用于互联的 IP 地址 |
| u2oInterconnectionMAC | String | 开启 Overlay/Underlay 互联模式后，所占用的用于互联的 MAC 地址 |
| u2oInterconnectionVPC | String | 开启 Overlay/Underlay 互联模式后，关联的 VPC |
| natOutgoingPolicyRules | []NatOutgoingPolicyRuleStatus | NAT 出网策略规则状态 |
| mcastQuerierIP | String | 组播查询器的 IP 地址 |
| mcastQuerierMAC | String | 组播查询器的 MAC 地址 |

### IP 定义

#### IP

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IP` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IPSpec | IP 具体配置信息字段 |

##### IPSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| podName | String | 绑定 Pod 名称 |
| namespace | String | 绑定 Pod 所在 Namespace 名称 |
| subnet | String | IP 所属 Subnet |
| attachSubnets | []String | 该主 IP 下其他附属子网名称（字段废弃不再使用） |
| nodeName | String | 绑定 Pod 所在的节点名称 |
| ipAddress | String | IP 地址，双栈情况下为 `v4IP，v6IP` 格式 |
| v4IpAddress | String | IPv4 IP 地址 |
| v6IpAddress | String | IPv6 IP 地址 |
| attachIps | []String | 该主 IP 下其他附属 IP 地址（字段废弃不再使用） |
| macAddress | String | 绑定 Pod 的 MAC 地址 |
| attachMacs | []String | 该主 IP 下其他附属 MAC 地址（字段废弃不再使用） |
| containerID | String | 绑定 Pod 对应的 Container ID |
| podType | String | 特殊工作负载 Pod，可为 `StatefulSet`，`VirtualMachine` 或空 |

### Vpc 定义

#### Vpc

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Vpc` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcSpec | Vpc 具体配置信息字段 |
| status | VpcStatus | Vpc 状态信息字段 |

##### VpcSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| defaultSubnet | String | 默认子网名称 |
| namespaces | []String | Vpc 绑定的命名空间列表 |
| staticRoutes | []StaticRoute | 静态路由配置 |
| policyRoutes | []PolicyRoute | 策略路由配置 |
| vpcPeerings | []VpcPeering | VPC 对等连接配置 |
| enableExternal | Bool | 是否启用外部连接 |
| extraExternalSubnets | []String | 额外的外部子网 |
| enableBfd | Bool | 是否启用 BFD (双向转发检测) |
| bfdPort | BFDPort | BFD 端口配置 |

###### StaticRoute

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| policy | String | 路由策略 |
| cidr | String | 目标网段 |
| nextHopIP | String | 下一跳 IP 地址 |
| ecmpMode | String | ECMP 模式 |
| bfdId | String | BFD ID |
| routeTable | String | 路由表名称 |

###### PolicyRoute

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| priority | Int | 策略路由优先级 |
| match | String | 匹配条件 |
| action | String | 动作，可为 `allow`、`drop`、`reroute` |
| nextHopIP | String | 重路由的下一跳 IP 地址（仅当 action 为 reroute 时需要） |

###### VpcPeering

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| remoteVpc | String | 远程 VPC 名称 |
| localConnectIP | String | 本地连接 IP 地址 |

###### BFDPort

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| enabled | Bool | 是否启用 BFD |
| ip | String | BFD 端口的 IP 地址 |
| nodeSelector | LabelSelector | 用于选择承载 BFD LRP 的节点的选择器 |

##### VpcStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []VpcCondition | Vpc 状态变化信息，具体字段参考文档开头 Condition 定义 |
| standby | Bool | 是否为备用 VPC |
| default | Bool | 是否为默认 VPC |
| defaultLogicalSwitch | String | 默认逻辑交换机名称 |
| router | String | 关联的路由器名称 |
| tcpLoadBalancer | String | TCP 负载均衡器名称 |
| udpLoadBalancer | String | UDP 负载均衡器名称 |
| sctpLoadBalancer | String | SCTP 负载均衡器名称 |
| tcpSessionLoadBalancer | String | TCP 会话负载均衡器名称 |
| udpSessionLoadBalancer | String | UDP 会话负载均衡器名称 |
| sctpSessionLoadBalancer | String | SCTP 会话负载均衡器名称 |
| subnets | []String | VPC 下的子网列表 |
| vpcPeerings | []String | VPC 对等连接列表 |
| enableExternal | Bool | 是否启用外部连接 |
| extraExternalSubnets | []String | 额外的外部子网 |
| enableBfd | Bool | 是否启用 BFD |

## Underlay 网络配置

### Vlan

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Vlan` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VlanSpec | Vlan 具体配置信息字段 |
| status | VlanStatus | Vlan 状态信息字段 |

#### VlanSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| id | Int | Vlan tag 号，取值范围为 0~4096 |
| provider | String | Vlan 绑定的 ProviderNetwork 名称 |

#### VlanStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| subnets | []String | Vlan 绑定的子网列表 |
| conflict | Bool | 是否存在冲突 |
| conditions | []VlanCondition | Vlan 状态变化信息，具体字段参考文档开头 Condition 定义 |

### ProviderNetwork

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `ProviderNetwork` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | ProviderNetworkSpec | ProviderNetwork 具体配置信息字段 |
| status | ProviderNetworkStatus | ProviderNetwork 状态信息字段 |

#### ProviderNetworkSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| defaultInterface | String | 该桥接网络默认使用的网卡接口名称 |
| customInterfaces | []CustomInterface | 该桥接网络特殊使用的网卡配置 |
| nodeSelector | LabelSelector | 基于节点标签选择需要创建 OVS 网桥的节点，支持 matchLabels 和 matchExpressions（一旦使用 nodeSelector，excludeNodes 将不再生效） |
| excludeNodes | []String | 该桥接网络不会绑定的节点名称 |
| exchangeLinkName | Bool | 是否交换桥接网卡和对应 OVS 网桥名称 |

##### CustomInterface

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| interface | String | Underlay 使用网卡接口名称 |
| nodes | []String | 使用自定义网卡接口的节点列表 |

#### ProviderNetworkStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | 当前桥接网络是否进入就绪状态 |
| readyNodes | []String | 桥接网络进入就绪状态的节点名称 |
| notReadyNodes | []String | 桥接网络未进入就绪状态的节点名称 |
| vlans | []String | 桥接网络绑定的 Vlan 名称 |
| conditions | []ProviderNetworkCondition | ProviderNetwork 状态变化信息，具体字段参考文档开头 Condition 定义 |

## 安全配置

### SecurityGroup

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `SecurityGroup` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | SecurityGroupSpec | SecurityGroup 具体配置信息字段 |
| status | SecurityGroupStatus | SecurityGroup 状态信息字段 |

#### SecurityGroupSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ingressRules | []SecurityGroupRule | 入站安全组规则 |
| egressRules | []SecurityGroupRule | 出站安全组规则 |
| allowSameGroupTraffic | Bool | 是否允许同安全组内的流量 |

##### SecurityGroupRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ipVersion | String | IP 版本，取值为 `ipv4` 或 `ipv6` |
| protocol | SgProtocol | 协议类型，取值为 `all`、`icmp`、`tcp` 或 `udp` |
| priority | Int | 规则优先级，取值范围为 1-200，数值越小，优先级越高 |
| remoteType | SgRemoteType | 远程类型，取值为 `address` 或 `securityGroup` |
| remoteAddress | String | 远程地址 |
| remoteSecurityGroup | String | 远程安全组名称 |
| portRangeMin | Int | 端口范围起始值，最小取值为 1 |
| portRangeMax | Int | 端口范围最大值，最大取值为 65535 |
| policy | SgPolicy | 策略动作，取值为 `allow` 或 `drop` |

#### SecurityGroupStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| portGroup | String | 关联的端口组 |
| allowSameGroupTraffic | Bool | 是否允许同安全组内的流量 |
| ingressMd5 | String | 入站规则的 MD5 值 |
| egressMd5 | String | 出站规则的 MD5 值 |
| ingressLastSyncSuccess | Bool | 入站规则最后一次同步是否成功 |
| egressLastSyncSuccess | Bool | 出站规则最后一次同步是否成功 |

## 负载均衡和虚拟 IP

### Vip

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Vip` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VipSpec | Vip 具体配置信息字段 |
| status | VipStatus | Vip 状态信息字段 |

#### VipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| namespace | String | VIP 所属的命名空间 |
| subnet | String | VIP 所属的子网 |
| type | String | VIP 类型 |
| v4ip | String | IPv4 地址 |
| v6ip | String | IPv6 地址 |
| macAddress | String | MAC 地址 |
| selector | []String | 选择器 |
| attachSubnets | []String | 附加的子网列表 |

#### VipStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []VipCondition | VIP 状态变化信息，具体字段参考文档开头 Condition 定义 |
| type | String | VIP 类型 |
| v4ip | String | IPv4 地址 |
| v6ip | String | IPv6 地址 |
| mac | String | MAC 地址 |

### SwitchLBRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `SwitchLBRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | SwitchLBRuleSpec | SwitchLBRule 具体配置信息字段 |
| status | SwitchLBRuleStatus | SwitchLBRule 状态信息字段 |

#### SwitchLBRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vip | String | 虚拟 IP 地址 |
| namespace | String | 所属命名空间 |
| selector | []String | 后端选择器 |
| endpoints | []String | 后端端点列表 |
| sessionAffinity | String | 会话亲和性 |
| ports | []SwitchLBRulePort | 端口配置 |

##### SwitchLBRulePort

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| name | String | 端口名称 |
| port | Int32 | 端口号 |
| targetPort | Int32 | 目标端口号 |
| protocol | String | 协议类型 |

#### SwitchLBRuleStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []SwitchLBRuleCondition | SwitchLBRule 状态变化信息，具体字段参考文档开头 Condition 定义 |
| ports | String | SwitchLBRule 端口信息 |
| service | String | SwitchLBRule 提供服务的 service 名称 |

## QoS 和 IP 池管理

### QoSPolicy

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `QoSPolicy` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | QoSPolicySpec | QoSPolicy 具体配置信息字段 |

#### QoSPolicySpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| bandwidthLimitRules | QoSPolicyBandwidthLimitRules | 带宽限制规则 |
| shared | Bool | 是否为共享策略 |
| bindingType | QoSPolicyBindingType | 绑定类型 |

### IPPool

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IPPool` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IPPoolSpec | IPPool 具体配置信息字段 |
| status | IPPoolStatus | IPPool 状态信息字段 |

#### IPPoolSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| subnet | String | 所属子网 |
| namespaces | []String | 绑定的命名空间列表 |
| ips | []String | IP 地址列表 |

#### IPPoolStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| v4AvailableIPs | BigInt | IPv4 可用 IP 地址数量 |
| v4AvailableIPRange | String | IPv4 可用 IP 地址范围 |
| v4UsingIPs | BigInt | IPv4 已使用 IP 地址数量 |
| v4UsingIPRange | String | IPv4 已使用 IP 地址范围 |
| v6AvailableIPs | BigInt | IPv6 可用 IP 地址数量 |
| v6AvailableIPRange | String | IPv6 可用 IP 地址范围 |
| v6UsingIPs | BigInt | IPv6 已使用 IP 地址数量 |
| v6UsingIPRange | String | IPv6 已使用 IP 地址范围 |
| conditions | []IPPoolCondition | IP 池状态变化信息，具体字段参考文档开头 Condition 定义 |

## NAT 和弹性 IP 管理

### IptablesEIP

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesEIP` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesEIPSpec | IptablesEIP 具体配置信息字段 |
| status | IptablesEIPStatus | IptablesEIP 状态信息字段 |

#### IptablesEIPSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| v4ip | String | IPv4 地址 |
| v6ip | String | IPv6 地址 |
| macAddress | String | MAC 地址 |
| natGwDp | String | NAT 网关数据路径 |
| qosPolicy | String | QoS 策略 |
| externalSubnet | String | 外部子网 |

#### IptablesEIPStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | IptablesEIP 是否配置完成 |
| ip | String | IptablesEIP 使用的 IP 地址，目前只支持了 IPv4 地址 |
| redo | String | IptablesEIP CRD 创建或者更新时间 |
| nat | String | IptablesEIP 的使用类型，取值为 `fip`、`snat` 或者 `dnat` |
| qosPolicy | String | QoS 策略名称 |
| conditions | []IptablesEIPCondition | IptablesEIP 状态变化信息，具体字段参考文档开头 Condition 定义 |

### OvnEip

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnEip` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnEipSpec | OvnEip 具体配置信息字段 |
| status | OvnEipStatus | OvnEip 状态信息字段 |

#### OvnEipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| externalSubnet | String | 外部子网 |
| v4Ip | String | IPv4 地址 |
| v6Ip | String | IPv6 地址 |
| macAddress | String | MAC 地址 |
| type | String | 类型，可以为 lrp、lsp 或 nat |

### IptablesFIPRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesFIPRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesFIPRuleSpec | IptablesFIPRule 具体配置信息字段 |

#### IptablesFIPRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| eip | String | 弹性 IP 地址 |
| internalIP | String | 内部 IP 地址 |

### OvnFip

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnFip` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnFipSpec | OvnFip 具体配置信息字段 |
| status | OvnFipStatus | OvnFip 状态信息字段 |

#### OvnFipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ovnEip | String | 关联的 OVN EIP |
| ipType | String | IP 类型，可以为 vip 或 ip |
| ipName | String | IP 名称 |
| vpc | String | 所属 VPC |
| v4Ip | String | IPv4 地址 |
| v6Ip | String | IPv6 地址 |
| type | String | 类型，可以为 distributed 或 centralized |

### IptablesDnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesDnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesDnatRuleSpec | IptablesDnatRule 具体配置信息字段 |

#### IptablesDnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| eip | String | 弹性 IP 地址 |
| externalPort | String | 外部端口 |
| protocol | String | 协议类型 |
| internalIP | String | 内部 IP 地址 |
| internalPort | String | 内部端口 |

### OvnDnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnDnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnDnatRuleSpec | OvnDnatRule 具体配置信息字段 |
| status | OvnDnatRuleStatus | OvnDnatRule 状态信息字段 |

#### OvnDnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ovnEip | String | 关联的 OVN EIP |
| ipType | String | IP 类型，可以为 vip 或 ip |
| ipName | String | IP 名称 |
| internalPort | String | 内部端口 |
| externalPort | String | 外部端口 |
| protocol | String | 协议类型 |
| vpc | String | 所属 VPC |
| v4Ip | String | IPv4 地址 |
| v6Ip | String | IPv6 地址 |

#### OvnDnatRuleStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vpc | String | 所属 VPC |
| v4Eip | String | IPv4 EIP 地址 |
| v6Eip | String | IPv6 EIP 地址 |
| externalPort | String | 外部端口 |
| v4Ip | String | IPv4 地址 |
| v6Ip | String | IPv6 地址 |
| internalPort | String | 内部端口 |
| protocol | String | 协议类型 |
| ipName | String | IP 名称 |
| ready | Bool | DNAT 规则是否配置完成 |
| conditions | []OvnDnatRuleCondition | OVN DNAT 规则状态变化信息，具体字段参考文档开头 Condition 定义 |

### IptablesSnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesSnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesSnatRuleSpec | IptablesSnatRule 具体配置信息字段 |

#### IptablesSnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| eip | String | 弹性 IP 地址 |
| internalCIDR | String | 内部 CIDR 网段 |

### OvnSnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnSnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnSnatRuleSpec | OvnSnatRule 具体配置信息字段 |
| status | OvnSnatRuleStatus | OvnSnatRule 状态信息字段 |

#### OvnSnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ovnEip | String | 关联的 OVN EIP |
| vpcSubnet | String | VPC 子网 |
| ipName | String | IP 名称 |
| vpc | String | 所属 VPC |
| v4IpCidr | String | IPv4 CIDR 网段 |
| v6IpCidr | String | IPv6 CIDR 网段 |

## VPC 高级功能

### VpcNatGateway

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `VpcNatGateway` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcNatGatewaySpec | VpcNatGateway 具体配置信息字段 |
| status | VpcNatGatewayStatus | VpcNatGateway 状态信息字段 |

#### VpcNatGatewaySpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vpc | String | VPC 网关 Pod 所在的 VPC 名称 |
| subnet | String | VPC 网关 Pod 所属的子网名称 |
| externalSubnets | []String | 外部子网列表 |
| lanIp | String | VPC 网关 Pod 指定分配的 IP 地址 |
| selector | []String | 标准 Kubernetes Selector 匹配信息 |
| tolerations | []Toleration | 标准 Kubernetes 容忍信息 |
| affinity | Affinity | 标准 Kubernetes 亲和性配置 |
| qosPolicy | String | QoS 策略名称 |
| bgpSpeaker | VpcBgpSpeaker | BGP speaker 配置 |
| routes | []Route | 路由配置列表 |

##### VpcBgpSpeaker

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| enabled | Bool | 是否启用 BGP speaker |
| asn | Uint32 | 本地自治系统号 |
| remoteAsn | Uint32 | 远程自治系统号 |
| neighbors | []String | BGP 邻居列表 |
| holdTime | Duration | BGP 保持时间 |
| routerId | String | BGP 路由器 ID |
| password | String | BGP 认证密码 |
| enableGracefulRestart | Bool | 是否启用优雅重启 |
| extraArgs | []String | 额外参数列表 |

##### Route

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| cidr | String | 路由目标 CIDR |
| nextHopIP | String | 下一跳 IP 地址 |

#### VpcNatGatewayStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| qosPolicy | String | QoS 策略名称 |
| externalSubnets | []String | 外部子网列表 |
| selector | []String | 标准 Kubernetes Selector 匹配信息 |
| tolerations | []Toleration | 标准 Kubernetes 容忍信息 |
| affinity | Affinity | 标准 Kubernetes 亲和性配置 |

### VpcEgressGateway

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `VpcEgressGateway` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcEgressGatewaySpec | VpcEgressGateway 具体配置信息字段 |
| status | VpcEgressGatewayStatus | VpcEgressGateway 状态信息字段 |

#### VpcEgressGatewaySpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vpc | String | 可选，所属 VPC，未指定时使用默认 VPC |
| bgpConf | String | 可选，引用集群级 `BgpConf` 资源名称，用于公布出口路由 |
| evpnConf | String | 可选，引用集群级 `EvpnConf` 资源名称，用于 EVPN 场景 |
| replicas | Int32 | 网关副本数量，默认 1 |
| prefix | String | 可选，工作负载名称前缀，最终名称为 `<prefix><veg-name>` |
| image | String | 可选，工作负载使用的镜像，未指定时使用 kube-ovn-controller 默认镜像 |
| internalSubnet | String | 可选，内部子网，未指定时使用 VPC 默认子网 |
| externalSubnet | String | 必填，外部子网名称 |
| internalIPs | []String | 可选，内部 IP 列表（数量不少于副本数；双栈时元素为 `v4,v6` 形式） |
| externalIPs | []String | 可选，外部 IP 列表（数量不少于副本数；双栈时元素为 `v4,v6` 形式） |
| selectors | []VpcEgressGatewaySelector | 命名空间/Pod 选择器，用于选择由该网关承载的流量来源 |
| trafficPolicy | String | 可选，流量策略，`Cluster`（默认）或 `Local`，仅默认 VPC 生效 |
| bfd | VpcEgressGatewayBFDConfig | BFD 配置 |
| policies | []VpcEgressGatewayPolicy | 出向策略列表，至少一项 |
| nodeSelector | []VpcEgressGatewayNodeSelector | 可选，工作负载节点选择器 |
| tolerations | []Toleration | 可选，标准 Kubernetes 容忍配置 |
| resources | ResourceRequirements | 可选，容器资源限制；未指定时控制器使用默认值 |
| bandwidth | BandwidthLimit | 可选，每个网关实例的入向/出向带宽限速（Mbps） |

##### VpcEgressGatewaySelector

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| namespaceSelector | LabelSelector | 命名空间标签选择器 |
| podSelector | LabelSelector | Pod 标签选择器 |

##### VpcEgressGatewayBFDConfig

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| enabled | Boolean | 是否启用 BFD（同时要求 VPC 的 `.spec.bfd.enabled=true`），默认 false |
| minRX | Int32 | BFD 最小接收间隔（ms），默认 1000 |
| minTX | Int32 | BFD 最小发送间隔（ms），默认 1000 |
| multiplier | Int32 | BFD 检测倍数，默认 3 |

##### VpcEgressGatewayPolicy

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| snat | Boolean | 是否对匹配出向流量做 SNAT/MASQUERADE，默认 false |
| ipBlocks | []String | 匹配的 CIDR 列表 |
| subnets | []String | 匹配的子网名称列表 |

##### VpcEgressGatewayNodeSelector

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| matchLabels | map[String]String | 标签匹配映射 |
| matchExpressions | []NodeSelectorRequirement | 标签匹配表达式 |
| matchFields | []NodeSelectorRequirement | 字段匹配表达式 |

##### BandwidthLimit

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ingress | Int64 | 入向带宽限速，单位 Mbps |
| egress | Int64 | 出向带宽限速，单位 Mbps |

#### VpcEgressGatewayStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| replicas | Int32 | 当前副本数（用于 scale 子资源） |
| labelSelector | String | 网关工作负载选择器（用于 scale 子资源） |
| ready | Boolean | 网关是否就绪 |
| phase | String | 当前阶段，可为 `Pending`、`Processing` 或 `Completed` |
| internalIPs | []String | 实际占用的内部 IP 列表 |
| externalIPs | []String | 实际占用的外部 IP 列表 |
| conditions | []Condition | 当前状态变化的最新观察 |
| workload | VpcEgressWorkload | 关联工作负载信息 |

##### VpcEgressWorkload

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 工作负载 API 版本 |
| kind | String | 工作负载类型，例如 `Deployment` |
| name | String | 工作负载名称 |
| nodes | []String | 当前承载工作负载的节点列表 |

### BgpConf

集群级（cluster-scoped）资源，被 `VpcEgressGateway.spec.bgpConf` 引用，用于宣告出口前缀。

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `BgpConf` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | BgpConfSpec | BgpConf 具体配置信息字段 |

#### BgpConfSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| localASN | UInt32 | 本端 BGP AS Number |
| peerASN | UInt32 | 对端 BGP AS Number |
| routerId | String | 可选，BGP Router ID |
| neighbours | []String | BGP 邻居 IP 列表 |
| password | String | 可选，TCP MD5 鉴权口令 |
| holdTime | Duration | 可选，BGP Hold time |
| keepaliveTime | Duration | 可选，BGP Keepalive 间隔 |
| connectTime | Duration | 可选，BGP Connect 间隔 |
| ebgpMultiHop | Boolean | 可选，是否启用 eBGP MultiHop |
| gracefulRestart | Boolean | 可选，是否启用 BGP Graceful Restart |

### EvpnConf

集群级（cluster-scoped）资源，被 `VpcEgressGateway.spec.evpnConf` 引用，用于在 EVPN 场景下声明 VNI 与 Route Target。

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `EvpnConf` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | EvpnConfSpec | EvpnConf 具体配置信息字段 |

#### EvpnConfSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vni | UInt32 | EVPN VNI |
| routeTargets | []String | Route Target 列表 |

### DNSNameResolver

集群级（cluster-scoped）资源，由 `enable-dns-name-resolver` 启用的 ANP/CNP 域名匹配场景使用，存储 DNS 解析结果。

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `DNSNameResolver` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | DNSNameResolverSpec | DNSNameResolver 具体配置信息字段 |
| status | DNSNameResolverStatus | DNSNameResolver 状态信息字段 |

#### DNSNameResolverSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| name | String | 需要解析的 DNS 名称（普通名称或以 `*.` 开头的通配名称），创建后不可变 |

#### DNSNameResolverStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| resolvedNames | []DNSNameResolverResolvedName | 实际解析得到的 DNS 名称及其 IP 详情 |

##### DNSNameResolverResolvedName

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| dnsName | String | 解析得到的实际 DNS 名称 |
| resolvedAddresses | []DNSNameResolverResolvedAddress | 解析到的 IP、TTL 与最近解析时间 |
| conditions | []Condition | 状态条件，已知类型 `Degraded` 表示最近一次解析失败 |
| resolutionFailures | Int32 | 连续解析失败次数，成功后清零，超过 5 次且 TTL 全部过期后会被移除 |

##### DNSNameResolverResolvedAddress

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ip | String | 解析到的 IP 地址 |
| ttlSeconds | Int32 | TTL 秒数；`lastLookupTime + ttlSeconds` 之后失效 |
| lastLookupTime | Time | 最近一次成功解析的时间戳 |

### VpcDns

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `VpcDns` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcDNSSpec | VpcDns 具体配置信息字段 |
| status | VpcDNSStatus | VpcDns 状态信息字段 |

#### VpcDNSSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| replicas | Int32 | 副本数量 |
| vpc | String | 所属 VPC |
| subnet | String | 所属子网 |
