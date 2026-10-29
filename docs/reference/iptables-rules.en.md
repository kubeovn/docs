# Gateway Netfilter Rules

Kube-OVN uses a gateway Netfilter backend to implement gateway NAT functionality in the default VPC overlay Subnets.
The backend can use either `iptables` or `nftables`, while this page also retains the rule reference for the iptables backend.

## Gateway backend selection

The `kube-ovn-cni` daemon supports three gateway Netfilter modes:

| Mode | Behavior |
| :--- | :--- |
| `auto` | Detect the local kube-proxy mode. `iptables` and `ipvs` use the iptables backend; `nftables` uses the nftables backend. |
| `iptables` | Always use Kube-OVN's iptables and ipset rules. |
| `nftables` | Always use Kube-OVN's nftables table and rules. |

`auto` is the default. During a cold start it polls the kube-proxy `proxyMode` endpoint and, if that endpoint is unavailable before the detection timeout, reads the `kube-proxy` ConfigMap in `kube-system`. The default endpoint is `http://localhost:10249/proxyMode` and the default timeout is 30 seconds. At runtime, a mode change is accepted after three consecutive observations so a transient response does not switch the backend.

Set the mode and detection options in the environment before running `bash install.sh`, or in the `kube-ovn-cni` DaemonSet:

```bash
export GATEWAY_NETFILTER_MODE=auto
export KUBE_PROXY_MODE_ENDPOINT=http://localhost:10249/proxyMode
export GATEWAY_NETFILTER_DETECT_TIMEOUT=30s
```

```yaml
args:
- --gateway-netfilter-mode=auto
- --kube-proxy-mode-endpoint=http://localhost:10249/proxyMode
- --gateway-netfilter-detect-timeout=30s
```

For Helm installations, use the values for the chart in use:

```yaml
# charts/kube-ovn
networking:
  GATEWAY_NETFILTER_MODE: auto
  KUBE_PROXY_MODE_ENDPOINT: http://localhost:10249/proxyMode
  GATEWAY_NETFILTER_DETECT_TIMEOUT: 30s
```

```yaml
# charts/kube-ovn-v2
agent:
  gatewayNetfilterMode: auto
  kubeProxyModeEndpoint: http://localhost:10249/proxyMode
  gatewayNetfilterDetectTimeout: 30s
```

The nftables backend manages Kube-OVN-owned `kube-ovn` tables in the IPv4 and IPv6 nftables families, as applicable, for Service and NodePort NAT, subnet NAT, NAT policy, TProxy, filter and mangle rules, and subnet traffic accounting. It does not read or modify kube-proxy-private nftables objects or marks, and it does not flush conntrack entries.

When the backend changes, Kube-OVN prepares and reconciles the target backend before cleaning the old backend. Switching and uninstall cleanup remove only Kube-OVN-owned iptables, ipset, and nftables objects. If cleanup fails, the active backend is retained and cleanup is retried during later reconciliation.

## Nftable LoadBalancer Service

The controller flag `--enable-nftable-lb-svc` enables LoadBalancer Services backed by the VPC NAT gateway's nftable share-DNAT implementation. In current master this flag defaults to `true`, and it requires the global `--enable-lb=true` switch.

The corresponding Helm values are:

```yaml
# charts/kube-ovn
func:
  ENABLE_NFTABLE_LB_SVC: true

# charts/kube-ovn-v2
features:
  enableNftableLoadbalancerService: false
```

The v2 chart only renders the controller flag when `enableNftableLoadbalancerService` is true. When it is false, the flag is omitted and the controller default remains true; use the controller argument explicitly if an installation must opt out until the chart exposes an effective opt-out.

When an nftable LoadBalancer Service is terminating, its `EIP:port:protocol` identity is released immediately. A replacement Service can therefore reuse the identity and be programmed without waiting for the deleted Service's finalizers to disappear.

The ipset used is shown in the following table:

| Name(IPv4/IPv6) | Type | Usage |
| :------------------------------------------------------ | :------- | :------------------------------------------------ |
| ovn40services/ovn60services | hash:net | Service CIDR |
| ovn40subnets/ovn60subnets | hash:net | Overlay Subnet CIDR and NodeLocal DNS IP address |
| ovn40subnets-nat/ovn60subnets-nat | hash:net | Overlay Subnet CIDRs that enable `NatOutgoing` |
| ovn40subnets-distributed-gw/ovn60subnets-distributed-gw | hash:net | Overlay Subnet CIDRs that use distributed gateway |
| ovn40other-node/ovn60other-node | hash:net | Internal IP addresses for other Nodes |
| ovn40local-pod-ip-nat/ovn60local-pod-ip-nat | hash:ip | Deprecated |
| ovn40subnets-nat-policy | hash:net | All subnet cidrs configured with natOutgoingPolicyRules |
| ovn40natpr-418e79269dc5-dst | hash:net | The dstIPs corresponding to the rule in natOutgoingPolicyRules |
| ovn40natpr-418e79269dc5-src | hash:net | The srcIPs corresponding to the rule in natOutgoingPolicyRules |

The iptables rules (IPv4) used are shown in the following table:

| Table | Chain | Rule | Usage | Note |
| :----- | :-------------- | :---------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- |
| filter | INPUT | -m set --match-set ovn40services src -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | INPUT | -m set --match-set ovn40services dst -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | INPUT | -m set --match-set ovn40subnets src -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | INPUT | -m set --match-set ovn40subnets dst -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | FORWARD | -m set --match-set ovn40services src -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | FORWARD | -m set --match-set ovn40services dst -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | FORWARD | -m set --match-set ovn40subnets src -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | FORWARD | -m set --match-set ovn40subnets dst -j ACCEPT | Allow k8s service and pod traffic to pass through | -- |
| filter | FORWARD | -s 10.16.0.0/16 -m comment --comment "ovn-subnet-gateway,ovn-default" | Used to count packets from the subnet to the external network | "10.16.0.0/16" is the cidr of the subnet, the "ovn-subnet-gateway" before the "," in comment is used to identify the iptables rule used to count the subnet inbound and outbound gateway packets, and the "ovn-default" after the "," is the name of the subnet |
| filter | FORWARD | -d 10.16.0.0/16 -m comment --comment "ovn-subnet-gateway,ovn-default" | Used to count packets from the external network accessing the subnet | "10.16.0.0/16" is the cidr of the subnet, the "ovn-subnet-gateway" before the "," in comment is used to identify the iptables rule used to count the subnet inbound and outbound gateway packets, and the "ovn-default" after the "," is the name of the subnet |
| filter | OUTPUT | -p udp -m udp --dport 6081 -j MARK --set-xmark 0x0 | Clear traffic tag to prevent SNAT | [UDP: bad checksum on VXLAN interface](https://github.com/flannel-io/flannel/issues/1279) |
| nat | PREROUTING | -m comment --comment "kube-ovn prerouting rules" -j OVN-PREROUTING | Enter OVN-PREROUTING chain processing | -- |
| nat | POSTROUTING | -m comment --comment "kube-ovn postrouting rules" -j OVN-POSTROUTING | Enter OVN-POSTROUTING chain processing | -- |
| nat | OVN-PREROUTING | -i ovn0 -m set --match-set ovn40subnets src -m set --match-set ovn40services dst -j MARK --set-xmark 0x4000/0x4000 | Adding masquerade tags to Pod access service traffic | Used when the built-in LB is turned off |
| nat | OVN-PREROUTING | -p tcp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-TCP dst -j MARK --set-xmark 0x80000/0x80000 | Add specific tags to ExternalTrafficPolicy for Local's Service traffic (TCP) | Only used when kube-proxy is using ipvs mode |
| nat | OVN-PREROUTING | -p udp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-UDP dst -j MARK --set-xmark 0x80000/0x80000 | Add specific tags to ExternalTrafficPolicy for Local's Service traffic (UDP) | Only used when kube-proxy is using ipvs mode |
| nat | OVN-POSTROUTING | -m set --match-set ovn40services src -m set --match-set ovn40subnets dst -m mark --mark 0x4000/0x4000 -j SNAT --to-source <NODE_IP> | Use node IP as the source address for access from node to overlay Pods via service IP. | Works only when kube-proxy is using ipvs mode |
| nat | OVN-POSTROUTING | -m mark --mark 0x4000/0x4000 -j MASQUERADE | Perform SNAT for specific tagged traffic | -- |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets src -m set --match-set ovn40subnets dst -j MASQUERADE | Perform SNAT for Service traffic between Pods passing through the node | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -m set --match-set ovn40subnets-distributed-gw dst -j RETURN | For Service traffic where ExternalTrafficPolicy is Local, if the Endpoint uses a distributed gateway, SNAT is not required. | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -j MASQUERADE | For Service traffic where ExternalTrafficPolicy is Local, if the Endpoint uses a centralized gateway, SNAT is required. | -- |
| nat | OVN-POSTROUTING | -p tcp -m tcp --tcp-flags SYN NONE -m conntrack --ctstate NEW -j RETURN | No SNAT is performed when the Pod IP is exposed to the outside world | -- |
| nat | OVN-POSTROUTING | -s 10.16.0.0/16 -m set ! --match-set ovn40subnets dst -j SNAT --to-source 192.168.0.101 | When the Pod accesses the network outside the cluster, if the subnet is NatOutgoing and a centralized gateway with the specified IP is used, perform SNAT | 10.16.0.0/16 is the Subnet CIDR, 192.168.0.101 is the specified IP of gateway node |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat src -m set ! --match-set ovn40subnets dst -j MASQUERADE | When the Pod accesses the network outside the cluster, if NatOutgoing is enabled on the subnet, perform SNAT | -- |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat-policy src -m set ! --match-set ovn40subnets dst -j OVN-NAT-POLICY | When Pod accesses the network outside the cluster, if natOutgoingPolicyRules is enabled on the subnet, the packet with the specified policy will perform SNAT | ovn40subnets-nat-policy is all subnet segments configured with natOutgoingPolicyRules |
| nat | OVN-POSTROUTING | -m mark --mark 0x90001/0x90001 -j MASQUERADE --random-fully | When Pod accesses the network outside the cluster, if natOutgoingPolicyRules is enabled on the subnet, the packet with the specified policy will perform SNAT | After coming out of OVN-NAT-POLICY, if it is tagged with 0x90001/0x90001, it will do SNAT |
| nat | OVN-POSTROUTING | -m mark --mark 0x90002/0x90002 -j RETURN | When Pod accesses the network outside the cluster, if natOutgoingPolicyRules is enabled on the subnet, the packet with the specified policy will perform SNAT | After coming out of OVN-NAT-POLICY, if it is tagged with 0x90002/0x90002, it will not do SNAT |
| nat | OVN-NAT-POLICY | -s 10.0.11.0/24 -m comment --comment natPolicySubnet-net1 -j OVN-NAT-PSUBNET-aa98851157c5 | When Pod accesses the network outside the cluster, if natOutgoingPolicyRules is enabled on the subnet, the packet with the specified policy will perform SNAT | 10.0.11.0/24 represents the CIDR of the subnet net1, and the rules under the OVN-NAT-PSUBNET-aa98851157c5 chain correspond to the natOutgoingPolicyRules configuration of this subnet |
| nat | OVN-NAT-PSUBNET-xxxxxxxxxxxx | -m set --match-set ovn40natpr-418e79269dc5-src src -m set --match-set ovn40natpr-418e79269dc5-dst dst -j MARK --set-xmark 0x90002/0x90002 | When Pod accesses the network outside the cluster, if natOutgoingPolicyRules is enabled on the subnet, the packet with the specified policy will perform SNAT | 418e79269dc5 indicates the ID of a rule in natOutgoingPolicyRules, which can be viewed through status.natOutgoingPolicyRules[index].RuleID, indicating that srcIPs meets ovn40natpr-418e79269dc5-src, and dstIPS meets ovn40natpr-418e79269dc5- dst will be marked with tag 0x90002 |
| mangle | OVN-OUTPUT | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j MARK --set-xmark 0x90003/0x90003 | Introduce kubelet's detection traffic to tproxy with a specific mark | |
| mangle | OVN-PREROUTING | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j TPROXY --on-port 8102 --on-ip 172.18.0.3 --tproxy-mark 0x90004/0x90004 | Introduce kubelet's detection traffic to tproxy with a specific mark | |
