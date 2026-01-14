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
  enableAddressSet: true
```

Bind to a specific Workload:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ippool
  labels:
    app: ippool
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ippool
  template:
    metadata:
      labels:
        app: ippool
      annotations:
        ovn.kubernetes.io/ip_pool: pool-1
    spec:
      containers:
      - name: ippool
        image: docker.io/library/nginx:alpine
```

Field description:

| Field | Usage | Comment |
| :--------: | :------------------------------------- | :------------------------------------------------------------------ |
| subnet | Specify the subnet to which it belongs | Required |
| ips | Specify IP ranges | Support three formats: <IP>, <CIDR> and <IP1>..<IP2>. Support IPv6. |
| namespaces | Specifies the bound namespaces | Optional. Pods in a bound namespace will only get IPs from the bound pool(s), not other ranges in the subnet. |
| enableAddressSet | Whether to automatically create an AddressSet with the same name | Default false. When set to true, ACL and policy routing can use the corresponding AddressSet for policy control |

## Precautions

1. To ensure compatibility with [Workload Universal IP Pool Fixed Address](./static-ip-mac.md#workload-ip-pool), the name of the IP pool cannot be an IP address.
2. The `.spec.ips` of the IP pool can specify an IP address beyond the scope of the subnet, but the actual effective IP address is the intersection of `.spec.ips` and the CIDR of the subnet.
3. Different IP pools of the same subnet cannot contain the same (effective) IP address.
4. The `.spec.ips` of the IP pool can be modified dynamically.
5. The IP pool will inherit the reserved IP of the subnet. When randomly assigning an IP address from the IP pool, the reserved IP included in the IP pool will be skipped.
6. When randomly assigning an IP address from a subnet, it will only be assigned from a range other than all IP pools in the subnet.
7. Multiple IP pools can be bound to the same Namespace.
8. The `.spec.enableAddressSet` of the IP pool defaults to `false`. After setting it to `true`, an OVN NB database AddressSet object corresponding to the IP pool will be created, and all IP addresses in the IP pool will be added to the AddressSet. You can use this AddressSet object with NetworkPolicy or VPC logical router policies.
