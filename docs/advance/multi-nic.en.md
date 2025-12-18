# Manage Multiple Interface

Kube-OVN can provide cluster-level IPAM capabilities for other CNI network plugins (such as macvlan, vlan, host-device, etc.),
enabling these network plugins to use Kube-OVN's subnet and fixed IP capabilities.

Kube-OVN also supports address management when multiple NICs are all of Kube-OVN type.

## Working Principle

Multi-nic management:

Here's an illustration of the network interfaces attached to a pod, as provisioned by [Multus CNI](https://github.com/k8snetworkplumbingwg/multus-cni). The diagram shows the pod with three interfaces: eth0, net0 and net1. eth0 connects kubernetes cluster network to connect with kubernetes server/services (e.g. kubernetes api-server, kubelet and so on). net0 and net1 are attached network interfaces and connect to other networks by using other CNI plugins (e.g. vlan/vxlan/ptp).

![multus-cni-multi-nic](../static/multus-pod-image.svg)

IPAM:

By using [Multus CNI](https://github.com/k8snetworkplumbingwg/multus-cni), we can add multiple NICs of different networks to a Pod.
However, we still lack the ability to manage the IP addresses of different networks within a cluster.
In Kube-OVN, we have been able to perform advanced IP management such as subnet management, IP reservation, random assignment, fixed assignment, etc. through CRD of Subnet and IP.
Now Kube-OVN extends the subnet to integrate with other different network plugins,
so that other network plugins can also use the IPAM functionality of Kube-OVN.

### Workflow

![work-flow](../static/mult-nic-workflow.png)

The above diagram shows how to manage the IP addresses of other network plugins via Kube-OVN.
The eth0 NIC of the container is connected to the OVN network and the net1 NIC is connected to other CNI networks.
The network definition for the net1 network is taken from the NetworkAttachmentDefinition resource definition in multus-cni.

When a Pod is created, `kube-ovn-controller` will get the Pod add event, find the corresponding Subnet according to the annotation in the Pod,
then manage the address from it, and write the address information assigned to the Pod back to the Pod annotation.

On the container node, CNI can configure `kube-ovn-cni` as the ipam plugin.
`kube-ovn-cni` will read the Pod annotation and return the address information to the corresponding CNI plugin using the standard format of the CNI protocol.

## Compatibility Issues

`NetworkAttachmentDefinition` supports an empty `spec`, where Multus will automatically search for the CNI configuration file with the same name in the `defaultConfDir` on each Node, as shown below:

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf-2
```

However, `kube-ovn-controller` needs to centrally retrieve the `provider` information from each `NetworkAttachmentDefinition` and cannot fetch the corresponding configuration files from each node. Since the configuration information is scattered across nodes when `spec` is empty, `kube-ovn-controller` cannot obtain the required `provider` information. As a result, the usage of an empty `spec` is incompatible with Kube-OVN's IPAM capability.

## Usage

### Install Kube-OVN and Multus

Please refer to [One-Click Installation](../start/one-step-install.en.md) and [Multus how to use](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/how-to-use.md) to install Kube-OVN and Multus-CNI.

### Provide IPAM for other types of CNI

#### Create NetworkAttachmentDefinition

Here we use macvlan as the second network of the container network and set its ipam to `kube-ovn`:

```shell
# load macvlan module
sudo modprobe macvlan
```

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "macvlan",
      "master": "eth0",
      "mode": "bridge",
      "ipam": {
        "type": "kube-ovn",
        "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
        "provider": "macvlan.default"
      }
    }'
```

- `spec.config.ipam.type`: Need to be set to `kube-ovn` to call the kube-ovn plugin to get the address information.
- `server_socket`: The socket file used for communication to Kube-OVN, the default location is `/run/openvswitch/kube-ovn-daemon.sock`.
- `provider`: The current NetworkAttachmentDefinition's `<name>.<namespace>`, Kube-OVN will use this information to find the corresponding Subnet resource.
- `master`: the host's physical network card

!!! info

    The `provider` here and `ProviderNetwork` in Underlay are two different concepts and are not directly related. Due to early naming, this may cause confusion, please distinguish them.

#### Create a Kube-OVN Subnet

Create a Kube-OVN Subnet, set the corresponding `cidrBlock` and `exclude_ips`, the `provider` should be set to the `<name>.<namespace>` of corresponding NetworkAttachmentDefinition.
For example, to provide attached NICs with macvlan, create a Subnet as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: macvlan
spec:
  protocol: IPv4
  provider: macvlan.default
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  excludeIps:
  - 172.17.0.0..172.17.0.10
```

> Note: The `gateway`, `private`, and `nat` fields are only valid for networks with `provider` type ovn, not for attachment networks.

##### Create a Pod with Multiple NIC

For Pods with randomly assigned addresses, simply add the following annotation `k8s.v1.cni.cncf.io/networks`, taking the value `<namespace>/<name>` of the corresponding NetworkAttachmentDefinition:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: samplepod
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: default/macvlan
spec:
  containers:
  - name: samplepod
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

##### Create Pod with a Fixed IP

For Pods with fixed IPs, add `<networkAttachmentName>.<networkAttachmentNamespace>.kubernetes.io/ip_address` annotation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: default/macvlan
    ovn.kubernetes.io/ip_address: 10.16.0.15
    ovn.kubernetes.io/mac_address: 00:00:00:53:6B:B6
    macvlan.default.kubernetes.io/ip_address: 172.17.0.100
    macvlan.default.kubernetes.io/mac_address: 00:00:00:53:6B:BB
spec:
  containers:
  - name: static-ip
    image: docker.io/library/nginx:alpine
```

##### Create Workloads with Fixed IPs

For workloads that use ippool, add `<networkAttachmentName>.<networkAttachmentNamespace>.kubernetes.io/ip_pool` annotation:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: default
  name: static-workload
  labels:
    app: static-workload
spec:
  replicas: 2
  selector:
    matchLabels:
      app: static-workload
  template:
    metadata:
      labels:
        app: static-workload
      annotations:
        k8s.v1.cni.cncf.io/networks: default/macvlan
        ovn.kubernetes.io/ip_pool: 10.16.0.15,10.16.0.16,10.16.0.17
        macvlan.default.kubernetes.io/ip_pool: 172.17.0.200,172.17.0.201,172.17.0.202
    spec:
      containers:
      - name: static-workload
        image: docker.io/library/nginx:alpine
```

##### Create a Pod using macvlan as default route

For Pods that use macvlan as an attached network card, if you want to use the attached network card as the default route of the Pod, you only need to add the following annotation, where `default-route` is the gateway address:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: samplepod-route
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: '[{
      "name": "macvlan",
      "namespace": "default",
      "default-route": ["172.17.0.1"]
    }]'
spec:
  containers:
  - name: samplepod-route
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

##### Create a Pod using macvlan as the main nic

For Pods that use macvlan as the main network card, you only need to add the following annotation `v1.multus-cni.io/default-network`, taking the value `<namespace>/<name>` of the corresponding NetworkAttachmentDefinition:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: samplepod-macvlan
  namespace: default
  annotations:
    v1.multus-cni.io/default-network: default/macvlan
spec:
  containers:
  - name: samplepod-macvlan
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

#### Create a Kube-OVN Subnet (Provider ovn)

When you need to obtain IP from a subnet with `provider` type ovn, you can create a Kube-OVN Subnet with `provider` set to ovn, set the corresponding `cidrBlock` and `exclude_ips`, and create the Subnet as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: macvlan
spec:
  protocol: IPv4
  provider: ovn
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  excludeIps:
  - 172.17.0.0..172.17.0.10
```

##### Create a Pod with Multiple NIC

For Pods that need to obtain IP from the subnet with `provider` type ovn, you need to combine the annotation `k8s.v1.cni.cncf.io/networks` and `<networkAttachmentName>.<networkAttachmentNamespace>.kubernetes.io/logical_switch`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: samplepod
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: default/macvlan
    macvlan.default.kubernetes.io/logical_switch: macvlan
spec:
  containers:
  - name: samplepod
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

- `k8s.v1.cni.cncf.io/networks`: The value is `<namespace>/<name>` of the corresponding NetworkAttachmentDefinition
- `macvlan.default.kubernetes.io/logical_switch`: The value is the subnet name

> Note:
>
> - Specifying a subnet through `<networkAttachmentName>.<networkAttachmentNamespace>.kubernetes.io/logical_switch` has a higher priority than specifying a subnet through provider.
> - Subnets based on ovn type provide ipam and also support the creation of fixed IP Pods, the creation of workloads with fixed IPs, and the creation of Pods with the default route as macvlan.
> - However, creating a Pod with the main network card as macvlan is not supported.

### The attached NIC is a Kube-OVN type NIC

At this point, the multiple NICs are all Kube-OVN type NICs.

#### Create NetworkAttachmentDefinition

Set the `provider` suffix to `ovn`:

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: attachnet
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "attachnet.default.ovn"
    }'
```

- `spec.config.type`: Set to `kube-ovn` to trigger the CNI plugin to use Kube-OVN subnet.
- `server_socket`: The socket file used for communication to Kube-OVN, the default location is `/run/openvswitch/kube-ovn-daemon.sock`.
- `provider`: The current NetworkAttachmentDefinition's `<name>.<namespace>.ovn`, Kube-OVN will use this information to find the corresponding Subnet resource, note that the suffix should be set to ovn.

#### Create a Kube-OVN Subnet

If you are using Kube-OVN as an attached NIC, `provider` should be set to the `<name>.<namespace>.ovn` of the corresponding NetworkAttachmentDefinition, and should end with `ovn` as a suffix.

An example of creating a Subnet with an attached NIC provided by Kube-OVN is as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: attachnet
spec:
  protocol: IPv4
  provider: attachnet.default.ovn
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  excludeIps:
  - 172.17.0.0..172.17.0.10
```

##### Create a Pod with Multiple NIC

For Pods with randomly assigned addresses, simply add the following annotation `k8s.v1.cni.cncf.io/networks`, taking the value `<namespace>/<name>` of the corresponding NetworkAttachmentDefinition:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: samplepod
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: default/attachnet
spec:
  containers:
  - name: samplepod
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

##### Configure Custom Routes for Attached NICs

For Pods with Kube-OVN attached network cards, custom routes can be configured through the `<networkAttachmentName>.<networkAttachmentNamespace>.ovn.kubernetes.io/routes` annotation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-routes-attach
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: default/attachnet
    attachnet.default.ovn.kubernetes.io/routes: |
      [{
        "dst": "192.168.0.101/24",
        "gw": "172.17.0.254"
      }, {
        "gw": "172.17.0.254"
      }]
spec:
  containers:
  - name: custom-routes-attach
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

> The `dst` field being empty means modifying the default route.

If the workload is a Deployment, DaemonSet, or StatefulSet, the corresponding annotation needs to be configured in the `.spec.template.metadata.annotations` of the resource:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-routes-attach
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
      annotations:
        k8s.v1.cni.cncf.io/networks: default/attachnet
        attachnet.default.ovn.kubernetes.io/routes: |
          [{
            "dst": "192.168.0.101/24",
            "gw": "172.17.0.254"
          }, {
            "gw": "172.17.0.254"
          }]
    spec:
      containers:
      - name: nginx
        image: docker.io/library/nginx:alpine
```

#### Create a Kube-OVN Subnet (Provider ovn)

When you need to obtain IP from a subnet with `provider` type ovn, you can create a Kube-OVN Subnet with `provider` set to ovn, set the corresponding `cidrBlock` and `exclude_ips`, and create the Subnet as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: attachnet
spec:
  protocol: IPv4
  provider: ovn
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  excludeIps:
  - 172.17.0.0..172.17.0.10
```

##### Create a Pod with Multiple NIC

For Pods that need to obtain IP from the subnet whose `provider` type is ovn, the annotation `k8s.v1.cni.cncf.io/networks` and `<networkAttachmentName>.<networkAttachmentNamespace>.ovn.kubernetes.io/logical_switch` need to be used in conjunction:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: samplepod
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: default/attachnet
    attachnet.default.ovn.kubernetes.io/logical_switch: attachnet
spec:
  containers:
  - name: samplepod
    command: ["/bin/ash", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: docker.io/library/alpine:edge
```

- `k8s.v1.cni.cncf.io/networks`: The value is `<namespace>/<name>` of the corresponding NetworkAttachmentDefinition
- `attachnet.default.ovn.kubernetes.io/logical_switch`: The value is the subnet name

> Note:
>
> - Specifying a subnet through `<networkAttachmentName>.<networkAttachmentNamespace>.ovn.kubernetes.io/logical_switch` has a higher priority than specifying a subnet through provider.
> - For Pods with Kube-OVN attached network cards, the creation of fixed IP Pods, the creation of workloads with fixed IPs, the creation of Pods with the default route as macvlan, and the creation of Pods with the main network card as Kube-OVN type are all supported. For the configuration method, please refer to the previous section.
> - For Pods with Kube-OVN attached network cards, custom routes can also be configured through the `<networkAttachmentName>.<networkAttachmentNamespace>.ovn.kubernetes.io/routes` annotation.
