# Fixed Addresses

By default, Kube-OVN randomly assigns IPs and Macs based on the Subnet to which the Pod's Namespace belongs.
For workloads that require fixed addresses, Kube-OVN provides multiple methods of fixing addresses depending on the scenario.

- Single Pod fixed IP/Mac.
- Workload IP Pool to specify fixed addresses.
- StatefulSet fixed address.
- KubeVirt VM fixed address.
- Using Multus to fix addresses for secondary network interfaces.

## Single Pod Fixed IP/Mac

You can specify the IP/Mac required for the Pod by annotation when creating the Pod.
The `kube-ovn-controller` will skip the address random assignment phase and use the specified address directly after conflict detection, as follows:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  annotations:
    ovn.kubernetes.io/ip_address: 10.16.0.15   // for dualstack use comma to separate addresses 10.16.0.15,fd00:10:16::000E
    ovn.kubernetes.io/mac_address: 00:00:00:53:6B:B6
spec:
  containers:
  - name: static-ip
    image: docker.io/library/nginx:alpine
```

The following points need to be noted when using annotation.

1. The IP/Mac used cannot conflict with an existing IP/Mac.
2. The IP must be in the CIDR range of the Subnet it belongs to.
3. You can specify only IP or Mac. When you specify only one, the other one will be assigned randomly.

## Workload IP Pool

Kube-OVN supports setting fixed IPs for Workloads (Deployment/StatefulSet/DaemonSet/Job/CronJob) via annotation `ovn.kubernetes.io/ip_pool`.
`kube-ovn-controller` will automatically select the IP specified in `ovn.kubernetes.io/ip_pool` and perform conflict detection.

The Annotation of the IP Pool needs to be added to the `annotation` field in the `template`.
In addition to Kubernetes built-in workload types, other user-defined workloads can also be assigned fixed addresses using the same approach.

### Deployment With Fixed IPs

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: ls1
  name: starter-backend
  labels:
    app: starter-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: starter-backend
  template:
    metadata:
      labels:
        app: starter-backend
      annotations:
        ovn.kubernetes.io/ip_pool: 10.16.0.15,10.16.0.16,10.16.0.17 // for dualstack ippool use semicolon to separate addresses 10.16.0.15,fd00:10:16::000E;10.16.0.16,fd00:10:16::000F;10.16.0.17,fd00:10:16::0010
    spec:
      containers:
      - name: backend
        image: docker.io/library/nginx:alpine
```

Using a fixed IP for Workload requires the following:

1. The IP in `ovn.kubernetes.io/ip_pool` should belong to the CIDR of the Subnet.
2. The IP in `ovn.kubernetes.io/ip_pool` cannot conflict with an IP already in use.
3. When the number of IPs in `ovn.kubernetes.io/ip_pool` is less than the number of replicas, the extra Pods will not be created. You need to adjust the number of IPs in `ovn.kubernetes.io/ip_pool` according to the update policy of the workload and the scaling plan.

## StatefulSet Fixed Address

StatefulSet supports fixed IP by default, and like other Workload, you can use `ovn.kubernetes.io/ip_pool` to specify the range of IP used by a Pod.

Since StatefulSet is mostly used for stateful services,
which have higher requirements for fixed addresses, Kube-OVN has made special enhancements:

1. Pods are assigned IPs in `ovn.kubernetes.io/ip_pool` in order. For example, if the name of the StatefulSet is web, web-0 will use the first IP in `ovn.kubernetes.io/ip_pool`, web-1 will use the second IP, and so on.
2. The logical_switch_port in the OVN is not deleted during update or deletion of the StatefulSet Pod, and the newly generated Pod directly reuses the old logical port information. Pods can therefore reuse IP/Mac and other network information to achieve similar state retention as StatefulSet Volumes.
3. Based on the capabilities of 2, for StatefulSet without the `ovn.kubernetes.io/ip_pool` annotation, a Pod is randomly assigned an IP/Mac when it is first generated, and then the network information remains fixed for the lifetime of the StatefulSet.

### StatefulSet Example

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx"
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: docker.io/library/nginx:alpine
        ports:
        - containerPort: 80
          name: web
```

You can try to delete the Pod under StatefulSet to observe if the Pod IP changes.

### Updating StatefulSet Pod IPs

Since the IPs of StatefulSet Pods are bound to their lifecycle along with the Pod names, directly updating the `ovn.kubernetes.io/ip_pool` annotation in the StatefulSet will not update the Pod IPs.

If you need to update the IPs of StatefulSet Pods, first scale the StatefulSet replicas down to 0. Then, update the annotation and restore the StatefulSet replicas afterward.

## KubeVirt VM Fixed Address

For VM instances created by KubeVirt, `kube-ovn-controller` can assign and manage IP addresses in a similar way to the StatefulSet Pod.
This allows VM instances address fixed during start-up, shutdown, upgrade, migration, and other operations throughout their lifecycle,
making them more compatible with the actual virtualization user experience. For specific operations, please refer to [Fixed Virtual Machine Addresses](../kubevirt/static-ip.en.md).

## Using Multus to Fix Addresses for Secondary Network Interfaces

When using Multus to configure multiple network interfaces for Pods, Kube-OVN type network interfaces can be configured with fixed addresses through specific annotations. For other CNIs that are not Kube-OVN, Kube-OVN can also provide IPAM capabilities separately to enable other CNIs to have fixed address capabilities as well. For specific operations, please refer to [Multi-NIC Management](../advance/multi-nic.en.md).
