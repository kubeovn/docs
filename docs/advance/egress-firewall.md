# Egress Firewall

该功能基于 AdminNetworkPolicy (ANP) 实现出口流量的域名级别控制，允许管理员通过域名方式管理集群内 Pod 对外部服务的访问。

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
|------|------|
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
