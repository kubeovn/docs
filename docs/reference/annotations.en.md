# Annotation Usage

Kube-OVN uses a large number of Pod and Node Annotations for configuring functionality and transferring information. Users can refer to this document to understand the usage of each Annotation, for better troubleshooting and information retrieval.

> Note: Some Annotations may change as the code is adjusted.

## Pod Annotation

| Key | Value | Description |
| ---------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| ovn.kubernetes.io/allocated | `true` or `false` | If the Pod primary interface has already been allocated an address |
| ovn.kubernetes.io/routed | `true` or `false` | If the Pod primary interface has already been allocated a route |
| ovn.kubernetes.io/routes | String | Route information for Pod primary interface |
| ovn.kubernetes.io/mac_address | String | MAC address allocated to Pod primary interface, when creating a Pod, you can set a fixed MAC address by this Annotation |
| ovn.kubernetes.io/ip_address | String | IP address allocated to Pod primary interface, when creating a Pod, you can set a fixed IP address by this Annotation |
| ovn.kubernetes.io/ip_family | `ipv4` or `ipv6` | Select a single IP family for the Pod primary interface in a dual-stack subnet. If unset, dual-stack allocation is kept |
| \<nadName\>.\<nadNamespace\>.kubernetes.io/ip_address.\<interfaceName\> | String | Per-interface fixed IP when multiple interfaces attach to the same switch; interfaceName must match the attachment's interface in Multus. ovn.kubernetes.io/ip_address remains as fallback if unset |
| \<nadName\>.\<nadNamespace\>.kubernetes.io/mac_address.\<interfaceName\> | String | Per-interface fixed MAC when multiple interfaces attach to the same switch; interfaceName must match the attachment's interface in Multus |
| ovn.kubernetes.io/cidr | String | Subnet CIDR that the Pod primary interface belongs to |
| ovn.kubernetes.io/gateway | String | Subnet Gateway address that the Pod primary interface belongs to |
| ovn.kubernetes.io/ip_pool | IP list, separated by comma | Pod primary interface will choose address from this list, used for workload fix address |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | Enable Pod address BGP advertisement |
| ovn.kubernetes.io/snat | String | SNAT address for accessing external address |
| ovn.kubernetes.io/eip | String | EIP address that Pod accesses external clusters and is accessed from external. |
| ovn.kubernetes.io/vip | String | VIP allocated to Pod primary interface |
| ovn.kubernetes.io/aaps | String | AAPs (Additional Allowed Addresses Pairs) configuration for Pod primary interface |
| ovn.kubernetes.io/virtualmachine | String | The VirtualMachineInstance that the Pod primary interface belongs to |
| ovn.kubernetes.io/activation_strategy | String | Activation strategy for Pod primary interface |
| ovn.kubernetes.io/logical_router | String | The VPC that the Pod primary interface belongs to |
| ovn.kubernetes.io/layer2_forward | `true` or `false` | Enable add `unknown` address to Pod primary interface in OVN NorthboundDB LSP |
| ovn.kubernetes.io/port_security | `true` or `false` | Enable Pod primary interface port security |
| ovn.kubernetes.io/logical_switch | String | The Subnet that the Pod primary interface belongs to |
| ovn.kubernetes.io/vlan_id | Int | The VlanID that the Pod primary interface belongs to |
| ovn.kubernetes.io/ingress_rate | Int | Pod primary interface ingress rate limit, measured in Mbits/s |
| ovn.kubernetes.io/egress_rate | Int | Pod primary interface egress rate limit, measured in Mbits/s |
| ovn.kubernetes.io/security_groups | String list, separated by comma | The SecurityGroup that the Pod primary interface belongs to |
| ovn.kubernetes.io/default_route | `true` or `false` | Set the default route to the Pod primary interface. |
| ovn.kubernetes.io/provider_network | String | The ProviderNetwork that the Pod primary interface belongs to |
| ovn.kubernetes.io/mirror | `true` or `false` | Enable Pod primary interface traffic mirror |
| ovn.kubernetes.io/north_gateway | String | North gateway configuration for Pod primary interface |
| ovn.kubernetes.io/latency | Int | The delay injected to the Pod primary interface card, measured in milliseconds |
| ovn.kubernetes.io/limit | Int | Maximum number of packets that the qdisc queue of the primary interface of the Pod |
| ovn.kubernetes.io/loss | Float | The probability of packet loss on the Pod primary interface |
| ovn.kubernetes.io/jitter | Int | The jitter of packet latency on the Pod primary interface, measured in milliseconds |
| ovn.kubernetes.io/generate-hash | `true` or `false` | Whether to generate hash for Pod |
| ovn.kubernetes.io/attachmentprovider | String | Attachment provider for Pod |
| ovn.kubernetes.io/ingress_burst | Int | Ingress burst limit for the Pod primary interface |
| ovn.kubernetes.io/egress_burst | Int | Egress burst limit for the Pod primary interface |
| ovn.kubernetes.io/routed_subnet | `true` or `false` | Marks that the Pod subnet uses routed mode (/32 or /128 addresses with on-link gateway routes) |
| ovn.kubernetes.io/pod_nic_type | `standard`, `dpdk`, `vhost-user` | Pod primary interface NIC type |
| ovn.kubernetes.io/dhcp-v4-options | String | Pod-level DHCPv4 options UUID, overriding subnet-level DHCP settings |
| ovn.kubernetes.io/dhcp-v6-options | String | Pod-level DHCPv6 options UUID, overriding subnet-level DHCP settings |
| ovn.kubernetes.io/ip_reserved | `true` or `false` | Whether the allocated IP address is marked as reserved |
| ovn.kubernetes.io/port_vips | VIP list, separated by comma | List of additional virtual IP addresses bound to the Pod primary interface |
| ovn.kubernetes.io/vpc_nat_gw | String | Identifier for the VPC NAT Gateway Pod, written by the controller |
| ovn.kubernetes.io/vpc_nat_gw_init | `true` or `false` | Whether the in-Pod initialization of the VPC NAT Gateway has finished |
| ovn.kubernetes.io/vpc_nat_gw_init_instance | String | Records the container instance ID where initialization completed, re-triggering init if replaced |
| ovn.kubernetes.io/vpc_nat_gw_container_restarted | `true` or `false` | Whether the main container of the VPC NAT Gateway has been restarted, used to trigger rule re-application |
| ovn.kubernetes.io/vpc_nat_gw_activated | `true` or `false` | Whether the VPC NAT Gateway has been activated and is taking traffic |
| ovn.kubernetes.io/vpc_eips | String | MD5 hash of synchronized EIP list on the VPC NAT Gateway Pod, maintained by controller |
| ovn.kubernetes.io/vpc_floating_ips | String | MD5 hash of synchronized Floating IP list on the VPC NAT Gateway Pod, maintained by controller |
| ovn.kubernetes.io/vpc_dnat_md5 | String | MD5 hash of synchronized DNAT rules on the VPC NAT Gateway Pod, maintained by controller |
| ovn.kubernetes.io/vpc_snat_md5 | String | MD5 hash of synchronized SNAT rules on the VPC NAT Gateway Pod, maintained by controller |
| ovn.kubernetes.io/vpc_cidrs | String | List of internal CIDRs steered to the VPC NAT Gateway Pod |
| \<provider\>.kubernetes.io/ip_pool | IP list, separated by comma | IP pool for the specified provider in multi-NIC scenarios |
| \<provider\>.kubernetes.io/ip_family | `ipv4` or `ipv6` | Select a single IP family for the specified provider interface in a dual-stack subnet |
| \<provider\>.kubernetes.io/port_vips | VIP list, separated by comma | List of additional virtual IP addresses bound to the specified provider interface |
| \<provider\>.kubernetes.io/vpc_cidrs | String | List of internal CIDRs steered to the specified provider interface |
| \<provider\>.kubernetes.io/dhcp-v4-options | String | DHCPv4 options for the specified provider in multi-NIC scenarios |
| \<provider\>.kubernetes.io/dhcp-v6-options | String | DHCPv6 options for the specified provider in multi-NIC scenarios |
| \<provider\>.kubernetes.io/port_security | `true` or `false` | Port security toggle for the specified provider in multi-NIC scenarios |
| \<provider\>.kubernetes.io/ingress_rate | Int | Ingress rate limit for the specified provider interface, in Mbits/s |
| \<provider\>.kubernetes.io/egress_rate | Int | Egress rate limit for the specified provider interface, in Mbits/s |
| \<provider\>.kubernetes.io/ingress_burst | Int | Ingress burst limit for the specified provider interface |
| \<provider\>.kubernetes.io/egress_burst | Int | Egress burst limit for the specified provider interface |
| \<provider\>.kubernetes.io/routed_subnet | `true` or `false` | Marks that the specified provider interface uses routed subnet mode |
| \<provider\>.kubernetes.io/latency | Int | Packet latency delay injected to the specified provider interface, in milliseconds |
| \<provider\>.kubernetes.io/limit | Int | Maximum number of packets for the qdisc queue of the specified provider interface |
| \<provider\>.kubernetes.io/loss | Float | Packet loss probability for the specified provider interface |
| \<provider\>.kubernetes.io/jitter | Int | Packet jitter delay injected to the specified provider interface, in milliseconds |
| \<provider\>.kubernetes.io/vf_representor | String | Specified VF representor interface name in multi-NIC SR-IOV scenarios |
| \<provider\>.kubernetes.io/vf | String | Allocated VF physical device interface name in multi-NIC SR-IOV scenarios |

## Node Annotation

| Key | Value | Description |
| ---------------------------------- | ----------------- | -------------------------------------------------------------------------- |
| ovn.kubernetes.io/allocated | `true` or `false` | If the `ovn0` interface has already been allocated an address |
| ovn.kubernetes.io/ip_address | String | IP address allocated to `ovn0` interface |
| ovn.kubernetes.io/mac_address | String | MAC address allocated to `ovn0` interface |
| ovn.kubernetes.io/cidr | String | Subnet CIDR that the node `ovn0` interface belongs to |
| ovn.kubernetes.io/gateway | String | Subnet gateway that the node `ovn0` interface belongs to |
| ovn.kubernetes.io/chassis | String | The Chassis ID in OVN-SouthBoundDB that the node belongs to |
| ovn.kubernetes.io/port_name | String | The LSP name in OVN-NorthboundDB that the node `ovn0` interface belongs to |
| ovn.kubernetes.io/logical_switch | String | Subnet that the node `ovn0` interface belongs to |
| ovn.kubernetes.io/tunnel_interface | String | Network interface used for tunnel encapsulation |
| ovn.kubernetes.io/node_networks | String | List of NetworkAttachmentDefinitions on the node that provide attachment networks for Pods |
| ovn.kubernetes.io/ovs_dp_type | `kernel` or `userspace` | OVS datapath type on the node (`userspace` enables OVS-DPDK) |
| \<provider\>.provider-network.kubernetes.io/ready | `true` or `false` | Indicates whether the ProviderNetwork is successfully initialized and ready on the node |
| \<provider\>.provider-network.kubernetes.io/interface | String | Physical network interface mapped to the ProviderNetwork on the node |
| \<provider\>.provider-network.kubernetes.io/mtu | Int | MTU of the ProviderNetwork interface on the node |
| \<provider\>.provider-network.kubernetes.io/vlan_interfaces | String | List of VLAN sub-interfaces created or managed on the node for this ProviderNetwork |
| \<provider\>.provider-network.kubernetes.io/err_mesg | String | Error message encountered during ProviderNetwork initialization on the node |
| \<provider\>.provider-network.kubernetes.io/exclude | String | Network interfaces excluded from the ProviderNetwork on the node |

## Namespace Annotation

| Key | Value | Description |
| ----------------------------- | --------------------------------------- | ------------------------------------------------- |
| ovn.kubernetes.io/cidr | CIDR list, separated by comma | The CIDRs of subnets bound by this Namespace |
| ovn.kubernetes.io/exclude_ips | excludeIPs list, separated by semicolon | The excludeIPs of subnets bound by this Namespace |

## Subnet Annotation

| Key | Value | Description |
| ----------------------- | ---------------------------- | ----------------------------------------- |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | Enable Subnet address BGP advertisement |
| ovn.kubernetes.io/vpc | String | The VPC the Subnet belongs to (maintained by the controller; useful for filtering by VPC) |

## Service Annotation

| Key | Value | Description |
| -------------------------------------------- | ----------------- | --------------------------------------------------------- |
| ovn.kubernetes.io/service-cidr-hash | String | Records and validates the checksum hash of the cluster Service CIDR to prevent conflict |
| ovn.kubernetes.io/bgp | `true`, `cluster`, `local` | Enable Service address BGP advertisement (only ClusterIP Services are affected; values are consistent with Pod/Subnet) |
| ovn.kubernetes.io/switch_lb_vip | String | Additional VIP addresses assigned to Service in Kube-OVN. |
| ovn.kubernetes.io/vpc | String | The VPC that the Service belongs to |
| ovn.kubernetes.io/service_external_ip_from_subnet | `true` or `false` | Whether Service external IP is allocated from subnet |
| ovn.kubernetes.io/service_health_check | `true` or `false` | Whether Service health check is enabled |
| ovn.kubernetes.io/lb_svc_img | String | Load balancer service image |

## Networkpolicy Annotation

| Key | Value | Description |
| ---------------------------- | ----------------- | ------------------------ |
| ovn.kubernetes.io/enable_log | `true` or `false` | Enable NetworkPolicy log |
| ovn.kubernetes.io/log_acl_actions | One or more combinations of "allow,drop,pass" | Print ACL logs that match ACL action |
| ovn.kubernetes.io/acl_log_meter_rate | Int | Rate limit for NetworkPolicy log output, in logs per second |
| ovn.kubernetes.io/network_policy_enforcement | `standard` or `lax` | Enforcement mode for an individual NetworkPolicy, overriding the controller default |
| ovn.kubernetes.io/network_policy_for | String | The multi-NIC provider (in the form `<nadName>.<nadNamespace>.ovn`) that this NetworkPolicy applies to |
| ovn.kubernetes.io/policy-for | String | Target provider or NetworkAttachmentDefinition for multi-network Pods (official standard annotation) |

## VIP Annotation

| Key | Value | Description |
| ------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------ |
| ovn.kubernetes.io/vip-last-attach-subnets | String | List of subnets previously attached to this VIP, used for cleanup during detachment or release |
