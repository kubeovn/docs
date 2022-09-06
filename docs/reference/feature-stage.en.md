# Feature Stage

In Kube-OVN, feature stage is classified into **Alpha**, **Beta** and **GA**, based on the degree of feature usage, documentation and test coverage.

## Definition of Stage

For **Alpha** stage functions:

- The feature is not fully documented and well tested.
- This feature may change or even be removed in the future.
- This feature API is not guaranteed to be stable and may be removed.
- Community provides low priority support for this feature and long-term support cannot be guaranteed.
- Since feature stability and long-term support cannot be guaranteed, it can be tested and verified, but is not recommended for production use.

For **Beta** stage functions:

- This feature is partially documented and tested, but complete coverage is not guaranteed.
- This feature may change in the future and the upgrade may affect the network, but it will not be removed as a whole.
- This feature API may change in the future and the fields may be adjusted, but not removed as a whole.
- This feature will be supported by the community in the long term.
- It can be used on non-critical services as the functionality will be supported for a long time, but it is not recommended for critical production service as there is a possibility of changes in functionality and APIs that may break the network.

For **GA** stage functions:

- The feature has full documentation and test coverage.
- The feature will remain stable and upgrades will be guaranteed to be smooth.
- This feature API is not subject to disruptive changes.
- This feature will be supported with high priority by the community and long-term support will be guaranteed.

## Feature Stage List

This list records the feature stages from the 1.8 release.

| Feature                                          | Default | Stage | Since | Until |
|--------------------------------------------------|---------|-------|-------|-------|
| Namespaced Subnet                                | true    | GA    | 1.8   |       |
| Distributed Gateway                              | true    | GA    | 1.8   |       |
| Active-backup Centralized Gateway                | true    | GA    | 1.8   |       |
| ECMP Centralized Gateway                         | false   | Beta  | 1.8   |       |
| Subnet ACL                                       | true    | Alpha | 1.9   |       |
| Subnet Isolation (Will be replaced by ACL later) | true    | Beta  | 1.8   |       |
| Underlay Subnet                                  | true    | GA    | 1.8   |       |
| Subnet QoS                                       | true    | Alpha | 1.9   |       |
| Multiple Pod Interface                           | true    | Beta  | 1.8   |       |
| Subnet DHCP                                      | false   | Alpha | 1.10  |       |
| Subnet with External Gateway                     | false   | Alpha | 1.8   |       |
| Cluster Inter-Connection with OVN-IC             | false   | Beta  | 1.8   |       |
| Cluster Inter-Connection with Submariner         | false   | Alpha | 1.9   |       |
| VIP Reservation                                  | true    | Alpha | 1.10  |       |
| Create Custom VPC                                | true    | Beta  | 1.8   |       |
| Custom VPC Floating IP/SNAT/DNAT                 | true    | Alpha | 1.10  |       |
| Custom VPC Static Route                          | true    | Alpha | 1.10  |       |
| Custom VPC Policy Route                          | true    | Alpha | 1.10  |       |
| Custom VPC Security Group                        | true    | Alpha | 1.10  |       |
| Container Bandwidth QoS                          | true    | GA    | 1.8   |       |
| linux-netem QoS                                  | true    | Alpha | 1.9   |       |
| Prometheus Integration                           | false   | GA    | 1.8   |       |
| Grafana Integration                              | false   | GA    | 1.8   |       |
| IPv4/v6 DualStack                                | false   | GA    | 1.8   |       |
| Default VPC EIP/SNAT                             | false   | Beta  | 1.8   |       |
| Traffic Mirroring                                | false   | GA    | 1.8   |       |
| NetworkPolicy                                    | true    | Beta  | 1.8   |       |
| Webhook                                          | false   | Alpha | 1.10  |       |
| Performance Tunning                              | false   | Beta  | 1.8   |       |
| Interconnection with Routes in Overlay Mode      | false   | Alpha | 1.8   |       |
| BGP Support                                      | false   | Alpha | 1.9   |       |
| Cilium Integration                               | false   | Alpha | 1.10  |       |
| Custom VPC Peering                               | false   | Alpha | 1.10  |       |
| Mellanox Offload                                 | false   | Alpha | 1.8   |       |
| Corigine Offload                                 | false   | Alpha | 1.10  |       |
| Windows Support                                  | false   | Alpha | 1.10  |       |
| DPDK Support                                     | false   | Alpha | 1.10  |       |
| OpenStack Integration                            | false   | Alpha | 1.9   |       |
| Single Pod Fixed IP/Mac                          | true    | GA    | 1.8   |       |
| Workload with Fixed IP                           | true    | GA    | 1.8   |       |
| StatefulSet with Fixed IP                        | true    | GA    | 1.8   |       |
| VM with Fixed IP                                 | false   | Beta  | 1.9   |       |
