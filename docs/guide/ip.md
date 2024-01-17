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

具体来说，这个功能是指定 Pod 或者 VM 预留 IP， 在预留 IP 的创建流程中，需要指定资源名，资源类型，命名空间，子网等必要参数。固定 IP 预留，需要指定 ip 地址，MAC 地址（如有需要）。

注意：之前实现的 Pod 使用 vip 占用 IP 的方式弃用。（这两种功能重叠）

如果不确定这些参数，只是想简单预留 IP，请使用 IP Pool。

## 一、创建

IP CR 控制器的创建过程仅处理预留 IP 业务场景（4, 5），不处理随 Pod 创建的 IP 资源。
随 Pod 创建的 IP 资源流程中，LSP 的创建在 IP CR 的创建之前，所以可以基于 LSP 有无来判断，在 IP CR 控制器的处理过程中，会先判断是否存在 LSP，如果存在则不处理该场景：IP 随 Pod 创建的流程。
预留 IP 的创建支持自动分配 IP 以及手动指定 IP，IP 的创建过程中只会实现 IP 占位，而不会创建 LSP。 LSP 的创建还是维护在 Pod 创建流程中。

IP CR 的创建过程也就是仅实现 IP 的预留，这种 IP 会自动添加一个 keep-ip 的 label，表明永久预留不会随 Pod 删除而清理，需要业务来管理这种预留 IP 的清理。GC 不会自动处理该 IP。

### 1.1 Pod 或者 VM 已经创建，需要预留 IP

目前支持用户手动创建 IP 资源，以便预留 IP。用户也可以手动删除 IP 资源。

支持 Pod 使用预留的 IP，而且同时兼容之前 IP 随 Pod 而创建的流程。

### 1.2 Pod 或者 VM 尚未创建，需要预留 IP

这个场景，Pod 或者 VM 尚未创建，IP 预留信息需要填写 Pod 名或者 VM 名， namespace，子网等信息。IP 的命名由这些信息格式化出来。当使用这个 IP 的时候，业务需要校验 IP 绑定到的 Pod 和 VM 是否和 IP 本身的属性一致，否则 Pod 或者 VM 无法使用该 IP。

```yaml

# 预留 IP 创建 Yaml 示例

```

- IP 属性中的 podType 用于指定 Pod 或者 VirtualMachine 的类型
- IP 属性中的 podName 用于指定使用该 IP 资源的名字，Pod 或者 VirtualMachine
- IP 属性中的 namespace 用于指定使用该 IP 资源的 namespace

IP 属性更新：如果使用 IP 的 Pod 或者 VM 发生变化，则会随之变更

## 二、删除

GC 流程不会清理独立的 IP 资源。如果需要清理 IP 以及它的 LSP，请直接删除 IP CR 资源。

IP 的删除流程会基于 IP 属性中的 podName 和 namespace 以及 subnet provider 格式化出 ipam key，LSP 名，释放 IPAM 占位，删除 LSP，以及清理 IP 本身的 Finalizer。
