# 指定资源预留 IP

IP 用于维护 Pod 或者 VirtualMachine(VM) 的 IP 地址。IP 的生命周期维护包括以下业务场景：

- 1. IP 随 Pod 创建，也随 Pod 删除。
- 2. VM IP 通过配置 ENABLE_KEEP_VM_IP 来保留 VM IP 资源，这种 IP 随 VM Pod 创建，但是不随 VM Pod 删除。
- 3. Statefulset Pod IP 会根据 Statefulset 的容量以及 Pod 序列号自动选择是否保留 Pod IP。

实际上在业务使用中，往往需要提前预留 IP 资源， 预留 IP 的业务场景包括如下两种：

- 4. Pod 或者 VM 已经创建，需要预留 IP
- 5. Pod 或者 VM 尚未创建，需要预留 IP

以上这几种场景，IP 和 Pod 在命名上的对应关系保持一致:

- Pod IP 的命名格式: Pod-name.Pod-namespace(.subnet-provider)
- VM Pod IP 的命名格式: vm-name.Pod-namespace.(subnet-provider)

如果不确定这些参数，只是想简单预留 IP，请使用 IP Pool。

具体来说，这个功能是指定 Pod 或者 VM 预留 IP， 在预留 IP 的创建流程中，需要指定资源名，资源类型，命名空间，子网等必要参数。固定 IP 预留，需要指定 ip 地址，MAC 地址（如有需要）。

> 注意：之前实现的 Pod 使用 vip 占用 IP 的方式弃用。（这两种功能重叠）

## 一、创建预留 IP

- Pod 或者 VM 已经创建，需要预留 IP
- Pod 或者 VM 尚未创建，需要预留 IP

预留 IP 只是一个扩展功能，支持 Pod 使用预留的 IP，但是使用方式，命名规则和 IP 随 Pod 而创建的业务逻辑一致。
所以预留 IP 创建时需要明确该 IP 后续被什么资源使用，必须准确填写类型，Pod 名或者 VM 名，namespace，子网等信息。
当使用这个 IP 的时候，业务需要校验 IP 绑定到的 Pod 和 VM 是否和 IP 本身的属性一致，否则 Pod 或者 VM 无法使用该 IP。

IP CR 控制器的创建过程仅处理预留 IP 业务场景，不处理随 Pod 创建的 IP 资源。
随 Pod 创建的 IP 资源流程中，LSP 的创建在 IP CR 的创建之前，所以可以基于 LSP 有无来判断，在 IP CR 控制器的处理过程中，会先判断是否存在 LSP，如果存在则不处理该业务逻辑：IP 随 Pod 创建的业务逻辑。
预留 IP 的创建支持自动分配 IP 以及手动指定 IP，IP 的创建过程中只会实现 IP 占位，而不会创建 LSP。 LSP 的创建还是维护在 Pod 创建流程中。
IP CR 的创建过程也就是仅实现 IP 的预留，这种 IP 会自动添加一个 keep-ip 的 label，表明永久预留不会随 Pod 删除而清理。需要业务或者管理员来管理这种预留 IP 的清理，GC 不会自动处理该 IP。

### 1.1 预留 IP 自动分配地址

如果只是为了预留若干 IP 而对 IP 地址本身没有要求可以使用下面的 yaml 进行创建：

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

- `subnet`: 将从该 Subnet 中预留 IP。
- `podType`: 用于指定 Pod 的 Owner 类型: "StatefulSet", "VirtualMachine"。
- `podName`: IP 属性中的 podName 用于指定使用该 IP 资源的名字，Pod 或者 VirtualMachine 的名字。
- `namespace`: 用于指定使用该 IP 资源所在的 namespace，Pod 或者 VirtualMachine namespace。

注意： 这些 IP 属性不允许变更

创建成功后查询该 IP：

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
    ovn.kubernetes.io/ip_reserved: "true" # 预留 IP 标识
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
# 预留 IP，仅在 IPAM 中分配地址，不创建 LSP，所以查看不到

```

### 1.2 指定地址预留 IP

如对预留的 IP 的 IP 地址有需求可使用下面的 yaml 进行固定分配：

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

- `v4IpAddress`: 指定 IPv4 地址，该地址需在 `subnet` 的 CIDR 范围内。
- `v6IpAddress`: 指定 IPv6 地址，该地址需在 `subnet` 的 CIDR 范围内。

### [Pod 使用预留 IP](../guide/ip.md)

> 注意: Pod 的名字以及 namespace 必须和预留 IP 的属性一致，否则 Pod 无法使用该 IP。VM 也是如此。

删除 Pod 或者 VM 后， 该 IP CR 依然保留。

```bash

root@base:~/test/ip# kubectl get po -n default -o wide
NAME            READY   STATUS    RESTARTS   AGE   IP          NODE              NOMINATED NODE   READINESS GATES
pod-static-01   1/1     Running   0          30s   10.16.0.3   kube-ovn-worker   <none>           <none>

```

## 二、删除

kube-ovn-controller GC 流程不会清理独立的 IP 资源。如果需要清理 IP 以及它的 LSP，请直接删除 IP CR 资源。

IP 的删除流程会基于 IP 属性中的 podName 和 namespace 以及 subnet provider 格式化出 ipam key，LSP 名，释放 IPAM 占位，删除 LSP，以及清理 IP 本身的 Finalizer。
