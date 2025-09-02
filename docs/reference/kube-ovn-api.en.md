# Kube-OVN API Reference

Based on the latest version of Kube-OVN, we have compiled a list of CRD resources supported by Kube-OVN, listing the types and meanings of each field of CRD definition for reference.

## Generic Condition Definition

| Property Name | Type | Description |
| --- | --- | --- |
| type | String | Type of status |
| status | String | The value of status, in the range of `True`, `False` or `Unknown` |
| reason | String | The reason for the status change |
| message | String | The specific message of the status change |
| observedGeneration | Int64 | The observed generation of the resource |
| lastUpdateTime | Time | The last time the status was updated |
| lastTransitionTime | Time | Time of last status type change |

In each CRD definition, the Condition field in Status follows the above format, so we explain it in advance.

## Core Network Resources

### Subnet Definition

#### Subnet

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Subnet` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | SubnetSpec | Subnet specific configuration information |
| status | SubnetStatus | Subnet status information |

##### SubnetSpec

| Property Name | Type | Description |
| --- | --- | --- |
| default | Bool | Whether this subnet is the default subnet |
| vpc | String | The vpc which the subnet belongs to, default is ovn-cluster |
| protocol | String | IP protocol, the value is in the range of `IPv4`, `IPv6` or `Dual` |
| namespaces | []String | The list of namespaces bound to this subnet |
| cidrBlock | String | The range of the subnet, e.g. 10.16.0.0/16 |
| gateway | String | The gateway address of the subnet, the default value is the first available address under the CIDRBlock of the subnet |
| excludeIps | []String | The range of addresses under this subnet that will not be automatically assigned |
| provider | String | Default value is `OVN`. In the case of multiple NICs, the value is `<name>.<namespace>` of the NetworkAttachmentDefinition, Kube-OVN will use this information to find the corresponding subnet resource |
| gatewayType | String | The gateway type in overlay mode, either `distributed` or `centralized` |
| gatewayNode | String | The gateway node when the gateway mode is centralized, node names can be comma-separated |
| natOutgoing | Bool | Whether the outgoing traffic is NAT |
| externalEgressGateway | String | The address of the external gateway. This parameter and the natOutgoing parameter cannot be set at the same time |
| policyRoutingPriority | Uint32 | Policy route priority. Used to control the forwarding of traffic to the external gateway address after the subnet gateway |
| policyRoutingTableID | Uint32 | The TableID of the local policy routing table, should be different for each subnet to avoid conflicts |
| mtu | Uint32 | The MTU size of the subnet |
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
| allowEWTraffic | Bool | Whether to allow east-west traffic |
| natOutgoingPolicyRules | []NatOutgoingPolicyRule | NAT outgoing policy rules |
| u2oInterconnectionIP | String | The IP address used for Underlay/Overlay interconnection |
| u2oInterconnection | Bool | Whether to enable interconnection mode for Overlay/Underlay |
| enableLb | *Bool | Whether the logical-switch of the subnet is associated with load-balancer records |
| enableEcmp | Bool | Centralized subnet, whether to enable ECMP routing |
| enableMulticastSnoop | Bool | Whether to enable multicast snooping |
| enableExternalLBAddress | Bool | Whether to enable external load balancer addresses |
| routeTable | String | Route table name |
| namespaceSelectors | []LabelSelector | Namespace selectors |

###### Acl

| Property Name | Type | Description |
| --- | --- | --- |
| direction | String | Restrict the direction of acl, which value is `from-lport` or `to-lport` |
| priority | Int | Acl priority, in the range 0 to 32767 |
| match | String | Acl rule match expression |
| action | String | The action of the rule, which value is in the range of `allow-related`, `allow-stateless`, `allow`, `drop`, `reject` |

###### NatOutgoingPolicyRule

| Property Name | Type | Description |
| --- | --- | --- |
| match | NatOutGoingPolicyMatch | Match conditions |
| action | String | Action |

###### NatOutGoingPolicyMatch

| Property Name | Type | Description |
| --- | --- | --- |
| srcIPs | String | Source IP address range |
| dstIPs | String | Destination IP address range |

##### SubnetStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []SubnetCondition | Subnet status change information, refer to the beginning of the document for the definition of Condition |
| v4availableIPs | Float64 | Number of available IPv4 IPs |
| v4availableIPrange | String | The available range of IPv4 addresses on the subnet |
| v4usingIPs | Float64 | Number of used IPv4 IPs |
| v4usingIPrange | String | Used IPv4 address ranges on the subnet |
| v6availableIPs | Float64 | Number of available IPv6 IPs |
| v6availableIPrange | String | The available range of IPv6 addresses on the subnet |
| v6usingIPs | Float64 | Number of used IPv6 IPs |
| v6usingIPrange | String | Used IPv6 address ranges on the subnet |
| activateGateway | String | The currently working gateway node in centralized subnet of master-backup mode |
| dhcpV4OptionsUUID | String | The DHCP_Options record identifier associated with the lsp dhcpv4_options on the subnet |
| dhcpV6OptionsUUID | String | The DHCP_Options record identifier associated with the lsp dhcpv6_options on the subnet |
| u2oInterconnectionIP | String | The IP address used for interconnection when Overlay/Underlay interconnection mode is enabled |
| u2oInterconnectionMAC | String | The MAC address used for interconnection when Overlay/Underlay interconnection mode is enabled |
| u2oInterconnectionVPC | String | The associated VPC when Overlay/Underlay interconnection mode is enabled |
| natOutgoingPolicyRules | []NatOutgoingPolicyRuleStatus | NAT outgoing policy rules status |
| mcastQuerierIP | String | The IP address of the multicast querier |
| mcastQuerierMAC | String | The MAC address of the multicast querier |

### IP Definition

#### IP

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources are kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource have the value `IP` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IPSpec | IP specific configuration information |

##### IPSpec

| Property Name | Type | Description |
| --- | --- | --- |
| podName | String | Pod name which assigned with this IP |
| namespace | String | The name of the namespace where the pod is bound |
| subnet | String | The subnet which the ip belongs to |
| attachSubnets | []String | The name of the other subnets attached to this primary IP (field deprecated) |
| nodeName | String | The name of the node where the pod is bound |
| ipAddress | String | IP address, in `v4IP,v6IP` format for dual-stack cases |
| v4IpAddress | String | IPv4 IP address |
| v6IpAddress | String | IPv6 IP address |
| attachIps | []String | Other IP addresses attached to this primary IP (field is deprecated) |
| macAddress | String | The MAC address of the bound pod |
| attachMacs | []String | Other MAC addresses attached to this primary IP (field deprecated) |
| containerID | String | The Container ID corresponding to the bound pod |
| podType | String | Special workload pod, can be `StatefulSet`, `VirtualMachine` or empty |

### Vpc Definition

#### Vpc

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Vpc` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcSpec | Vpc specific configuration information |
| status | VpcStatus | Vpc status information |

##### VpcSpec

| Property Name | Type | Description |
| --- | --- | --- |
| defaultSubnet | String | Default subnet name |
| namespaces | []String | List of namespaces bound by Vpc |
| staticRoutes | []StaticRoute | Static route configuration |
| policyRoutes | []PolicyRoute | Policy route configuration |
| vpcPeerings | []VpcPeering | VPC peering configuration |
| enableExternal | Bool | Whether to enable external connection |
| extraExternalSubnets | []String | Extra external subnets |
| enableBfd | Bool | Whether to enable BFD (Bidirectional Forwarding Detection) |
| bfdPort | BFDPort | BFD port configuration |

###### StaticRoute

| Property Name | Type | Description |
| --- | --- | --- |
| policy | String | Route policy |
| cidr | String | Destination CIDR |
| nextHopIP | String | Next hop IP address |
| ecmpMode | String | ECMP mode |
| bfdId | String | BFD ID |
| routeTable | String | Route table name |

###### PolicyRoute

| Property Name | Type | Description |
| --- | --- | --- |
| priority | Int | Policy route priority |
| match | String | Match conditions |
| action | String | Action, can be `allow`, `drop`, `reroute` |
| nextHopIP | String | Next hop IP address for rerouting (required only when action is reroute) |

###### VpcPeering

| Property Name | Type | Description |
| --- | --- | --- |
| remoteVpc | String | Remote VPC name |
| localConnectIP | String | Local connection IP address |

###### BFDPort

| Property Name | Type | Description |
| --- | --- | --- |
| enabled | Bool | Whether BFD is enabled |
| ip | String | IP address of the BFD port |
| nodeSelector | LabelSelector | Node selector for selecting nodes to host the BFD LRP |

##### VpcStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []VpcCondition | Vpc status change information, refer to the beginning of the document for the definition of Condition |
| standby | Bool | Whether this is a standby VPC |
| default | Bool | Whether this is the default VPC |
| defaultLogicalSwitch | String | Default logical switch name |
| router | String | Associated router name |
| tcpLoadBalancer | String | TCP load balancer name |
| udpLoadBalancer | String | UDP load balancer name |
| sctpLoadBalancer | String | SCTP load balancer name |
| tcpSessionLoadBalancer | String | TCP session load balancer name |
| udpSessionLoadBalancer | String | UDP session load balancer name |
| sctpSessionLoadBalancer | String | SCTP session load balancer name |
| subnets | []String | List of subnets under the VPC |
| vpcPeerings | []String | List of VPC peerings |
| enableExternal | Bool | Whether external connection is enabled |
| extraExternalSubnets | []String | Extra external subnets |
| enableBfd | Bool | Whether BFD is enabled |

## Underlay Network Configuration

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
| conflict | Bool | Whether there is a conflict |
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
| nodeSelector | LabelSelector | Select nodes for creating OVS bridges based on node labels, supports matchLabels and matchExpressions (once nodeSelector is used, excludeNodes will no longer take effect) |
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

## Security Configuration

### SecurityGroup

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `SecurityGroup` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | SecurityGroupSpec | SecurityGroup specific configuration information |
| status | SecurityGroupStatus | SecurityGroup status information |

#### SecurityGroupSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ingressRules | []SecurityGroupRule | Ingress security group rules |
| egressRules | []SecurityGroupRule | Egress security group rules |
| allowSameGroupTraffic | Bool | Whether to allow traffic within the same security group |

##### SecurityGroupRule

| Property Name | Type | Description |
| --- | --- | --- |
| ipVersion | String | IP version, can be `ipv4` or `ipv6` |
| protocol | SgProtocol | Protocol type, can be `all`, `icmp`, `tcp` or `udp` |
| priority | Int | Rule priority, range 1-200, smaller value means higher priority |
| remoteType | SgRemoteType | Remote type, can be `address` or `securityGroup` |
| remoteAddress | String | Remote address |
| remoteSecurityGroup | String | Remote security group name |
| portRangeMin | Int | Port range minimum value, minimum value is 1 |
| portRangeMax | Int | Port range maximum value, maximum value is 65535 |
| policy | SgPolicy | Policy action, can be `allow` or `drop` |

#### SecurityGroupStatus

| Property Name | Type | Description |
| --- | --- | --- |
| portGroup | String | Associated port group |
| allowSameGroupTraffic | Bool | Whether traffic within the same security group is allowed |
| ingressMd5 | String | MD5 value of ingress rules |
| egressMd5 | String | MD5 value of egress rules |
| ingressLastSyncSuccess | Bool | Whether the last sync of ingress rules was successful |
| egressLastSyncSuccess | Bool | Whether the last sync of egress rules was successful |

## Load Balancing and Virtual IP

### Vip

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `Vip` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VipSpec | Vip specific configuration information |
| status | VipStatus | Vip status information |

#### VipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| namespace | String | The namespace to which the VIP belongs |
| subnet | String | The subnet to which the VIP belongs |
| type | String | VIP type |
| v4ip | String | IPv4 address |
| v6ip | String | IPv6 address |
| macAddress | String | MAC address |
| selector | []String | Selector |
| attachSubnets | []String | List of attached subnets |

#### VipStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []VipCondition | VIP status change information, refer to the beginning of the document for the definition of Condition |
| type | String | VIP type |
| v4ip | String | IPv4 address |
| v6ip | String | IPv6 address |
| mac | String | MAC address |

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
| vip | String | Virtual IP address |
| namespace | String | Namespace |
| selector | []String | Backend selector |
| endpoints | []String | List of backend endpoints |
| sessionAffinity | String | Session affinity |
| ports | []SwitchLBRulePort | Port configuration |

##### SwitchLBRulePort

| Property Name | Type | Description |
| --- | --- | --- |
| name | String | Port name |
| port | Int32 | Port number |
| targetPort | Int32 | Target port number |
| protocol | String | Protocol type |

#### SwitchLBRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| conditions | []SwitchLBRuleCondition | SwitchLBRule status change information, refer to the beginning of the document for the definition of Condition |
| ports | String | SwitchLBRule port information |
| service | String | SwitchLBRule service name |

## QoS and IP Pool Management

### QoSPolicy

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `QoSPolicy` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | QoSPolicySpec | QoSPolicy specific configuration information |

#### QoSPolicySpec

| Property Name | Type | Description |
| --- | --- | --- |
| bandwidthLimitRules | QoSPolicyBandwidthLimitRules | Bandwidth limit rules |
| shared | Bool | Whether it is a shared policy |
| bindingType | QoSPolicyBindingType | Binding type |

### IPPool

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `IPPool` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IPPoolSpec | IPPool specific configuration information |
| status | IPPoolStatus | IPPool status information |

#### IPPoolSpec

| Property Name | Type | Description |
| --- | --- | --- |
| subnet | String | Subnet |
| namespaces | []String | List of bound namespaces |
| ips | []String | List of IP addresses |

#### IPPoolStatus

| Property Name | Type | Description |
| --- | --- | --- |
| v4AvailableIPs | BigInt | Number of available IPv4 addresses |
| v4AvailableIPRange | String | Available IPv4 address range |
| v4UsingIPs | BigInt | Number of used IPv4 addresses |
| v4UsingIPRange | String | Used IPv4 address range |
| v6AvailableIPs | BigInt | Number of available IPv6 addresses |
| v6AvailableIPRange | String | Available IPv6 address range |
| v6UsingIPs | BigInt | Number of used IPv6 addresses |
| v6UsingIPRange | String | Used IPv6 address range |
| conditions | []IPPoolCondition | IP pool status change information, refer to the beginning of the document for the definition of Condition |

## NAT and Elastic IP Management

### IptablesEIP

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `IptablesEIP` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesEIPSpec | IptablesEIP specific configuration information |
| status | IptablesEIPStatus | IptablesEIP status information |

#### IptablesEIPSpec

| Property Name | Type | Description |
| --- | --- | --- |
| v4ip | String | IPv4 address |
| v6ip | String | IPv6 address |
| macAddress | String | MAC address |
| natGwDp | String | NAT gateway data path |
| qosPolicy | String | QoS policy |
| externalSubnet | String | External subnet |

#### IptablesEIPStatus

| Property Name | Type | Description |
| --- | --- | --- |
| ready | Bool | Whether IptablesEIP is configured successfully |
| ip | String | IP address used by IptablesEIP, currently only supports IPv4 address |
| redo | String | IptablesEIP CRD creation or update time |
| nat | String | IptablesEIP usage type, can be `fip`, `snat` or `dnat` |
| qosPolicy | String | QoS policy name |
| conditions | []IptablesEIPCondition | IptablesEIP status change information, refer to the beginning of the document for the definition of Condition |

### OvnEip

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnEip` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnEipSpec | OvnEip specific configuration information |
| status | OvnEipStatus | OvnEip status information |

#### OvnEipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| externalSubnet | String | External subnet |
| v4Ip | String | IPv4 address |
| v6Ip | String | IPv6 address |
| macAddress | String | MAC address |
| type | String | Type, can be lrp, lsp or nat |

### IptablesFIPRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `IptablesFIPRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesFIPRuleSpec | IptablesFIPRule specific configuration information |

#### IptablesFIPRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| eip | String | Elastic IP address |
| internalIP | String | Internal IP address |

### OvnFip

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnFip` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnFipSpec | OvnFip specific configuration information |
| status | OvnFipStatus | OvnFip status information |

#### OvnFipSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ovnEip | String | Associated OVN EIP |
| ipType | String | IP type, can be vip or ip |
| ipName | String | IP name |
| vpc | String | VPC |
| v4Ip | String | IPv4 address |
| v6Ip | String | IPv6 address |
| type | String | Type, can be distributed or centralized |

### IptablesDnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `IptablesDnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesDnatRuleSpec | IptablesDnatRule specific configuration information |

#### IptablesDnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| eip | String | Elastic IP address |
| externalPort | String | External port |
| protocol | String | Protocol type |
| internalIP | String | Internal IP address |
| internalPort | String | Internal port |

### OvnDnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnDnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnDnatRuleSpec | OvnDnatRule specific configuration information |
| status | OvnDnatRuleStatus | OvnDnatRule status information |

#### OvnDnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ovnEip | String | Associated OVN EIP |
| ipType | String | IP type, can be vip or ip |
| ipName | String | IP name |
| internalPort | String | Internal port |
| externalPort | String | External port |
| protocol | String | Protocol type |
| vpc | String | VPC |
| v4Ip | String | IPv4 address |
| v6Ip | String | IPv6 address |

#### OvnDnatRuleStatus

| Property Name | Type | Description |
| --- | --- | --- |
| vpc | String | VPC |
| v4Eip | String | IPv4 EIP address |
| v6Eip | String | IPv6 EIP address |
| externalPort | String | External port |
| v4Ip | String | IPv4 address |
| v6Ip | String | IPv6 address |
| internalPort | String | Internal port |
| protocol | String | Protocol type |
| ipName | String | IP name |
| ready | Bool | Whether DNAT rule is configured successfully |
| conditions | []OvnDnatRuleCondition | OVN DNAT rule status change information, refer to the beginning of the document for the definition of Condition |

### IptablesSnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `IptablesSnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | IptablesSnatRuleSpec | IptablesSnatRule specific configuration information |

#### IptablesSnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| eip | String | Elastic IP address |
| internalCIDR | String | Internal CIDR range |

### OvnSnatRule

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `OvnSnatRule` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | OvnSnatRuleSpec | OvnSnatRule specific configuration information |
| status | OvnSnatRuleStatus | OvnSnatRule status information |

#### OvnSnatRuleSpec

| Property Name | Type | Description |
| --- | --- | --- |
| ovnEip | String | Associated OVN EIP |
| vpcSubnet | String | VPC subnet |
| ipName | String | IP name |
| vpc | String | VPC |
| v4IpCidr | String | IPv4 CIDR range |
| v6IpCidr | String | IPv6 CIDR range |

## VPC Advanced Features

### VpcNatGateway

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `VpcNatGateway` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcNatGatewaySpec | VpcNatGateway specific configuration information |
| status | VpcNatGatewayStatus | VpcNatGateway status information |

#### VpcNatGatewaySpec

| Property Name | Type | Description |
| --- | --- | --- |
| vpc | String | VPC name where the VPC gateway Pod is located |
| subnet | String | Subnet name where the VPC gateway Pod belongs |
| externalSubnets | []String | List of external subnets |
| lanIp | String | Specified IP address allocated for the VPC gateway Pod |
| selector | []String | Standard Kubernetes Selector matching information |
| tolerations | []Toleration | Standard Kubernetes toleration information |
| affinity | Affinity | Standard Kubernetes affinity configuration |
| qosPolicy | String | QoS policy name |
| bgpSpeaker | VpcBgpSpeaker | BGP speaker configuration |
| routes | []Route | Route configuration list |

##### VpcBgpSpeaker

| Property Name | Type | Description |
| --- | --- | --- |
| enabled | Bool | Whether to enable BGP speaker |
| asn | Uint32 | Local autonomous system number |
| remoteAsn | Uint32 | Remote autonomous system number |
| neighbors | []String | BGP neighbor list |
| holdTime | Duration | BGP hold time |
| routerId | String | BGP router ID |
| password | String | BGP authentication password |
| enableGracefulRestart | Bool | Whether to enable graceful restart |
| extraArgs | []String | Additional arguments list |

##### Route

| Property Name | Type | Description |
| --- | --- | --- |
| cidr | String | Route destination CIDR |
| nextHopIP | String | Next hop IP address |

#### VpcNatGatewayStatus

| Property Name | Type | Description |
| --- | --- | --- |
| qosPolicy | String | QoS policy name |
| externalSubnets | []String | List of external subnets |
| selector | []String | Standard Kubernetes Selector matching information |
| tolerations | []Toleration | Standard Kubernetes toleration information |
| affinity | Affinity | Standard Kubernetes affinity configuration |

### VpcEgressGateway

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `VpcEgressGateway` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcEgressGatewaySpec | VpcEgressGateway specific configuration information |
| status | VpcEgressGatewayStatus | VpcEgressGateway status information |

#### VpcEgressGatewaySpec

| Property Name | Type | Description |
| --- | --- | --- |
| vpc | String | VPC |
| replicas | Int32 | Number of replicas |
| prefix | String | Name prefix |
| image | String | Container image |
| internalSubnet | String | Internal subnet |
| externalSubnet | String | External subnet |
| internalIPs | []String | List of internal IPs |
| externalIPs | []String | List of external IPs |
| trafficPolicy | String | Traffic policy |

### VpcDns

| Property Name | Type | Description |
| --- | --- | --- |
| apiVersion | String | Standard Kubernetes version information field, all custom resources have this value as kubeovn.io/v1 |
| kind | String | Standard Kubernetes resource type field, all instances of this resource will have the value `VpcDns` |
| metadata | ObjectMeta | Standard Kubernetes resource metadata information |
| spec | VpcDNSSpec | VpcDns specific configuration information |
| status | VpcDNSStatus | VpcDns status information |

#### VpcDNSSpec

| Property Name | Type | Description |
| --- | --- | --- |
| replicas | Int32 | Number of replicas |
| vpc | String | VPC |
| subnet | String | Subnet |
