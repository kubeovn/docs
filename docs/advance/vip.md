# VIP 预留设置

在一些场景下我们希望动态的预留一部分 IP 但是并不分配给 Pod 而是分配给其他的基础设施启用，例如：

- Kubernetes 嵌套 Kubernetes 的场景中上层 Kubernetes 使用 Underlay 网络会占用底层 Subnet 可用地址。
- LB 或其他网络基础设施需要使用一个 Subnet 内的 IP，但不会单独起 Pod。

## 创建随机地址 VIP

如果只是为了预留若干 IP 而对 IP 地址本身没有要求可以使用下面的 yaml 进行创建：

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-dynamic-01
spec:
  subnet: ovn-default
```

- `subnet`: 将从该 Subnet 中预留 IP。

创建成功后查询该 VIP：

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
vip-dynamic-01   10.16.0.12           00:00:00:F0:DB:25                         ovn-default   true
```

可见该 VIP 被分配了 `10.16.0.12` 的 IP 地址，该地址可以之后供其他网络基础设施使用。

## 创建固定地址 VIP

如对预留的 VIP 的 IP 地址有需求可使用下面的 yaml 进行固定分配：

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: static-vip01
spec:
  subnet: ovn-default 
  v4ip: "10.16.0.121"
```

- `subnet`: 将从该 Subnet 中预留 IP。
- `v4ip`: 固定分配的 IP 地址，该地址需在 `subnet` 的 CIDR 范围内。

创建成功后查询该 VIP：

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
static-vip01   10.16.0.121           00:00:00:F0:DB:26                         ovn-default   true
```

可见该 VIP 被分配了所预期的 IP 地址。

## Pod 使用 VIP 来固定 IP

> 该功能目前只在 master 分支支持。

可以使用 annotation 将某个 VIP 分配给一个 Pod：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  annotations:
    ovn.kubernetes.io/vip: vip-dynamic-01 # 指定 vip
  namespace: default
spec:
  containers:
    - name: static-ip
      image: docker.io/library/nginx:alpine
```
