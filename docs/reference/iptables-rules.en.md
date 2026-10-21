# Netfilter (Iptables / Nftables) Rules

Kube-OVN leverages the host Linux Netfilter mechanism to assist in implementing gateway NAT for container overlay networks in the default VPC, Kube-Proxy compatibility, and TProxy transparent proxying.

Kube-OVN supports two underlying backend implementations: **Iptables** (legacy compatibility) and **Nftables** (modern architecture). This can be configured via the startup parameter `--gateway-netfilter-mode=auto|iptables|nftables` (defaults to `auto`, which auto-detects and aligns with the local Kube-Proxy runtime mode).

## Iptables Rules

In Iptables backend mode, Kube-OVN uses `ipset` and `iptables` rules working in tandem.

### IPSet Definitions

The ipsets used are shown in the following table:

| Name (IPv4/IPv6) | Type | Usage |
| :------------------------------------------------------ | :------- | :------------------------------------------------ |
| ovn40services/ovn60services | hash:net | Service CIDR |
| ovn40subnets/ovn60subnets | hash:net | Overlay Subnet CIDR and NodeLocal DNS IP address |
| ovn40subnets-nat/ovn60subnets-nat | hash:net | Overlay Subnet CIDRs that enable `NatOutgoing` |
| ovn40subnets-distributed-gw/ovn60subnets-distributed-gw | hash:net | Overlay Subnet CIDRs that use distributed gateway |
| ovn40other-node/ovn60other-node | hash:net | Internal IP addresses for other Nodes |
| ovn40local-pod-ip-nat/ovn60local-pod-ip-nat | hash:ip | Deprecated |
| ovn40subnets-nat-policy | hash:net | All subnet CIDRs configured with natOutgoingPolicyRules |
| ovn40natpr-418e79269dc5-dst | hash:net | Destination IPs corresponding to the rule in natOutgoingPolicyRules |
| ovn40natpr-418e79269dc5-src | hash:net | Source IPs corresponding to the rule in natOutgoingPolicyRules |

### Iptables Rule Definitions

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
| filter | FORWARD | -s 10.16.0.0/16 -m comment --comment "ovn-subnet-gateway,ovn-default" | Used to count packets from the subnet to the external network | "10.16.0.0/16" is the subnet CIDR; "ovn-subnet-gateway" before the comma identifies the rule for packet counting; "ovn-default" after the comma is the subnet name |
| filter | FORWARD | -d 10.16.0.0/16 -m comment --comment "ovn-subnet-gateway,ovn-default" | Used to count packets from the external network accessing the subnet | Same as above |
| filter | OUTPUT | -p udp -m udp --dport 6081 -j MARK --set-xmark 0x0 | Clear traffic tag to prevent unexpected SNAT | [UDP: bad checksum on VXLAN interface](https://github.com/flannel-io/flannel/issues/1279){: target="_blank" } |
| nat | PREROUTING | -m comment --comment "kube-ovn prerouting rules" -j OVN-PREROUTING | Enter OVN-PREROUTING chain processing | -- |
| nat | POSTROUTING | -m comment --comment "kube-ovn postrouting rules" -j OVN-POSTROUTING | Enter OVN-POSTROUTING chain processing | -- |
| nat | OVN-PREROUTING | -i ovn0 -m set --match-set ovn40subnets src -m set --match-set ovn40services dst -j MARK --set-xmark 0x4000/0x4000 | Add masquerade mark to Pod-to-Service traffic | Used when the built-in LB is disabled |
| nat | OVN-PREROUTING | -p tcp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-TCP dst -j MARK --set-xmark 0x80000/0x80000 | Add specific marks to ExternalTrafficPolicy=Local Service traffic (TCP) | Only present when kube-proxy uses IPVS mode |
| nat | OVN-PREROUTING | -p udp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-UDP dst -j MARK --set-xmark 0x80000/0x80000 | Add specific marks to ExternalTrafficPolicy=Local Service traffic (UDP) | Same as above |
| nat | OVN-POSTROUTING | -m set --match-set ovn40services src -m set --match-set ovn40subnets dst -m mark --mark 0x4000/0x4000 -j SNAT --to-source <NODE_IP> | Keep node IP as source address when node accesses overlay Pods via Service IP | Only effective when kube-proxy uses IPVS mode |
| nat | OVN-POSTROUTING | -m mark --mark 0x4000/0x4000 -j MASQUERADE | Perform SNAT for specific tagged traffic | -- |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets src -m set --match-set ovn40subnets dst -j MASQUERADE | Perform SNAT for Service traffic between Pods passing through the node | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -m set --match-set ovn40subnets-distributed-gw dst -j RETURN | For Service traffic where ExternalTrafficPolicy is Local, if Endpoint uses distributed gateway, SNAT is not required | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -j MASQUERADE | For Service traffic where ExternalTrafficPolicy is Local, if Endpoint uses centralized gateway, SNAT is required | -- |
| nat | OVN-POSTROUTING | -p tcp -m tcp --tcp-flags SYN NONE -m conntrack --ctstate NEW -j RETURN | No SNAT is performed when Pod IP is exposed to the outside | -- |
| nat | OVN-POSTROUTING | -s 10.16.0.0/16 -m set ! --match-set ovn40subnets dst -j SNAT --to-source 192.168.0.101 | When Pod accesses external network, if subnet enables NatOutgoing and uses centralized gateway with specified IP, perform SNAT | 10.16.0.0/16 is the subnet CIDR, 192.168.0.101 is the specified gateway node IP |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat src -m set ! --match-set ovn40subnets dst -j MASQUERADE | When Pod accesses external network, if NatOutgoing is enabled on the subnet, perform SNAT | -- |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat-policy src -m set ! --match-set ovn40subnets dst -j OVN-NAT-POLICY | When Pod accesses external network, if natOutgoingPolicyRules is configured on the subnet, matching packets enter OVN-NAT-POLICY | Packets from subnets with natOutgoingPolicyRules enter OVN-NAT-POLICY chain |
| nat | OVN-POSTROUTING | -m mark --mark 0x90001/0x90001 -j MASQUERADE --random-fully | Packets emerging from OVN-NAT-POLICY tagged with 0x90001/0x90001 undergo SNAT | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x90002/0x90002 -j RETURN | Packets emerging from OVN-NAT-POLICY tagged with 0x90002/0x90002 bypass SNAT | -- |
| nat | OVN-NAT-POLICY | -s 10.0.11.0/24 -m comment --comment natPolicySubnet-net1 -j OVN-NAT-PSUBNET-aa98851157c5 | Packets matching subnet net1 jump to its corresponding rule chain | 10.0.11.0/24 represents the subnet CIDR; OVN-NAT-PSUBNET-aa98851157c5 corresponds to its natOutgoingPolicyRules |
| nat | OVN-NAT-PSUBNET-xxxxxxxxxxxx | -m set --match-set ovn40natpr-418e79269dc5-src src -m set --match-set ovn40natpr-418e79269dc5-dst dst -j MARK --set-xmark 0x90002/0x90002 | Matches rule ID in natOutgoingPolicyRules and marks packet with tag 0x90002 | 418e79269dc5 is the rule ID viewable via status.natOutgoingPolicyRules[index].RuleID |
| mangle | OVN-OUTPUT | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j MARK --set-xmark 0x90003/0x90003 | Mark kubelet probe traffic to redirect into TProxy | -- |
| mangle | OVN-PREROUTING | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j TPROXY --on-port 8102 --on-ip 172.18.0.3 --tproxy-mark 0x90004/0x90004 | Intercept and redirect marked probe traffic into local TProxy port | -- |

## Nftables Rules

In Nftables backend mode, Kube-OVN creates dedicated table namespaces in the kernel (`table ip kube-ovn` for IPv4 and `table ip6 kube-ovn` for IPv6). All sets, chains, and rules are managed atomically within the dedicated table, preventing contamination of host system tables.

### Native Set Definitions

In Nftables mode, legacy ipsets are mapped to native kernel sets:

| Set Name (IPv4 / IPv6) | Element Type | Usage and Stored Content |
| :--------------------- | :----------- | :----------------------- |
| subnets | `ipv4_addr` / `ipv6_addr` (interval) | Overlay Subnet CIDRs and NodeLocal DNS IP address |
| services | `ipv4_addr` / `ipv6_addr` (interval) | Service CIDRs |
| subnets-nat | `ipv4_addr` / `ipv6_addr` (interval) | Overlay Subnet CIDRs with `NatOutgoing` enabled |
| subnets-distributed-gw | `ipv4_addr` / `ipv6_addr` (interval) | Overlay Subnet CIDRs that use distributed gateway |
| other-node | `ipv4_addr` / `ipv6_addr` | Internal IP addresses of other Nodes |
| subnets-nat-policy | `ipv4_addr` / `ipv6_addr` (interval) | All Subnet CIDRs configured with natOutgoingPolicyRules |
| natpr-\<ruleID\>-src | `ipv4_addr` / `ipv6_addr` (interval) | Source IP ranges for rules in natOutgoingPolicyRules |
| natpr-\<ruleID\>-dst | `ipv4_addr` / `ipv6_addr` (interval) | Destination IP ranges for rules in natOutgoingPolicyRules |

### Native Counters

In Nftables mode, reliance on iptables comment string parsing is eliminated in favor of high-performance native named counters:

| Counter Name Format | Type | Usage |
| :------------------ | :--- | :---- |
| cnt-subnet-\<subnetName\>-in | counter | Counts inbound packets and bytes accessing the subnet from external networks |
| cnt-subnet-\<subnetName\>-out | counter | Counts outbound packets and bytes accessing external networks from the subnet |

### Nftables Core Chains and Rules (IPv4)

| Chain Name | Hook and Priority | Core Rule Expressions | Description |
| :--------- | :---------------- | :-------------------- | :---------- |
| input | `hook input priority filter` | `ip saddr @services accept`<br>`ip daddr @services accept`<br>`ip saddr @subnets accept`<br>`ip daddr @subnets accept` | Allow Kubernetes Service and Pod traffic through local INPUT |
| forward | `hook forward priority filter` | `ip saddr @services accept`<br>`ip daddr @services accept`<br>`ip saddr @subnets accept`<br>`ip daddr @subnets accept`<br>`ip saddr <CIDR> counter name <counter-out>`<br>`ip daddr <CIDR> counter name <counter-in>` | Forward cross-subnet traffic and invoke named counters for traffic accounting |
| output | `hook output priority filter` | `udp dport 6081 meta mark set 0x0` | Clear traffic tag on Geneve tunnel packets to avoid unexpected SNAT |
| prerouting | `hook prerouting priority nat` | `iifname "ovn0" ip saddr @subnets ip daddr @services meta mark set 0x4000/0x4000` | Mark Pod-to-Service traffic for masquerade when built-in LB is disabled |
| postrouting | `hook postrouting priority nat` | `ip saddr @services ip daddr @subnets meta mark 0x4000/0x4000 snat to <NODE_IP>`<br>`meta mark 0x4000/0x4000 masquerade`<br>`ip saddr @subnets ip daddr @subnets masquerade`<br>`ip saddr <CIDR> ip daddr != @subnets snat to <Gateway_IP>`<br>`ip saddr @subnets-nat ip daddr != @subnets masquerade`<br>`ip saddr @subnets-nat-policy ip daddr != @subnets jump nat-policy` | Perform egress masquerade, centralized fixed-IP SNAT, and policy-based NAT routing jumps |
| nat-policy | Custom jump chain | `ip saddr @natpr-<ruleID>-src ip daddr @natpr-<ruleID>-dst meta mark set 0x90001`<br>`ip saddr @natpr-<ruleID>-src ip daddr @natpr-<ruleID>-dst meta mark set 0x90002` | Match policy rules and mark traffic (0x90001 triggers SNAT, 0x90002 bypasses SNAT) |
