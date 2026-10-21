# 端口安全

端口安全功能用于防止 Pod 进行源地址欺骗攻击。当启用端口安全后，Pod 只能使用由 Kube-OVN IPAM 分配的 MAC 地址和 IP 地址发送网络报文，任何使用未授权地址的报文都会被拦截。这在多租户环境或需要严格网络安全策略的场景中非常有用。

典型使用场景包括：

- 防止恶意 Pod 伪造源 IP 地址发起攻击
- 防止 Pod 伪造 MAC 地址进行 ARP 欺骗
- 满足多租户环境的安全隔离要求

## 实现原理

端口安全基于 OVN 的 Port Security 机制实现。当为 Pod 启用端口安全后，Kube-OVN 会在 OVN 逻辑交换机端口上配置相应的安全策略：

- 在逻辑交换机端口上设置允许的 MAC 地址列表和 IP 地址列表
- OVN 会检查从该端口发出的所有报文的源 MAC 地址和源 IP 地址
- 只有源地址与 IPAM 分配的地址匹配的报文才能通过
- 不匹配的报文会被 OVN 直接丢弃

这种机制在 OVN 数据平面层面实现，性能开销极小，可以有效防止各种源地址欺骗攻击。

## 使用方式

端口安全默认处于关闭状态，支持在子网级别全局开启或在 Pod 级别按需开启。

### 子网级别全局开启

可在创建或更新 Subnet 时设置 `spec.portSecurity: true`，此时该子网下创建的所有 Pod 端口都会默认启用端口安全：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: secure-subnet
spec:
  cidrBlock: 10.16.0.0/16
  portSecurity: true
```

### 单个 Pod 启用端口安全

通过在 Pod 上添加 `ovn.kubernetes.io/port_security` annotation 针对单个 Pod 启用端口安全：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  annotations:
    ovn.kubernetes.io/port_security: "true"
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

对于通过 Multus 添加的多网卡 Pod，可以使用 `<provider>.kubernetes.io/port_security: "true"` 为指定的附属网卡独立启用端口安全。

### 配合 AAP 放行额外地址（如 Keepalived / VRRP）

当启用了端口安全的 Pod 需要使用额外的浮动 IP（VIP）发送报文（例如运行 Keepalived 或 VRRP）时，默认的端口安全策略会将其拦截。可通过 `ovn.kubernetes.io/aaps`（Additional Allowed Address Pairs）注解将允许的额外 IP/MAC 加入端口白名单中：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: vrrp-pod
  annotations:
    ovn.kubernetes.io/port_security: "true"
    ovn.kubernetes.io/aaps: "10.16.0.250"
spec:
  containers:
  - name: keepalived
    image: docker.io/library/nginx:alpine
```
