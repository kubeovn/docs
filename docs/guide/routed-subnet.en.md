# Routed Subnet Mode

Set `spec.routed: true` on a `Subnet` to configure Pods with host masks (`/32` for IPv4 or `/128` for IPv6) and send all traffic through the subnet gateway. The subnet is no longer a shared Layer 2 broadcast domain, and same-subnet traffic is routed through the OVN logical router.

## Create a Routed Subnet

The following example creates an IPv4 routed Overlay subnet:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: routed-subnet
spec:
  cidrBlock: 10.0.0.0/16
  gateway: 10.0.0.1
  protocol: IPv4
  provider: ovn
  routed: true
```

`spec.cidrBlock` is still used for IPAM allocation. `routed` only changes the Pod interface mask and routes. For a Pod with address `10.0.0.5`, CNI configures:

```text
ip addr add 10.0.0.5/32 dev eth0
ip route add 10.0.0.1/32 dev eth0
ip route add default via 10.0.0.1
```

IPv6 Pods use `/128` addresses and the corresponding IPv6 gateway host route.

## Traffic Isolation

East-west traffic between Pods in the same subnet is hairpinned through the OVN logical router instead of being switched directly at Layer 2. Routed-subnet OVN ACLs use an allow-list and default-deny policy:

- Allow ARP/ND only for the subnet gateway.
- Allow IP frames destined for the logical router port MAC in both ACL directions.
- Allow IP frames sourced from the logical router port MAC. In the `from-lport` direction, the packet must also enter through the logical router port, preventing Pods from spoofing the gateway MAC.
- Drop all other IP, ARP, and ND traffic.

When `private: true`, ingress through the logical router is further limited to same-subnet hairpin traffic, the node Join CIDR, and the ranges listed in `allowSubnets`.

## Route Annotations

Provider route annotations, such as `ovn.kubernetes.io/routes`, are supported on non-DPDK interfaces. In a routed subnet, every annotated route must use the subnet gateway as its next hop. With U2O interconnection, the corresponding U2O interconnection IP can be used. Destinations must be valid CIDRs; CNI ADD fails when a route cannot be parsed or installed.

Other next hops are rejected because routed subnets only allow Pods to resolve the subnet gateway. `ovn.kubernetes.io/routed` is a separate Pod annotation that only indicates OVN routes are ready for the Pod; it does not enable routed-subnet mode.

## Limitations

- Only OVN Provider subnets are supported. Overlay subnets can use routed mode directly; Underlay subnets must enable `logicalGateway` or `u2oInterconnection` to provide an OVN logical router port.
- `enableDHCP`, `enableIPv6RA`, `enableMulticastSnoop`, mac-only/BYO-DHCP subnets, and custom `spec.acls` are not supported.
- DPDK/vhost-user interfaces are not supported, and those interfaces also reject route annotations.
- Enabling or disabling `routed` does not reconfigure existing Pods. Recreate Pods after changing the field to apply the new masks and routes.
