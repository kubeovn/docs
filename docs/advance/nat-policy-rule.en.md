# Default VPC NAT Policy Rule

## Purpose

In the Overlay Subnet under the default VPC, when the `natOutgoing` switch is turned on, all Pods in the subnet need to do SNAT to access the external network, but in some scenarios we do not want all Pods in the subnet to access the external network by SNAT.

So the NAT Policy Rule is to provide a way for users to decide which CIDRs or IPs in the subnet to access the external network need SNAT.

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

`action`: The action that will be executed for packets that meets the corresponding conditions of the `match`. The action is divided into two types: `forward` and `nat`. When natOutgoingPolicyRules is not configured, packets are still SNAT by default.

`match`: Indicates the matching segment of the message, the matching segment includes `srcIPs` and `dstIPs`, here indicates the source IP and destination IP of the message from the subnet to the external network. `match.srcIPs` and `match.dstIPs` support multiple cidr and ip, separated by commas.
If multiple match rules overlap, the action that is matched first will be executed according to the order of the `natOutgoingPolicyRules` array.
