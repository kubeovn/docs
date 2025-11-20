# 基于域名的访问控制

Kubernetes 原生的 NetworkPolicy 只支持通过 L3 和 L4 协议对网络访问进行控制。通过 [AdminNetworkPolicy (ANP)](https://network-policy-api.sigs.k8s.io/api-overview/) 可以实现出口流量的域名级别控制，允许管理员通过域名方式管理集群内 Pod 对外部服务的访问。该功能需要配合 [DNSNameResolver](https://github.com/kubeovn/dnsnameresolver) CoreDNS 插件来使用。

## 实现原理

相比原生的 NetworkPolicy 可以直接使用 OVN 中的 AddressSet 记录需要进行访问控制的 IP 列表，基于域名的访问控制需要动态将域名转换成 IP 地址加入到 OVN 的 AddressSet 中，从而实现 DNS 的访问控制。

实现流程：

1. kube-ovn-controller 根据 AdminNetworkPolicy 里域名规则的信息生成 DNSNameResolver CR 资源。
2. CoreDNS 在解析域名过程中和所有 DNSNameResolver CR 资源进行匹配，一旦解析记录匹配，则将域名对应的 IP 地址信息更新到 DNSNameResolver status 中。
3. kube-ovn-controller 根据 DNSNameResolver CR 资源的 status 信息更新对应的 AddressSet。

## 使用限制

由于域名和 IP 的映射关系是解析时确认，因此规则的生效存在延迟，可能导致对于 Deny 规则第一次访问成功，对于 Allow 规则第一次访问失败的现象。为了避免安全泄漏的问题，我们建议对于域名的访问控制只使用 Allow 规则，配合默认的 Deny 规则，同时应用自身要有重试的机制。

## 前置条件

### 部署 ANP 和 BANP CRD

首先部署 AdminNetworkPolicy 相关的 CRD：

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/network-policy-api/refs/heads/main/config/crd/experimental/policy.networking.k8s.io_adminnetworkpolicies.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/network-policy-api/refs/heads/main/config/crd/experimental/policy.networking.k8s.io_baselineadminnetworkpolicies.yaml
```

### 部署 DNSNameResolver 组件

部署 DNSNameResolver 相关资源：

```bash
kubectl apply -f https://raw.githubusercontent.com/kubeovn/dnsnameresolver/refs/heads/main/manifest/crd.yaml
kubectl apply -f https://raw.githubusercontent.com/kubeovn/dnsnameresolver/refs/heads/main/manifest/rbac.yaml
kubectl apply -f https://raw.githubusercontent.com/kubeovn/dnsnameresolver/refs/heads/main/manifest/cm.yaml
```

### 部署 CoreDNS 镜像

使用预构建的 DNSNameResolver 镜像更新 CoreDNS：

```bash
kubectl set image deployment/coredns coredns=kubeovn/dnsnameresolver:dev -n kube-system
```

确认 CoreDNS 是否正常启动：

```bash
kubectl get pod -n kube-system -l k8s-app=kube-dns
```

### 启用 ANP 功能

在 kube-ovn-controller 部署中添加相关参数：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube-ovn-controller
spec:
  template:
    spec:
      containers:
      - name: kube-ovn-controller
        args:
        - --enable-anp=true
        - --enable-dns-name-resolver=true
        # ... 其他参数
```

## 使用方式

### 基本配置

```yaml
apiVersion: policy.networking.k8s.io/v1alpha1
kind: AdminNetworkPolicy
metadata:
  name: deny-external-domains
spec:
  priority: 55
  subject:
    namespaces:
      matchLabels:
        kubernetes.io/metadata.name: kube-system
  egress:
  - action: Deny
    name: deny-baidu-google
    to:
    - domainNames:
      - '*.baidu.com.'
      - '*.google.com.'
```

字段说明：

| 字段 | 说明 |
| ------ | ------ |
| `priority` | 策略优先级，数值越小优先级越高 |
| `subject` | 策略应用的目标，支持按命名空间、Pod 标签等选择 |
| `egress` | 出口规则配置 |
| `action` | 执行动作，支持 `Allow`、`Deny`、`Pass` |
| `domainNames` | 目标域名列表，支持通配符，需要以 `.` 结尾 |

## 验证测试

使用 kube-ovn-pinger 测试连通性：

```bash
# 测试对被阻止域名的访问
kubectl exec -it -n kube-system kube-ovn-pinger-xxxxx -- ping baidu.com
```

> 注意：首次访问可能成功，因为 DNS 解析和 ACL 规则应用需要时间。

查看 DNSNameResolver 状态：

```bash
# kubectl get dnsnameresolver
NAME                                 DNS NAME        RESOLVED IPS
anp-deny-external-domains-88dc32ab   *.google.com.
anp-deny-external-domains-fb3029ce   *.baidu.com.    220.181.7.203
```
