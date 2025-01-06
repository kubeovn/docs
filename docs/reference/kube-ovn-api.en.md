# Kube-OVN API Reference

Based on Kube-OVN v1.12.0, we have compiled a list of CRD resources supported by Kube-OVN, listing the types and meanings of each field of CRD definition for reference.

## Generic Condition Definition

| Property Name | Type | Description |
| --- | --- | --- |
| type | String | Type of status |
| status | String | The value of status, in the range of `True`, `False` or `Unknown` |
| reason | String | The reason for the status change |
| message | String | The specific message of the status change |
| lastUpdateTime | Time | The last time the status was updated |
| lastTransitionTime | Time | Time of last status type change |

In each CRD definition, the Condition field in Status follows the above format, so we explain it in advance.

## Subnet Definition

### Subnet

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Subnet` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | SubnetSpec | Subnet specific configuration information |
| status | SubnetStatus | Subnet status information |

#### SubnetSpec

| Property Name | Type | Description |
| --- | --- | --- |
| default | Bool | Whether this subnet is the default subnet |
| vpc | String | The vpc which the subnet belongs to, default is ovn-cluster |
| protocol | String | IP protocol, the value is in the range of `IPv4`, `IPv6` or `Dual` |
| namespaces | []String | The list of namespaces bound to this subnet |
| cidrBlock | String | The range of the subnet, e.g. 10.16.0.0/16 |
| gateway | String | The gateway address of the subnet, the default value is the first available address under the CIDRBlock of the subnet |
| excludeIps | []String | The range of addresses under this subnet that will not be automatically assigned |
| provider | String | Default value is `ovn`. In the case of multiple NICs, the value is `<name>.<namespace>` of the NetworkAttachmentDefinition, Kube-OVN will use this information to find the corresponding subnet resource |
| gatewayType | String | The gateway type in overlay mode, either `distributed` or `centralized` |
| gatewayNode | String | The gateway node when the gateway mode is centralized, node names can be comma-separated |
| natOutgoing | Bool | Whether the outgoing traffic is NAT |
| externalEgressGateway | String | The address of the external gateway. This parameter and the natOutgoing parameter cannot be set at the same time |
| policyRoutingPriority | Uint32 | Policy route priority. Used to control the forwarding of traffic to the external gateway address after the subnet gateway |
| policyRoutingTableID | Uint32 | The TableID of the local policy routing table, should be different for each subnet to avoid conflicts |
| private | Bool | Whether the subnet is a private subnet, which denies access to addresses inside the subnet if the subnet is private |
| allowSubnets | []String | If the subnet is a private subnet, the set of addresses that are allowed to access the subnet |
| vlan | String | The name of vlan to which the subnet is bound |
| vips | []String | The virtual-ip parameter information for virtual type lsp on the subnet |
| logicalGateway | Bool | Whether to enable logical gateway |
| disableGatewayCheck | Bool | Whether to skip the gateway connectivity check when creating a pod |
| disableInterConnection | Bool | Whether to enable subnet interconnection across clusters |
| enableDHCP | Bool | Whether to configure dhcp configuration options for lsps belong this subnet |
| dhcpV4Options | String | The DHCP_Options record associated with lsp dhcpv4_options on the subnet |
| dhcpV6Options | String | The DHCP_Options record associated with lsp dhcpv6_options on the subnet |
| enableIPv6RA | Bool | Whether to configure the ipv6_ra_configs parameter for the lrp port of the router connected to the subnet |
| ipv6RAConfigs | String | The ipv6_ra_configs parameter configuration for the lrp port of the router connected to the subnet |
| acls | []Acl | The acls record associated with the logical-switch of the subnet |
| u2oInterconnection | Bool | Whether to enable interconnection mode for Overlay/Underlay |
| enableLb | *Bool | Whether the logical-switch of the subnet is associated with load-balancer records |
| enableEcmp | Bool | Centralized subnet, whether to enable ECMP routing |

##### Acl

| Property Name | Type | Description |
| --- | --- | --- |
| direction | String | Restrict the direction of acl, which value is `from-lport` or `to-lport` |
| priority | Int | Acl priority, in the range 0 to 32767 |
| match | String | Acl rule match expression |
| action | String | The action of the rule, which value is in the range of `allow-related`, `allow-stateless`, `allow`, `drop`, `reject` |

#### SubnetStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []SubnetCondition | Subnet status change information, refer to the beginning of the document for the definition of Condition |
| v4AvailableIPs | Float64 | Number of available IPv4 IPs |
| v4availableIPrange | String | The available range of IPv4 addresses on the subnet |
| v4UsingIPs | Float64 | Number of used IPv4 IPs |
| v4usingIPrange | String | Used IPv4 address ranges on the subnet |
| v6AvailableIPs | Float64 | Number of available IPv6 IPs |
| v6availableIPrange | String | The available range of IPv6 addresses on the subnet |
| v6UsingIPs | Float64 | Number of used IPv6 IPs |
| v6usingIPrange | String | Used IPv6 address ranges on the subnet |
| sctivateGateway | String | The currently working gateway node in centralized subnet of master-backup mode |
| dhcpV4OptionsUUID | String | The DHCP_Options record identifier associated with the lsp dhcpv4_options on the subnet |
| dhcpV6OptionsUUID | String | The DHCP_Options record identifier associated with the lsp dhcpv6_options on the subnet |
| u2oInterconnectionIP | String | The IP address used for interconnection when Overlay/Underlay interconnection mode is enabled |

## IP Definition

### IP

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource have the value `IP` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IPSpec | IP specific configuration information |

#### IPSepc

| Property Name | Type | Description |
| --- | --- | --- |
| podName | String | Pod name which assigned with this IP |
| namespace | String | The name of the namespace where the pod is bound |
| subnet | String | The subnet which the ip belongs to |
| attachSubnets | []String | The name of the other subnets attached to this primary IP (field deprecated) |
| nodeName | String | The name of the node where the pod is bound |
| ipAddress | String | IP address, in `v4IP,v6IP` format for dual-stack cases |
| v4IPAddress | String | IPv4 IP address |
| v6IPAddress | String | IPv6 IP address |
| attachIPs | []String | Other IP addresses attached to this primary IP (field is deprecated) |
| macAddress | String | The Mac address of the bound pod |
| attachMacs | []String | Other Mac addresses attached to this primary IP (field deprecated) |
| containerID | String | The Container ID corresponding to the bound pod |
| podType | String | Special workload pod, can be `StatefulSet`, `VirtualMachine` or empty |

## Underlay configuration

### Vlan

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all instances of this resource will be kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Vlan` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VlanSpec | Vlan specific configuration information |
| status | VlanStatus | Vlan status information |

#### VlanSpec

| Property Name | Type | Description |
| --- | --- | --- |
| id | Int | Vlan tag number, in the range of 0~4096 |
| provider | String | The name of the ProviderNetwork to which the vlan is bound |

#### VlanStatus

| Property Name | Type | Description |
| --- | --- | --- |
| subnets | []String | The list of subnets to which the vlan is bound |
| conditions | []VlanCondition | Vlan status change information, refer to the beginning of the document for the definition of Condition |

### ProviderNetwork

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `ProviderNetwork` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | ProviderNetworkSpec | ProviderNetwork specific configuration information |
| status | ProviderNetworkStatus | ProviderNetwork status information |

#### ProviderNetworkSpec

| Property Name | Type | Description |
| --- | --- | --- |
| defaultInterface | String | The name of the NIC interface used by default for this bridge network |
| customInterfaces | []CustomInterface | The special NIC configuration used by this bridge network |
| excludeNodes | []String | The names of the nodes that will not be bound to this bridge network |
| exchangeLinkName | Bool | Whether to exchange the bridge NIC and the corresponding OVS bridge name |

##### CustomInterface

| Property Name | Type | Description |
| --- | --- | --- |
| interface | String | NIC interface name used for underlay |
| nodes | []String | List of nodes using the custom NIC interface |

#### ProviderNetworkStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | Whether the current bridge network is in the ready state |
| readyNodes | []String | The name of the node whose bridge network is ready |
| notReadyNodes | []String | The name of the node whose bridge network is not ready |
| vlans | []String | The name of the vlan to which the bridge network is bound |
| conditions | []ProviderNetworkCondition | ProviderNetwork status change information, refer to the beginning of the document for the definition of Condition |

## Vpc Definition

### Vpc

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Vpc` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcSpec | Vpc specific configuration information |
| status | VpcStatus | Vpc status information |

#### VpcSpec

| Property Name | Type | Description |
| --- | --- | --- |
| namespaces | []String | List of namespaces bound by Vpc |
| staticRoutes | []*StaticRoute | The static route information configured under Vpc |
| policyRoutes | []*PolicyRoute | The policy route information configured under Vpc |
| vpcPeerings | []*VpcPeering | Vpc interconnection information |
| enableExternal | Bool | Whether vpc is connected to an external switch |
| defaultSubnet | String | Name of the subnet that should be used by custom Vpc as the default one |

##### StaticRoute

| Property Name | Type | Description |
| --- | --- | --- |
| policy | String | Routing policy, takes the value of `policySrc` or `policyDst` |
| cidr | String | Routing cidr value |
| nextHopIP | String | The next hop information of the route |

##### PolicyRoute

| Property Name | Type | Description |
| --- | --- | --- |
| priority | Int32 | Priority for policy route |
| match | String | Match expression for policy route |
| action | String | Action for policy route, the value is in the range of `allow`, `drop`, `reroute` |
| nextHopIP | String | The next hop of the policy route, separated by commas in the case of ECMP routing |

##### VpcPeering

| Property Name | Type | Description |
| --- | --- | --- |
| remoteVpc | String | Name of the interconnected peering vpc |
| localConnectIP | String | The local ip for vpc used to connect to peer vpc |

#### VpcStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []VpcCondition | Vpc status change information, refer to the beginning of the documentation for the definition of Condition |
| standby | Bool | Whether the vpc creation is complete, the subnet under the vpc needs to wait for the vpc creation to complete other proceeding |
| default | Bool | Whether it is the default vpc |
| defaultLogicalSwitch | String | The default subnet under vpc |
| router | String | The logical-router name for the vpc |
| tcpLoadBalancer | String | TCP LB information for vpc |
| udpLoadBalancer | String | UDP LB information for vpc |
| tcpSessionLoadBalancer | String | TCP Session Hold LB Information for Vpc |
| udpSessionLoadBalancer | String | UDP session hold LB information for Vpc |
| subnets | []String | List of subnets for vpc |
| vpcPeerings | []String | List of peer vpcs for vpc interconnection |
| enableExternal| Bool | Whether the vpc is connected to an external switch |

### VpcNatGateway

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `VpcNatGateway` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcNatSpec | Vpc gateway specific configuration information |

#### VpcNatSpec

| Property Name | Type | Description |
| --- | --- | --- |
| vpc | String | Vpc name which the vpc gateway belongs to |
| subnet | String | The name of the subnet to which the gateway pod belongs |
| lanIp | String | The IP address assigned to the gateway pod |
| selector | []String | Standard Kubernetes selector match information |
| tolerations | []VpcNatToleration | Standard Kubernetes tolerance information |

##### VpcNatToleration

| Property Name | Type | Description |
| --- | --- | --- |
| key | String | The key information of the taint tolerance |
| operator | String | Takes the value of `Exists` or `Equal` |
| value | String | The value information of the taint tolerance |
| effect | String | The effect of the taint tolerance, takes the value of `NoExecute`, `NoSchedule`, or `PreferNoSchedule` |
| tolerationSeconds | Int64 | The amount of time the pod can continue to run on the node after the taint is added |

The meaning of the above tolerance fields can be found in the official Kubernetes documentation [Taint and Tolerance](https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/){: target="_blank" }.

### IptablesEIP

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource have the value `IptablesEIP` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesEipSpec | IptablesEIP specific configuration information used by vpc gateway |
| status | IptablesEipStatus | IptablesEIP status information used by vpc gateway |

#### IptablesEipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| v4ip | String | IptablesEIP v4 address |
| v6ip | String | IptablesEIP v6 address |
| macAddress | String | The assigned mac address, not actually used |
| natGwDp | String | Vpc gateway name |

#### IptablesEipStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | Whether IptablesEIP is configured complete |
| ip | String | The IP address used by IptablesEIP, currently only IPv4 addresses are supported |
| redo | String | IptablesEIP crd creation or update time |
| nat | String | The type of IptablesEIP, either `fip`, `snat`, or `dnat` |
| conditions | []IptablesEIPCondition | IptablesEIP status change information, refer to the beginning of the documentation for the definition of Condition |

### IptablesFIPRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource have the value `IptablesFIPRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesFIPRuleSpec | The IptablesFIPRule specific configuration information used by vpc gateway |
| status | IptablesFIPRuleStatus | IptablesFIPRule status information used by vpc gateway |

#### IptablesFIPRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| eip | String | Name of the IptablesEIP used for IptablesFIPRule |
| internalIp | String | The corresponding internal IP address |

#### IptablesFIPRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | Whether IptablesFIPRule is configured or not |
| v4ip | String | The v4 IP address used by IptablesEIP |
| v6ip | String | The v6 IP address used by IptablesEIP |
| natGwDp | String | Vpc gateway name |
| redo | String | IptablesFIPRule crd creation or update time |
| conditions | []IptablesFIPRuleCondition | IptablesFIPRule status change information, refer to the beginning of the documentation for the definition of Condition |

### IptablesSnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource have the value `IptablesSnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesSnatRuleSpec | The IptablesSnatRule specific configuration information used by the vpc gateway |
| status | IptablesSnatRuleStatus | IptablesSnatRule status information used by vpc gateway |

#### IptablesSnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| eip | String | Name of the IptablesEIP used by IptablesSnatRule |
| internalIp | String | IptablesSnatRule's corresponding internal IP address |

#### IptablesSnatRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | Whether the configuration is complete |
| v4ip | String | The v4 IP address used by IptablesSnatRule |
| v6ip | String | The v6 IP address used by IptablesSnatRule |
| natGwDp | String | Vpc gateway name |
| redo | String | IptablesSnatRule crd creation or update time |
| conditions | []IptablesSnatRuleCondition | IptablesSnatRule status change information, refer to the beginning of the documentation for the definition of Condition |

### IptablesDnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource have the value `IptablesDnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesDnatRuleSpec | The IptablesDnatRule specific configuration information used by vpc gateway |
| status | IptablesDnatRuleStatus | IptablesDnatRule status information used by vpc gateway |

#### IptablesDnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| eip | Sting | Name of IptablesEIP used by IptablesDnatRule |
| externalPort | Sting | External port used by IptablesDnatRule |
| protocol | Sting | Vpc gateway dnat protocol type |
| internalIp | Sting | Internal IP address used by IptablesDnatRule |
| internalPort | Sting | Internal port used by IptablesDnatRule |

#### IptablesDnatRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | Whether the configuration is complete |
| v4ip | String | The v4 IP address used by IptablesDnatRule |
| v6ip | String | The v6 IP address used by IptablesDnatRule |
| natGwDp | String | Vpc gateway name |
| redo | String | IptablesDnatRule crd creation or update time |
| conditions | []IptablesDnatRuleCondition | IptablesDnatRule Status change information, refer to the beginning of the documentation for the definition of Condition |

### VpcDns

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `VpcDns` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcDnsSpec | VpcDns specific configuration information |
| status | VpcDnsStatus | VpcDns status information |

#### VpcDnsSpec

| Property Name | Type | Description |
| --- | --- | --- |
| vpc | String | Name of the vpc where VpcDns is located |
| subnet | String | The subnet name of the address assigned to the VpcDns pod |

#### VpcDnsStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []VpcDnsCondition | VpcDns status change information, refer to the beginning of the document for the definition of Condition |
| active | Bool | Whether VpcDns is in use |

For detailed documentation on the use of VpcDns, see [Customizing VPC DNS](../vpc/vpc-internal-dns.md).

### SwitchLBRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `SwitchLBRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | SwitchLBRuleSpec | SwitchLBRule specific configuration information |
| status | SwitchLBRuleStatus | SwitchLBRule status information |

#### SwitchLBRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| vip | String | Vip address of SwitchLBRule |
| namespace | String | SwitchLBRule's namespace |
| selector | []String | Standard Kubernetes selector match information |
| sessionAffinity | String | Standard Kubernetes service sessionAffinity value |
| ports | []SlrPort | List of SwitchLBRule ports |

For detailed configuration information of SwitchLBRule, you can refer to [Customizing VPC Internal Load Balancing health check](../vpc/vpc-internal-lb.md).

##### SlrPort

| Property Name | Type | Description |
| --- | --- | --- |
| name | String | Port name |
| port | Int32 | Port number |
| targetPort | Int32 | Target port of SwitchLBRule |
| protocol | String | Protocol type |

#### SwitchLBRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []SwitchLBRuleCondition | SwitchLBRule status change information, refer to the beginning of the document for the definition of Condition |
| ports | String | Port information |
| service | String | Name of the service |

## Security Group and Vip

### SecurityGroup

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have a value of `SecurityGroup` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | SecurityGroupSpec | Security Group specific configuration information |
| status | SecurityGroupStatus | Security group status information |

#### SecurityGroupSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ingressRules | []*SgRule | Inbound security group rules |
| egressRules | []*SgRule | Outbound security group rules |
| allowSameGroupTraffic | Bool | Whether lsps in the same security group can interoperate and whether traffic rules need to be updated |

##### SgRule

| Property Name | Type | Description |
| --- | --- | --- |
| ipVersion | String | IP version number, `ipv4` or `ipv6` |
| protocol | String | The value of `icmp`, `tcp`, or `udp` |
| priority | Int | Acl priority. The value range is 1-200, the smaller the value, the higher the priority. |
| remoteType | String | The value is either `address` or `securityGroup` |
| remoteAddress | String | The address of the other side |
| remoteSecurityGroup | String | The name of security group on the other side |
| portRangeMin | Int | The starting value of the port range, the minimum value is 1. |
| portRangeMax | Int | The ending value of the port range, the maximum value is 65535. |
| policy | String | The value is `allow` or `drop` |

#### SecurityGroupStatus

| Property Name | Type | Description |
| --- | --- | --- |
| portGroup | String | The name of the port-group for the security group |
| allowSameGroupTraffic | Bool | Whether lsps in the same security group can interoperate, and whether the security group traffic rules need to be updated |
| ingressMd5 | String | The MD5 value of the inbound security group rule |
| egressMd5 | String | The MD5 value of the outbound security group rule |
| ingressLastSyncSuccess | Bool | Whether the last synchronization of the inbound rule was successful |
| egressLastSyncSuccess | Bool | Whether the last synchronization of the outbound rule was successful |

### Vip

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Vip` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VipSpec | Vip specific configuration information |
| status | VipStatus | Vip status information |

#### VipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| namespace | String | Vip's namespace |
| subnet | String | Vip's subnet |
| type | String | The type of Vip, either `switch_lb_vip`, or empty |
| v4ip | String | Vip IPv4 ip address |
| v6ip | String | Vip IPv6 ip address |
| macAddress | String | Vip mac address |
| parentV4ip | String | Not currently in use |
| parentV6ip | String | Not currently in use |
| parentMac | String | Not currently in use |
| selector | []String | Standard Kubernetes selector match information |
| attachSubnets | []String | This field is deprecated and no longer used |

#### VipStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []VipCondition | Vip status change information, refer to the beginning of the documentation for the definition of Condition |
| ready | Bool | Vip is ready or not |
| v4ip | String | Vip IPv4 ip address, should be the same as the spec field |
| v6ip | String | Vip IPv6 ip address, should be the same as the spec field |
| mac | String | The vip mac address, which should be the same as the spec field |
| pv4ip | String | Not currently used |
| pv6ip | String | Not currently used |
| pmac | String | Not currently used |

### OvnEip

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnEip` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnEipSpec | OvnEip specific configuration information for default vpc |
| status | OvnEipStatus | OvnEip status information for default vpc |

#### OvnEipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| externalSubnet | String | OvnEip's subnet name |
| v4Ip | String | OvnEip IPv4 address |
| v6Ip | String | OvnEip IPv6 address |
| macAddress | String | OvnEip Mac address |
| type | String | OvnEip use type, the value can be `lrp`, `lsp` or `nat` |

#### OvnEipStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []OvnEipCondition | OvnEip status change information, refer to the beginning of the documentation for the definition of Condition |
| type | String | OvnEip use type, the value can be `lrp`, `lsp` or `nat` |
| nat | String | dnat snat fip |
| v4Ip | String | The IPv4 ip address used by ovnEip |
| v6Ip | String | The IPv4 ip address used by ovnEip |
| macAddress | String | Mac address used by ovnEip |

### OvnFip

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnFip` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnFipSpec | OvnFip specific configuration information in default vpc |
| status | OvnFipStatus | OvnFip status information in default vpc |

#### OvnFipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ovnEip | String | Name of the bound ovnEip |
| ipType | String | vip crd or ip crd ("" means ip crd) |
| ipName | String | The IP crd name corresponding to the bound Pod |
| vpc | String | The vpc crd name corresponding to the bound Pod |
| V4Ip | String | The IPv4 ip addresss corresponding to vip or the bound Pod |

#### OvnFipStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | OvnFip is ready or not |
| v4Eip | String | Name of the ovnEip to which ovnFip is bound |
| v4Ip | String | The ovnEip address currently in use |
| vpc | String | The name of the vpc where ovnFip is located |
| conditions | []OvnFipCondition | OvnFip status change information, refer to the beginning of the document for the definition of Condition |

### OvnSnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnSnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnSnatRuleSpec | OvnSnatRule specific configuration information in default vpc |
| status | OvnSnatRuleStatus | OvnSnatRule status information in default vpc |

#### OvnSnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ovnEip | String | Name of the ovnEip to which ovnSnatRule is bound |
| vpcSubnet | String | The name of the subnet of the vpc configured by ovnSnatRule |
| vpc | String | The vpc crd name corresponding to the ovnSnatRule bound Pod |
| ipName | String | The IP crd name corresponding to the ovnSnatRule bound Pod |
| v4IpCidr | String | The IPv4 cidr of the vpc subnet |

#### OvnSnatRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | OvnSnatRule is ready or not |
| v4Eip | String | The ovnEip address to which ovnSnatRule is bound |
| v4IpCidr | String | The cidr address used to configure snat in the logical-router |
| vpc | String | The name of the vpc where ovnSnatRule is located |
| conditions | []OvnSnatRuleCondition | OvnSnatRule status change information, refer to the beginning of the document for the definition of Condition |
