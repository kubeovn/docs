# Reserved IP for Specific Resources

IP is used to maintain the IP address of Pod or VirtualMachine (VM). The lifecycle maintenance of IP includes the following business scenarios:

- 1. IP is created with Pod and deleted with Pod.
- 2. VM IP is retained by configuring ENABLE_KEEP_VM_IP. This type of IP is created with VM Pod, but not deleted with VM Pod.
- 3. Statefulset Pod IP will automatically decide whether to retain Pod IP based on the capacity of Statefulset and the sequence number of Pod.

In actual business use, it is often necessary to reserve IP resources in advance. The business scenarios for reserving IP include the following two types:

- 4. Pod or VM has been created and needs to reserve IP
- 5. Pod or VM has not been created yet and needs to reserve IP

In the above scenarios, the naming correspondence between IP and Pod remains consistent:

- Naming format of Pod IP: Pod-name.Pod-namespace(.subnet-provider)
- Naming format of VM Pod IP: vm-name.Pod-namespace.(subnet-provider)

If you are unsure about these parameters and just want to simply reserve IP, please use IP Pool.

Specifically, this function is to reserve IP for specific Pod or VM. In the creation process of reserved IP, it is necessary to specify resource name, resource type, namespace, subnet and other necessary parameters. For fixed IP reservation, it is necessary to specify IP address and MAC address (if necessary).

Note: The previous implementation of Pod using vip to occupy IP is deprecated. (These two functions overlap)

## 1. Create Reserved IP

- Pod or VM has been created and needs to reserve IP
- Pod or VM has not been created yet and needs to reserve IP

Reserving IP is just an extended function, which supports Pod to use the reserved IP, but the usage method, naming rules and business logic of IP created with Pod are consistent.
Therefore, when creating a reserved IP, it is necessary to clearly know what resources will use this IP in the future, and the type, Pod name or VM name, namespace, subnet and other information must be accurately filled in.
When using this IP, the business needs to verify whether the Pod and VM bound to the IP are consistent with the attributes of the IP itself, otherwise the Pod or VM cannot use this IP.

The creation process of IP CR controller only handles the business scenario of reserving IP, and does not handle the IP resources created with Pod. In the process of IP resources created with Pod, the creation of LSP is before the creation of IP CR, so it can be judged based on whether LSP exists. In the processing process of IP CR controller, it will first judge whether LSP exists. If it exists, it will not handle this business logic: the business logic of IP created with Pod. The creation of reserved IP supports automatic allocation of IP and manual specification of IP. The creation process of IP will only implement IP occupation, but will not create LSP. The creation of LSP is still maintained in the process of Pod creation. The creation process of IP CR is just to reserve IP. This kind of IP will automatically add a keep-ip label, indicating that it is permanently reserved and will not be cleaned up with the deletion of Pod. This kind of reserved IP needs to be managed by the business or administrator, and GC will not automatically handle this IP.

### 1.1 Auto Allocate Address for Reserved IP

If you just want to reserve some IPs and have no requirements for the IP address itself, you can use the following yaml to create:

```yaml

# cat 01-dynamic.yaml

apiVersion: kubeovn.io/v1
kind: IP
metadata:
  name: vm-dynamic-01.default
spec:
  subnet: ovn-default
  podType: "VirtualMachine"
  namespace: default
  podName: vm-dynamic-01

```

- `subnet`: The IP address is reserved from the Subnet.
- `podType`: Used to specify the Owner type of the Pod: "StatefulSet", "VirtualMachine".
- `podName`: Pod name or VirtualMachine name.
- `namespace`: Used to specify the namespace where the IP resource resides，Pod namespace or VirtualMachine namespace.

> Note: These IP properties are not allowed to change

Query the IP address after the IP address is created:

```bash

# kubectl get subnet ovn-default
NAME          PROVIDER   VPC           PROTOCOL   CIDR           PRIVATE   NAT    DEFAULT   GATEWAYTYPE   V4USED   V4AVAILABLE   V6USED   V6AVAILABLE   EXCLUDEIPS      U2OINTERCONNECTIONIP
ovn-default   ovn        ovn-cluster   IPv4       10.16.0.0/16   false     true   true      distributed   7        65526         0        0             ["10.16.0.1"]

# kubectl get ip vm-dynamic-01.default -o yaml
apiVersion: kubeovn.io/v1
kind: IP
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"kubeovn.io/v1","kind":"IP","metadata":{"annotations":{},"name":"vm-dynamic-01.default"},"spec":{"namespace":"default","podName":"vm-dynamic-01","podType":"VirtualMachine","subnet":"ovn-default"}}
  creationTimestamp: "2024-01-29T03:05:40Z"
  finalizers:
  - kube-ovn-controller
  generation: 2
  labels:
    ovn.kubernetes.io/ip_reserved: "true" # reserved ip
    ovn.kubernetes.io/node-name: ""
    ovn.kubernetes.io/subnet: ovn-default
  name: vm-dynamic-01.default
  resourceVersion: "1571"
  uid: 89d05a26-294a-450b-ab63-1eaa957984d7
spec:
  attachIps: []
  attachMacs: []
  attachSubnets: []
  containerID: ""
  ipAddress: 10.16.0.13
  macAddress: 00:00:00:86:C6:36
  namespace: default
  nodeName: ""
  podName: vm-dynamic-01
  podType: VirtualMachine
  subnet: ovn-default
  v4IpAddress: 10.16.0.13
  v6IpAddress: ""

# kubectl ko nbctl show ovn-default | grep vm-dynamic-01.default
# The reserved IP address is assigned only in the IPAM, and the LSP is not created. Therefore, you cannot view the IP address

```

### 1.2 Specifies the reserved IP address

If there is a need for the IP address of the reserved IP, the following yaml can be used for fixed allocation:

```yaml
# cat  02-static.yaml

apiVersion: kubeovn.io/v1
kind: IP
metadata:
  name: pod-static-01.default
spec:
  subnet: ovn-default
  podType: ""
  namespace: default
  podName: pod-static-01
  v4IpAddress: 10.16.0.3
  v6IpAddress:

# kubectl get ip pod-static-01.default -o yaml
apiVersion: kubeovn.io/v1
kind: IP
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"kubeovn.io/v1","kind":"IP","metadata":{"annotations":{},"name":"pod-static-01.default"},"spec":{"namespace":"default","podName":"pod-static-01","podType":"","subnet":"ovn-default","v4IpAddress":"10.16.0.3","v6IpAddress":null}}
  creationTimestamp: "2024-01-29T03:08:28Z"
  finalizers:
  - kube-ovn-controller
  generation: 2
  labels:
    ovn.kubernetes.io/ip_reserved: "true"
    ovn.kubernetes.io/node-name: ""
    ovn.kubernetes.io/subnet: ovn-default
  name: pod-static-01.default
  resourceVersion: "1864"
  uid: 11fc767d-f57d-4520-89f9-448f9b272bca
spec:
  attachIps: []
  attachMacs: []
  attachSubnets: []
  containerID: ""
  ipAddress: 10.16.0.3
  macAddress: 00:00:00:4D:B4:36
  namespace: default
  nodeName: ""
  podName: pod-static-01
  podType: ""
  subnet: ovn-default
  v4IpAddress: 10.16.0.3
  v6IpAddress: ""

```

- `v4IpAddress`: Specify an IPv4 address that is within the CIDR range of the subnet.
- `v6IpAddress`: Specify an IPv6 address that is within the CIDR range of the subnet.

### [Pod use reserved IP](../guide/ip.en.md)

> Note: The Pod(VMS) name and namespace must be the same as the reserved IP address, otherwise the Pod(VMS) cannot use the IP address.

After a Pod or VM is deleted, the IP CR remains.

```bash

root@base:~/test/ip# kubectl get po -n default -o wide
NAME            READY   STATUS    RESTARTS   AGE   IP          NODE              NOMINATED NODE   READINESS GATES
pod-static-01   1/1     Running   0          30s   10.16.0.3   kube-ovn-worker   <none>           <none>

```

## 2. Delete

The kube-ovn-controller GC process does not clean up individual IP resources. To clear an IP address and its LSPS, delete the IP CR resource.

The IP deletion process formats the ipam key and LSP name based on the podName, namespace, and subnet provider in the IP attribute, releases the IPAM slot, deletes the LSP, and clears the Finalizer of the IP.
