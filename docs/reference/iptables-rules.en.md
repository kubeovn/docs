# Iptables Rules

Kube-OVN uses `ipset` and `iptables` to implement gateway NAT functionality in the default VPC overlay Subnets.

The ipset used is shown in the following table:

| Name（IPv4/IPv6）                                         | Type     | Usage                                             |
|:--------------------------------------------------------|:---------|:--------------------------------------------------|
| ovn40services/ovn60services                             | hash:net | Service CIDR                                      |
| ovn40subnets/ovn60subnets                               | hash:net | Overlay Subnet CIDR and NodeLocal DNS IP address  |
| ovn40subnets-nat/ovn60subnets-nat                       | hash:net | Overlay Subnet CIDRs that enable `NatOutgoing`    |
| ovn40subnets-distributed-gw/ovn60subnets-distributed-gw | hash:net | Overlay Subnet CIDRs that use distributed gateway |
| ovn40other-node/ovn60other-node                         | hash:net | Internal IP addresses for other Nodes             |
| ovn40local-pod-ip-nat/ovn60local-pod-ip-nat             | hash:ip  | Deprecated                                        |


The iptables rules (IPv4) used are shown in the following table:

| Table  | Chain           | Rule                                                                                                                    | Usage                                                                                                                                                     | Note                                                                                      |
|:-------|:----------------|:------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------|
| filter | INPUT           | -m set --match-set ovn40services src -j ACCEPT                                                                          | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | INPUT           | -m set --match-set ovn40services dst -j ACCEPT                                                                          | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | INPUT           | -m set --match-set ovn40subnets src -j ACCEPT                                                                           | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | INPUT           | -m set --match-set ovn40subnets dst -j ACCEPT                                                                           | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | FORWARD         | -m set --match-set ovn40services src -j ACCEPT                                                                          | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | FORWARD         | -m set --match-set ovn40services dst -j ACCEPT                                                                          | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | FORWARD         | -m set --match-set ovn40subnets src -j ACCEPT                                                                           | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | FORWARD         | -m set --match-set ovn40subnets dst -j ACCEPT                                                                           | Allow k8s service and pod traffic to pass through                                                                                                         | --                                                                                        |
| filter | OUTPUT          | -p udp -m udp --dport 6081 -j MARK --set-xmark 0x0                                                                      | Clear traffic tag to prevent SNAT                                                                                                                         | [UDP: bad checksum on VXLAN interface](https://github.com/flannel-io/flannel/issues/1279) |
| nat    | PREROUTING      | -m comment --comment "kube-ovn prerouting rules" -j OVN-PREROUTING                                                      | Enter OVN-PREROUTING chain processing                                                                                                                     | --                                                                                        |
| nat    | POSTROUTING     | -m comment --comment "kube-ovn postrouting rules" -j OVN-POSTROUTING                                                    | Enter OVN-POSTROUTING chain processing                                                                                                                    | --                                                                                        |
| nat    | OVN-PREROUTING  | -i ovn0 -m set --match-set ovn40subnets src -m set --match-set ovn40services dst -j MARK --set-xmark 0x4000/0x4000      | Adding masquerade tags to Pod access service traffic                                                                                                      | Used when the built-in LB is turned off                                                   |
| nat    | OVN-PREROUTING  | -p tcp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-TCP dst -j MARK --set-xmark 0x80000/0x80000 | Add specific tags to ExternalTrafficPolicy for Local's Service traffic (TCP)                                                                              | Only used when kube-proxy is using ipvs mode                                              |
| nat    | OVN-PREROUTING  | -p udp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-UDP dst -j MARK --set-xmark 0x80000/0x80000 | Add specific tags to ExternalTrafficPolicy for Local's Service traffic (UDP)                                                                              | Only used when kube-proxy is using ipvs mode                                              |
| nat    | OVN-POSTROUTING | -m mark --mark 0x4000/0x4000 -j MASQUERADE                                                                              | Perform SNAT for specific tagged traffic                                                                                                                  | --                                                                                        |
| nat    | OVN-POSTROUTING | -m set --match-set ovn40subnets src -m set --match-set ovn40subnets dst -j MASQUERADE                                   | Perform SNAT for Service traffic between Pods passing through the node                                                                                    | --                                                                                        |
| nat    | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -m set --match-set ovn40subnets-distributed-gw dst -j RETURN                             | For Service traffic where ExternalTrafficPolicy is Local, if the Endpoint uses a distributed gateway, SNAT is not required.                               | --                                                                                        |
| nat    | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -j MASQUERADE                                                                            | For Service traffic where ExternalTrafficPolicy is Local, if the Endpoint uses a centralized gateway, SNAT is required.                                   | --                                                                                        |
| nat    | OVN-POSTROUTING | -p tcp -m tcp --tcp-flags SYN NONE -m conntrack --ctstate NEW -j RETURN                                                 | No SNAT is performed when the Pod IP is exposed to the outside world                                                                                      | --                                                                                        |
| nat    | OVN-POSTROUTING | -s 10.16.0.0/16 -m set ! --match-set ovn40subnets dst -j SNAT --to-source 192.168.0.101                                 | When the Pod accesses the network outside the cluster, if the subnet is NatOutgoing and a centralized gateway with the specified IP is used, perform SNAT | 10.16.0.0/16 is the Subnet CIDR，192.168.0.101 is the specified IP of gateway node         |
| nat    | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat src -m set ! --match-set ovn40subnets dst -j MASQUERADE                             | When the Pod accesses the network outside the cluster, if NatOutgoing is enabled on the subnet, perform SNAT                                              | --                                                                                        |