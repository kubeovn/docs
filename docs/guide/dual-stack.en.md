# DualStack

Different subnets in Kube-OVN can support different IP protocols. IPv4, IPv6 and dual-stack types of subnets can exist within one cluster.
However, it is recommended to use a uniform protocol type within a cluster to simplify usage and maintenance.

In order to support dual-stack, the host network needs to meet the dual-stack requirements,
and the Kubernetes-related parameters need to be adjusted, please refer to [official guide to dual-stack](https://kubernetes.io/docs/concepts/services-networking/dual-stack).

## Create dual-stack Subnet

When configuring a dual stack Subnet, you only need to set the corresponding subnet CIDR format as `cidr=<IPv4 CIDR>,<IPv6 CIDR>`.

The CIDR order requires IPv4 to come first and IPv6 to come second, as follows.

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata: 
  name: ovn-test
spec:
  cidrBlock: 10.16.0.0/16,fd00:10:16::/64
  excludeIps:
  - 10.16.0.1
  - fd00:10:16::1
  gateway: 10.16.0.1,fd00:10:16::1
```

If you need to use a dual stack for the default subnet during installation, you need to change the following parameters in the installation script (the default IPv6 mask under dual-stack in `install.sh` is `/112`, which more easily avoids common ULA ranges; `/64` is also allowed if preferred, but make sure it does not collide with node or Service CIDRs):

```bash
POD_CIDR="10.16.0.0/16,fd00:10:16::/112"
JOIN_CIDR="100.64.0.0/16,fd00:100:64::/112"
```

## Check Pod Address

Pods configured for dual-stack networks will be assigned both IPv4 and IPv6 addresses from that subnet,
and the results will be displayed in the annotation of the Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/allocated: "true"
    ovn.kubernetes.io/cidr: 10.16.0.0/16,fd00:10:16::/64
    ovn.kubernetes.io/gateway: 10.16.0.1,fd00:10:16::1
    ovn.kubernetes.io/ip_address: 10.16.0.9,fd00:10:16::9
    ovn.kubernetes.io/logical_switch: ovn-default
    ovn.kubernetes.io/mac_address: 00:00:00:14:88:09
    ovn.kubernetes.io/routed: "true"
...
podIP: 10.16.0.9
  podIPs:
  - ip: 10.16.0.9
  - ip: fd00:10:16::9
```

## Select IP Family for a Single Pod or NIC

In a dual-stack subnet, if a Pod or one of its NICs only needs an IPv4 or IPv6 address, set the `ip_family` annotation when creating the Pod.
When this annotation is not set, Kube-OVN keeps the default dual-stack allocation behavior.
The following examples assume that the target Pod or NIC uses a dual-stack Subnet.

Use `ovn.kubernetes.io/ip_family` for the default network:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ipv4-only
  annotations:
    ovn.kubernetes.io/ip_family: ipv4
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

The supported values are `ipv4` and `ipv6`. This feature only selects one address family from a dual-stack subnet and does not change the protocol type of the subnet.
If `ipv6` is requested from an IPv4-only subnet, or `ipv4` is requested from an IPv6-only subnet, Kube-OVN will not allocate an address for the Pod.

For a secondary NIC added through Multus, use `<provider>.kubernetes.io/ip_family`. The `<provider>` must match the provider in the corresponding NetworkAttachmentDefinition or Subnet:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: attach-ipv6-only
  annotations:
    k8s.v1.cni.cncf.io/networks: default/attachnet
    attachnet.default.ovn.kubernetes.io/ip_family: ipv6
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

When the same NetworkAttachmentDefinition is attached multiple times with different `interface` names, Kube-OVN reads the annotation from the provider name that includes the interface name.
For example, `net1` gets IPv4 only and `net2` gets IPv6 only:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: attach-mixed-family
  annotations:
    k8s.v1.cni.cncf.io/networks: '[{"name": "attachnet", "namespace": "default", "interface": "net1"}, {"name": "attachnet", "namespace": "default", "interface": "net2"}]'
    attachnet.default.ovn.net1.kubernetes.io/ip_family: ipv4
    attachnet.default.ovn.net2.kubernetes.io/ip_family: ipv6
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

If a static IP is also set, for example with `ovn.kubernetes.io/ip_address`, `<provider>.kubernetes.io/ip_address`, or `<nadName>.<nadNamespace>.kubernetes.io/ip_address.<interfaceName>` for same-NAD multi-interface Pods, the static IP address family must match `ip_family`.
