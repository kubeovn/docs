# Kube-OVN 接口规范

基于 Kube-OVN v1.12.0 版本，整理了 Kube-OVN 支持的 CRD 资源列表，列出 CRD 定义各字段的取值类型和含义，以供参考。

## 通用的 Condition 定义

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| type | String | 状态类型 |
| status | String | 状态值，取值为 `True`，`False` 或 `Unknown` |
| reason | String | 状态变化的原因 |
| message | String | 状态变化的具体信息 |
| lastUpdateTime | Time | 上次状态更新时间 |
| lastTransitionTime | Time | 上次状态类型发生变化的时间 |

在各 CRD 的定义中，Status 中的 Condition 字段，都遵循上述格式，因此提前进行说明。

## Subnet 定义

### Subnet

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Subnet` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | SubnetSpec | Subnet 具体配置信息字段 |
| status | SubnetStatus | Subnet 状态信息字段 |

#### SubnetSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| default | Bool | 该子网是否为默认子网 |
| vpc | String | 子网所属 Vpc，默认为 ovn-cluster |
| protocol | String | IP 协议，取值可以为 `IPv4`，`IPv6` 或 `Dual` |
| namespaces | []String | 该子网所绑定的 namespace 列表 |
| cidrBlock | String | 子网的网段范围，如 10.16.0.0/16 |
| gateway | String | 子网网关地址，默认为该子网 CIDRBlock 下的第一个可用地址 |
| excludeIps | []String | 该子网下不会被自动分配的地址范围 |
| provider | String | 默认为 ovn。多网卡情况下可以配置取值为 NetworkAttachmentDefinition 的 <name>.<namespace>，Kube-OVN 将会使用这些信息找到对应的 Subnet 资源 |
| gatewayType | String | Overlay 模式下的网关类型，取值可以为 `distributed` 或 `centralized` |
| gatewayNode | String | 当网关模式为 centralized 时的网关节点，可以为逗号分隔的多个节点 |
| natOutgoing | Bool | 出网流量是否进行 NAT。该参数和 `externalEgressGateway` 参数不能同时设置。 |
| externalEgressGateway | String | 外部网关地址。需要和子网网关节点在同一个二层可达域，该参数和 `natOutgoing` 参数不能同时设置 |
| policyRoutingPriority | Uint32 | 策略路由优先级。添加策略路由使用参数，控制流量经子网网关之后，转发到外部网关地址 |
| policyRoutingTableID | Uint32 | 使用的本地策略路由表的 TableID，每个子网均需不同以避免冲突 |
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
| u2oInterconnection | Bool | 是否开启 Overlay/Underlay 的互联模式 |
| enableLb | *Bool | 控制子网对应的 logical-switch 是否关联 load-balancer 记录 |
| enableEcmp | Bool | 集中式网关，是否开启 ECMP 路由 |

##### Acl

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| direction | String | Acl 限制方向，取值为 `from-lport` 或者 `to-lport` |
| priority | Int | Acl 优先级，取值范围 0 到 32767 |
| match | String | Acl 规则匹配表达式 |
| action | String | Acl 规则动作，取值为 `allow-related`, `allow-stateless`, `allow`, `drop`, `reject` 其中一个 |

#### SubnetStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []SubnetCondition | 子网状态变化信息，具体字段参考文档开头 Condition 定义 |
| v4AvailableIPs | Float64 | 子网现在可用的 IPv4 IP 地址数量 |
| v4availableIPrange | String | 子网现在可用的 IPv4 地址范围 |
| v4UsingIPs | Float64 | 子网现在已用的 IPv4 IP 地址数量 |
| v4usingIPrange | String | 子网现在已用的 IPv4 地址范围 |
| v6AvailableIPs | Float64 | 子网现在可用的 IPv6 IP 地址数量 |
| v6availableIPrange | String | 子网现在可用的 IPv6 地址范围 |
| v6UsingIPs | Float64 | 子网现在已用的 IPv6 IP 地址数量 |
| v6usingIPrange | String | 子网现在已用的 IPv6 地址范围 |
| sctivateGateway | String | 集中式子网，主备模式下当前正在工作的网关节点 |
| dhcpV4OptionsUUID | String | 子网下 lsp dhcpv4_options 关联的 DHCP_Options 记录标识 |
| dhcpV6OptionsUUID | String | 子网下 lsp dhcpv6_options 关联的 DHCP_Options 记录标识 |
| u2oInterconnectionIP | String | 开启 Overlay/Underlay 互联模式后，所占用的用于互联的 IP 地址 |

## IP 定义

### IP

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IP` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IPSpec | IP 具体配置信息字段 |

#### IPSepc

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| podName | String | 绑定 Pod 名称 |
| namespace | String | 绑定 Pod 所在 Namespace 名称 |
| subnet | String | IP 所属 Subnet |
| attachSubnets | []String | 该主 IP 下其他附属子网名称（字段废弃不再使用） |
| nodeName | String | 绑定 Pod 所在的节点名称 |
| ipAddress | String | IP 地址，双栈情况下为 `v4IP,v6IP` 格式 |
| v4IPAddress | String | IPv4 IP 地址 |
| v6IPAddress | String | IPv6 IP 地址 |
| attachIPs | []String | 该主 IP 下其他附属 IP 地址（字段废弃不再使用） |
| macAddress | String | 绑定 Pod 的 Mac 地址 |
| attachMacs | []String | 该主 IP 下其他附属 Mac 地址（字段废弃不再使用） |
| containerID | String | 绑定 Pod 对应的 Container ID |
| podType | String | 特殊工作负载 Pod，可为 `StatefulSet`，`VirtualMachine` 或空 |

## Underlay 配置

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

## Vpc 定义

### Vpc

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Vpc` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcSpec | Vpc 具体配置信息字段 |
| status | VpcStatus | Vpc 状态信息字段 |

#### VpcSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| namespaces | []String | Vpc 绑定的命名空间列表 |
| staticRoutes | []*StaticRoute | Vpc 下配置的静态路由信息 |
| policyRoutes | []*PolicyRoute | Vpc 下配置的策略路由信息 |
| vpcPeerings | []*VpcPeering | Vpc 互联信息 |
| enableExternal | Bool | Vpc 是否连接到外部交换机 |

##### StaticRoute

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| policy | String | 路由策略，取值为 `policySrc` 或者 `policyDst` |
| cidr | String | 路由 Cidr 网段 |
| nextHopIP | String | 路由下一跳信息 |

##### PolicyRoute

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| priority | Int32 | 策略路由优先级 |
| match | String | 策略路由匹配条件 |
| action | String | 策略路由动作，取值为 `allow`、`drop` 或者 `reroute` |
| nextHopIP | String | 策略路由下一跳信息，ECMP 路由情况下下一跳地址使用逗号隔开 |

##### VpcPeering

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| remoteVpc | String | Vpc 互联对端 Vpc 名称 |
| localConnectIP | String | Vpc 互联本端 IP 地址 |

#### VpcStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []VpcCondition | Vpc 状态变化信息，具体字段参考文档开头 Condition 定义 |
| standby | Bool | 标识 Vpc 是否创建完成，Vpc 下的 Subnet 需要等 Vpc 创建完成转换再继续处理 |
| default | Bool | 是否是默认 Vpc |
| defaultLogicalSwitch | String | Vpc 下的默认子网 |
| router | String | Vpc 对应的 logical-router 名称 |
| tcpLoadBalancer | String | Vpc 下的 TCP LB 信息 |
| udpLoadBalancer | String | Vpc 下的 UDP LB 信息 |
| tcpSessionLoadBalancer | String | Vpc 下的 TCP 会话保持 LB 信息 |
| udpSessionLoadBalancer | String | Vpc 下的 UDP 会话保持 LB 信息 |
| subnets | []String | Vpc 下的子网列表 |
| vpcPeerings | []String | Vpc 互联的对端 Vpc 列表 |
| enableExternal| Bool | Vpc 是否连接到外部交换机 |

### VpcNatGateway

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `VpcNatGateway` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcNatSpec | Vpc 网关具体配置信息字段 |

#### VpcNatSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vpc | String | Vpc 网关 Pod 所在的 Vpc 名称 |
| subnet | String | Vpc 网关 Pod 所属的子网名称 |
| lanIp | String | Vpc 网关 Pod 指定分配的 IP 地址 |
| selector | []String | 标准 Kubernetes Selector 匹配信息 |
| tolerations | []VpcNatToleration | 标准 Kubernetes 容忍信息 |

##### VpcNatToleration

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| key | String | 容忍污点的 key 信息 |
| operator | String | 取值为 `Exists` 或者 `Equal` |
| value | String | 容忍污点的 value 信息 |
| effect | String | 容忍污点的作用效果，取值为 `NoExecute` 、`NoSchedule` 或者 `PreferNoSchedule` |
| tolerationSeconds | Int64 | 添加污点后，Pod 还能继续在节点上运行的时间 |

以上容忍字段的含义，可以参考 Kubernetes 官方文档 [污点和容忍度](https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/){: target="_blank" }。

### IptablesEIP

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesEIP` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesEipSpec | Vpc 网关使用的 IptablesEIP 具体配置信息字段 |
| status | IptablesEipStatus | Vpc 网关使用的 IptablesEIP 状态信息 |

#### IptablesEipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| v4ip | String | IptablesEIP v4 地址 |
| v6ip | String | IptablesEIP v6 地址 |
| macAddress | String | IptablesEIP crd 记录分配的 mac 地址，没有实际使用 |
| natGwDp | String | Vpc 网关名称 |

#### IptablesEipStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | IptablesEIP 是否配置完成 |
| ip | String | IptablesEIP 使用的 IP 地址，目前只支持了 IPv4 地址 |
| redo | String | IptablesEIP crd 创建或者更新时间 |
| nat | String | IptablesEIP 的使用类型，取值为 `fip`、`snat` 或者 `dnat` |
| conditions | []IptablesEIPCondition | IptablesEIP 状态变化信息，具体字段参考文档开头 Condition 定义 |

### IptablesFIPRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesFIPRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesFIPRuleSpec | Vpc 网关使用的 IptablesFIPRule 具体配置信息字段 |
| status | IptablesFIPRuleStatus | Vpc 网关使用的 IptablesFIPRule 状态信息 |

#### IptablesFIPRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| eip | String | IptablesFIPRule 使用的 IptablesEIP 名称 |
| internalIp | String | IptablesFIPRule 对应的内部的 IP 地址 |

#### IptablesFIPRuleStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | IptablesFIPRule 是否配置完成 |
| v4ip | String | IptablesEIP 使用的 v4 IP 地址 |
| v6ip | String | IptablesEIP 使用的 v6 IP 地址 |
| natGwDp | String | Vpc 网关名称 |
| redo | String | IptablesFIPRule crd 创建或者更新时间 |
| conditions | []IptablesFIPRuleCondition | IptablesFIPRule 状态变化信息，具体字段参考文档开头 Condition 定义 |

### IptablesSnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesSnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesSnatRuleSpec | Vpc 网关使用的 IptablesSnatRule 具体配置信息字段 |
| status | IptablesSnatRuleStatus | Vpc 网关使用的 IptablesSnatRule 状态信息 |

#### IptablesSnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| eip | String | IptablesSnatRule 使用的 IptablesEIP 名称 |
| internalIp | String | IptablesSnatRule 对应的内部的 IP 地址 |

#### IptablesSnatRuleStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | IptablesSnatRule 是否配置完成 |
| v4ip | String | IptablesSnatRule 使用的 v4 IP 地址 |
| v6ip | String | IptablesSnatRule 使用的 v6 IP 地址 |
| natGwDp | String | Vpc 网关名称 |
| redo | String | IptablesSnatRule crd 创建或者更新时间 |
| conditions | []IptablesSnatRuleCondition | IptablesSnatRule 状态变化信息，具体字段参考文档开头 Condition 定义 |

### IptablesDnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `IptablesDnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | IptablesDnatRuleSpec | Vpc 网关使用的 IptablesDnatRule 具体配置信息字段 |
| status | IptablesDnatRuleStatus | Vpc 网关使用的 IptablesDnatRule 状态信息 |

#### IptablesDnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| eip | Sting | Vpc 网关配置 IptablesDnatRule 使用的 IptablesEIP 名称 |
| externalPort | Sting | Vpc 网关配置 IptablesDnatRule 使用的外部端口 |
| protocol | Sting | Vpc 网关配置 IptablesDnatRule 的协议类型 |
| internalIp | Sting | Vpc 网关配置 IptablesDnatRule 使用的内部 IP 地址 |
| internalPort | Sting | Vpc 网关配置 IptablesDnatRule 使用的内部端口 |

#### IptablesDnatRuleStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | IptablesDnatRule 是否配置完成 |
| v4ip | String | IptablesDnatRule 使用的 v4 IP 地址 |
| v6ip | String | IptablesDnatRule 使用的 v6 IP 地址 |
| natGwDp | String | Vpc 网关名称 |
| redo | String | IptablesDnatRule crd 创建或者更新时间 |
| conditions | []IptablesDnatRuleCondition | IptablesDnatRule 状态变化信息，具体字段参考文档开头 Condition 定义 |

### VpcDns

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `VpcDns` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VpcDnsSpec | VpcDns 具体配置信息字段 |
| status | VpcDnsStatus | VpcDns 状态信息 |

#### VpcDnsSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vpc | String | VpcDns 所在的 Vpc 名称 |
| subnet | String | VpcDns Pod 分配地址的 Subnet 名称 |

#### VpcDnsStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []VpcDnsCondition | VpcDns 状态变化信息，具体字段参考文档开头 Condition 定义 |
| active | Bool | VpcDns 是否正在使用 |

VpcDns 的详细使用文档，可以参考 [自定义 VPC 内部 DNS](../advance/vpc-internal-dns.md)。

### SwitchLBRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `SwitchLBRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | SwitchLBRuleSpec | SwitchLBRule 具体配置信息字段 |
| status | SwitchLBRuleStatus | SwitchLBRule 状态信息 |

#### SwitchLBRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| vip | String | SwitchLBRule 配置的 vip 地址 |
| namespace | String | SwitchLBRule 的命名空间 |
| selector | []String | 标准 Kubernetes Selector 匹配信息 |
| sessionAffinity | String | 标准 Kubernetes Service 中 sessionAffinity 取值 |
| ports | []SlrPort | SwitchLBRule 端口列表 |

SwitchLBRule 的详细配置信息，可以参考 [自定义 VPC 内部负载均衡](../advance/vpc-internal-lb.md)。

##### SlrPort

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

## 安全组与 Vip

### SecurityGroup

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `SecurityGroup` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | SecurityGroupSpec | 安全组具体配置信息字段 |
| status | SecurityGroupStatus | 安全组状态信息 |

#### SecurityGroupSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ingressRules | []*SgRule | 入方向安全组规则 |
| egressRules | []*SgRule | 出方向安全组规则 |
| allowSameGroupTraffic | Bool | 同一安全组内的 lsp 是否可以互通，以及流量规则是否需要更新 |

##### SgRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ipVersion | String | IP 版本号，取值为 `ipv4` 或者 `ipv6` |
| protocol | String | 取值为 `all`、`icmp`、`tcp` 或者 `udp` |
| priority | Int | Acl 优先级，取值范围为 1-200，数值越小，优先级越高 |
| remoteType | String | 取值为 `address` 或者 `securityGroup` |
| remoteAddress | String | 对端地址 |
| remoteSecurityGroup | String | 对端安全组 |
| portRangeMin | Int | 端口范围起始值，最小取值为 1 |
| portRangeMax | Int | 端口范围最大值，最大取值为 65535 |
| policy | String | 取值为 `allow` 或者 `drop` |

#### SecurityGroupStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| portGroup | String | 安全组对应的 port-group 名称 |
| allowSameGroupTraffic | Bool | 同一安全组内的 lsp 是否可以互通，以及安全组的流量规则是否需要更新 |
| ingressMd5 | String | 入方向安全组规则 MD5 取值 |
| egressMd5 | String | 出方向安全组规则 MD5 取值 |
| ingressLastSyncSuccess | Bool | 入方向规则上一次同步是否成功 |
| egressLastSyncSuccess | Bool | 出方向规则上一次同步是否成功 |

### Vip

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `Vip` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | VipSpec | Vip 具体配置信息字段 |
| status | VipStatus | Vip 状态信息 |

#### VipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| namespace | String | Vip 所在命名空间 |
| subnet | String | Vip 所属子网 |
| v4ip | String | Vip v4 IP 地址 |
| v6ip | String | Vip v6 IP 地址 |
| macAddress | String | Vip mac 地址 |
| parentV4ip | String | 目前没有使用 |
| parentV6ip | String | 目前没有使用 |
| parentMac | String | 目前没有使用 |
| attachSubnets | []String | 该字段废弃，不再使用 |

#### VipStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []VipCondition | Vip 状态变化信息，具体字段参考文档开头 Condition 定义 |
| ready | Bool | Vip 是否准备好 |
| v4ip | String | Vip v4 IP 地址，应该和 spec 字段取值一致 |
| v6ip | String | Vip v6 IP 地址，应该和 spec 字段取值一致 |
| mac | String | Vip mac 地址，应该和 spec 字段取值一致 |
| pv4ip | String | 目前没有使用 |
| pv6ip | String | 目前没有使用 |
| pmac | String | 目前没有使用 |

### OvnEip

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnEip` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnEipSpec | 默认 Vpc 使用 OvnEip 具体配置信息字段 |
| status | OvnEipStatus | 默认 Vpc 使用 OvnEip 状态信息 |

#### OvnEipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| externalSubnet | String | OvnEip 所在的子网名称 |
| v4Ip | String | OvnEip IPv4 地址 |
| v6Ip | String | OvnEip IPv6 地址 |
| macAddress | String | OvnEip Mac 地址 |
| type | String | OvnEip 使用类型，取值有 `lrp`、`lsp` 或者 `nat` |

#### OvnEipStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| conditions | []OvnEipCondition | 默认 Vpc OvnEip 状态变化信息，具体字段参考文档开头 Condition 定义 |
| type | String | OvnEip 使用类型, 可以是 `lrp`, `lsp` or `nat` |
| nat | String | dnat snat fip |
| v4Ip | String | OvnEip 使用的 v4 IP 地址 |
| v6Ip | String | OvnEip 使用的 v6 IP 地址 |
| macAddress | String | OvnEip 使用的 Mac 地址 |

### OvnFip

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnFip` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnFipSpec | 默认 Vpc 使用 OvnFip 具体配置信息字段 |
| status | OvnFipStatus | 默认 Vpc 使用 OvnFip 状态信息 |

#### OvnFipSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ovnEip | String | OvnFip 绑定的 OvnEip 名称 |
| ipType | String | vip 或者 ip crd ("" 表示 ip crd) |
| ipName | String | OvnFip 绑定 Pod 对应的 IP crd 名称 |
| vpc | String | Pod 所在的 VPC 的名字 |
| V4Ip | String |IP 或者 VIP 的 IPv4 地址 |

#### OvnFipStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | OvnFip 是否配置完成 |
| v4Eip | String | OvnFip 绑定的 OvnEip 名称 |
| v4Ip | String | OvnFip 当前使用的 OvnEip 地址 |
| vpc | String | OvnFip 所在的 Vpc 名称 |
| conditions | []OvnFipCondition | OvnFip 状态变化信息，具体字段参考文档开头 Condition 定义 |

### OvnSnatRule

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| apiVersion | String | 标准 Kubernetes 版本信息字段，所有自定义资源该值均为 kubeovn.io/v1 |
| kind | String | 标准 Kubernetes 资源类型字段，本资源所有实例该值均为 `OvnSnatRule` |
| metadata | ObjectMeta | 标准 Kubernetes 资源元数据信息 |
| spec | OvnSnatRuleSpec | 默认 Vpc OvnSnatRule 具体配置信息字段 |
| status | OvnSnatRuleStatus | 默认 Vpc OvnSnatRule 状态信息 |

#### OvnSnatRuleSpec

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ovnEip | String | OvnSnatRule 绑定的 OvnEip 名称 |
| vpcSubnet | String | OvnSnatRule 配置的子网名称 |
| vpc | String | Pod 所在的 VPC |
| ipName | String | OvnSnatRule 绑定 Pod 对应的 IP crd 名称 |
| v4IpCidr | String | vpc subnet 的 IPv4 cidr  |

#### OvnSnatRuleStatus

| 属性名称 | 类型 | 描述 |
| --- | --- | --- |
| ready | Bool | OvnSnatRule 是否配置完成 |
| v4Eip | String | OvnSnatRule 绑定的 OvnEip 地址 |
| v4IpCidr | String | 在 logical-router 中配置 snat 转换使用的 cidr 地址 |
| vpc | String | OvnSnatRule 所在的 Vpc 名称 |
| conditions | []OvnSnatRuleCondition | OvnSnatRule 状态变化信息，具体字段参考文档开头 Condition 定义 |
