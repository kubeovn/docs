# IP

IP 用于维护 Pod 或者 VirtualMachine 的 IP 地址。在最初的设计中，IP 的创建在 Pod 的创建流程中，IP 的删除在 Pod 的删除流程中。
目前支持用户手动创建 IP 资源，以便预留 IP。用户也可以手动删除 IP 资源。

支持 pod 使用预先创建的 IP，但同时兼容之前 IP 随 Pod 而创建的流程。

- IP 随 Pod 创建: IP 和 Pod 的关系，命名有对应关系，IP 的命名为 <pod 名>.<pod ns>.<subnet provider> 或者 <VM 名>.<pod ns>.<subnet provider>
- Pod 指定 IP：不强制要求有命名上的对应关系（再考虑下这个点，我不确定这个调整是好的，而且我们自己的需求并未包括做到这点，但是目前先尝试实现，毕竟是一个传统功能），但是强烈建议在业务编排设计上将 IP 的命名和目前的 Pod 或者 VM 命名保持一致。

这两种使用方式，只能独立使用。
Pod 基于 annotation 指定 IP 优先。之前实现的 pod 使用 vip 占用 IP 的方式弃用。（这两种功能重叠）

## 创建

IP 的创建支持自动分配 IP 以及手动指定 IP，IP 的创建过程中只会实现 IP 占位，而不会创建 LSP。
GC 流程不会清理独立的 IP 资源。如果需要清理 IP 以及它的 LSP，请直接删除 IP 资源。

```yaml

# 创建 IP

```

- IP 属性中的 podType 用于指定 Pod 或者 VirtualMachine 的类型
- IP 属性中的 podName 用于指定使用该 IP 资源的名字
- IP 属性中的 namespace 用于指定使用该 IP 资源的 namespace

IP 属性更新：如果变更资源（pod，vm），则会随资源变更

## 删除

IP 的删除流程会基于 IP 属性中的 podName 和 namespace 以及 subnet provider 格式化出 ipam key，LSP 名，释放 IPAM 占位，删除 LSP，以及清理 IP 本身的 Finalizer。
