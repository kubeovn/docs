# Configure IPPool

IPPool is a more granular IPAM management unit than Subnet. You can subdivide the subnet segment into multiple units through IPPool, and each unit is bound to one or more namespaces.

## Instructions

Below is an example:

```yaml
apiVersion: kubeovn.io/v1
kind: IPPool
metadata:
  name: pool-1
spec:
  subnet: ovn-default
  ips:
  - "10.16.0.201"
  - "10.16.0.210/30"
  - "10.16.0.220..10.16.0.230"
  namespaces:
  - ns-1
```

Field description:

|   Field    | Usage                                  | Comment                                                             |
| :--------: | :------------------------------------- | :------------------------------------------------------------------ |
|   subnet   | Specify the subnet to which it belongs | Required                                                            |
|    ips     | Specify IP ranges                      | Support three formats: <IP>, <CIDR> and <IP1>..<IP2>. Support IPv6. |
| namespaces | Specifies the bound namespaces         | Optional, once a namespace is bound to an IP pool, it will not allocate addresses from other address spaces within the subnet.  |

## Precautions

1. To ensure compatibility with [Workload Universal IP Pool Fixed Address](./static-ip-mac.md#workload-ip-pool), the name of the IP pool cannot be an IP address.
2. The `.spec.ips` of the IP pool can specify an IP address beyond the scope of the subnet, but the actual effective IP address is the intersection of `.spec.ips` and the CIDR of the subnet.
3. Different IP pools of the same subnet cannot contain the same (effective) IP address.
4. The `.spec.ips` of the IP pool can be modified dynamically.
5. The IP pool will inherit the reserved IP of the subnet. When randomly assigning an IP address from the IP pool, the reserved IP included in the IP pool will be skipped.
6. When randomly assigning an IP address from a subnet, it will only be assigned from a range other than all IP pools in the subnet.
7. Multiple IP pools can be bound to the same Namespace.
