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

该功能默认关闭，需要通过在 Pod 上添加 `ovn.kubernetes.io/port_security` annotation 来启用端口安全功能。

### 启用端口安全

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
