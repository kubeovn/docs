# Annotation Usage

Kube-OVN uses a large number of Pod and Node Annotations for configuring functionality and transferring information. Users can refer to this document to understand the usage of each Annotation, to better troubleshooting and information retrieval.

> Note: Some Annotations may change as the code is adjusted.

## Pod Annotation

| Key                                    | Value                           | Description                                                                     |
| -------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------- |
| ovn.kubernetes.io/allocated            | `true` or `false`               | If the Pod primary interface has already been allocated an address              |
| ovn.kubernetes.io/routed               | `true` or `false`               | If the Pod primary interface has already been allocated a route                 |
| ovn.kubernetes.io/mac_address          | String                          | MAC address allocated to Pod primary interface，when creating a Pod, you can set a fixed MAC address by this Annotation |
| ovn.kubernetes.io/ip_address           | String                          | IP address allocated to Pod primary interface，when creating a Pod, you can set a fixed IP address by this Annotation |
| ovn.kubernetes.io/cidr                 | String                          | Subnet CIDR that the Pod primary interface belongs to                                                       |
| ovn.kubernetes.io/gateway              | String                          | Subnet Gateway address that the Pod primary interface belongs to                                               |
| ovn.kubernetes.io/ip_pool              | IP list, separated by comma     | Pod primary interface will choose address from this list, used for workload fix address                      |
| ovn.kubernetes.io/bgp                  | `true` or `false`               | Enable Pod address BGP advertisement址                                          |
| ovn.kubernetes.io/snat                 | String                          | SNAT address for accessing external address                                                 |
| ovn.kubernetes.io/eip                  | String                          | EIP address that Pod accesses external clusters and is accessed from external.                               |
| ovn.kubernetes.io/vip                  | String                          | VIP allocated to Pod primary interface           |
| ovn.kubernetes.io/virtualmachine       | String                          | The VirtualMachineInstance that the Pod primary interface belongs to                                          |
| ovn.kubernetes.io/logical_router       | String                          | The VPC that the Pod primary interface belongs to                                                            |
| ovn.kubernetes.io/layer2_forward       | `true` or `false`               | Enable add `unknown` address to Pod primary interface in OVN NorthboundDB LSP                                  |
| ovn.kubernetes.io/port_security        | `true` or `false`               | Enable Pod primary interface port security                                        |
| ovn.kubernetes.io/logical_switch       | String                          | The Subnet that the Pod primary interface belongs to                                                         |
| ovn.kubernetes.io/vlan_id              | Int                             | The VlanID that the Pod primary interface belongs to                                                |
| ovn.kubernetes.io/ingress_rate         | Int                             | Pod primary interface ingress rate limit, measured in Mbits/s                                          |
| ovn.kubernetes.io/egress_rate          | Int                             | Pod primary interface egress rate limit, measured in Mbits/s                                          |
| ovn.kubernetes.io/security_groups      | String list, separated by comma | The SecurityGroup that the Pod primary interface belongs to                                                 |
| ovn.kubernetes.io/allow_live_migration | `true` or `false`               | Allow live migration for Pod primary interface, used by KubeVirt                      |
| ovn.kubernetes.io/default_route        | `true` or `false`               | Set the default route to the Pod primary interface.                                                  |
| ovn.kubernetes.io/provider_network     | String                          | The ProviderNetwork that the Pod primary interface belongs to                                              |
| ovn.kubernetes.io/mirror               | `true` or `false`               | Enable Pod primary interface traffic mirror                                                        |
| ovn.kubernetes.io/latency              | Int                             | The delay injected to the Pod primary interface card, measured in milliseconds                                              |
| ovn.kubernetes.io/limit                | Int                             | Maximum number of packets that the qdisc queue of the primary interface of the Pod                                      |
| ovn.kubernetes.io/loss                 | Float                           | The probability of packet loss on the Pod primary interface                                                    |
| ovn.kubernetes.io/jitter               | Int                             | The jitter of packet latency on the Pod primary interface, measured in milliseconds                                                                          |

## Node Annotation

| Key                                | Value             | Description                                                                |
| ---------------------------------- | ----------------- | -------------------------------------------------------------------------- |
| ovn.kubernetes.io/allocated        | `true` or `false` | If the `ovn0` interface has already been allocated an address              |
| ovn.kubernetes.io/ip_address       | String            | IP address allocated to `ovn0` interface                                   |
| ovn.kubernetes.io/mac_address      | String            | MAC address allocated to `ovn0` interface                                  |
| ovn.kubernetes.io/cidr             | String            | Subnet CIDR that the node `ovn0` interface belongs to                      |
| ovn.kubernetes.io/gateway          | String            | Subnet gateway that the node `ovn0` interface belongs to                   |
| ovn.kubernetes.io/chassis          | String            | The Chassis ID in OVN-SouthBoundDB that the node belongs to                |
| ovn.kubernetes.io/port_name        | String            | The LSP name in OVN-NorthboundDB that the node `ovn0` interface belongs to |
| ovn.kubernetes.io/logical_switch   | String            | Subnet that the node `ovn0` interface belongs to                           |
| ovn.kubernetes.io/tunnel_interface | String            | Network interface used for tunnel encapsulation                            |

## Namespace Annotation

| Key                           | Value                                   | Description                                       |
| ----------------------------- | --------------------------------------- | ------------------------------------------------- |
| ovn.kubernetes.io/cidr        | CIDR list, separated by comma           | The CIDRs of subnets bound by this Namespace      |
| ovn.kubernetes.io/exclude_ips | excludeIPs list, separated by semicolon | The excludeIPs of subnets bound by this Namespace |

## Subnet Annotation

| Key                   | Value             | Description                             |
| --------------------- | ----------------- | --------------------------------------- |
| ovn.kubernetes.io/bgp | `true` or `false` | Enable Subnet address BGP advertisement |


## Service Annotation

| Key                             | Value             | Description                                               |
| ------------------------------- | ----------------- | --------------------------------------------------------- |
| ovn.kubernetes.io/bgp           | `true` or `false` | Enable Service address BGP advertisement                  |
| ovn.kubernetes.io/switch_lb_vip | String            | Additional VIP addresses assigned to Service in Kube-OVN. |
| ovn.kubernetes.io/vpc           | String            | The VPC that the Service belongs to                       |

## Networkpolicy Annotation

| Key                          | Value             | Description              |
| ---------------------------- | ----------------- | ------------------------ |
| ovn.kubernetes.io/enable_log | `true` or `false` | Enable NetworkPolicy log |