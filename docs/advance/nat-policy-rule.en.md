# NAT Policy Rule Function

## NAT Policy Rule Function Purpose

In the Overlay subnet under the default VPC, when the `natOutgoing` switch is turned on, all Pods in the subnet need to do SNAT to access the external network to the IP of the current node, but in some scenarios we do not want all Pods in the subnet to access the external network by SNAT.

So the NAT Policy Rule is to provide an interface for users to decide which CIDRs or IPs in the subnet to access the external network for SNAT.

## How to use NAT Policy Rules

Enable the `natOutgoing` switch in `subnet.Spec`, and add the field `natOutgoingPolicyRules` as follows:

```yaml
spec:
  natOutgoing: true
  natOutgoingPolicyRules:
    - action: forward
      match:
        srcIPs: 10.0.11.0/30,10.0.11.254
    - action: nat
      match:
        srcIPs: 10.0.11.128/26
        dstIPs: 114.114.114.114,8.8.8.8
```

The above case shows that there are two NAT policy rules:

1. Packets with source IP 10.0.11.0/30 or 10.0.11.254 will not perform SNAT when accessing the external network.
2. When a packet with source IP 10.0.11.128/26 and destination IP 114.114.114.114 or 8.8.8.8 accesses the external network, SNAT will be performed.

Field description:

Action: Indicates the action that will be executed for the message that meets the corresponding conditions of the "match". The action is divided into two types: `forward` and `nat`. SNAT.
When natOutgoingPolicyRules is not configured, packets are still SNAT by default.

match: Indicates the matching segment of the message, the matching segment includes srcIPs and dstIPs, here indicates the source IP and destination IP of the message from the subnet to the external network. `match.srcIPs` and `match.dstIPs` support multiple cidr and ip, separated by commas.
If several matches are repeated but the actions are different, the array position of natOutgoingPolicyRules shall prevail, and the lower the array index, the higher the priority.
