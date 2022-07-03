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

If you need to use a dual stack for the default subnet during installation, you need to change the following parameters in the installation script:

```bash
POD_CIDR="10.16.0.0/16,fd00:10:16::/64"
JOIN_CIDR="100.64.0.0/16,fd00:100:64::/64"
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
    ovn.kubernetes.io/network_types: geneve
    ovn.kubernetes.io/routed: "true"
...
podIP: 10.16.0.9
  podIPs:
  - ip: 10.16.0.9
  - ip: fd00:10:16::9
```
