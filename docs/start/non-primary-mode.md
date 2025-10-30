# 附属 CNI 模式

本文档介绍如何将 Kube-OVN 作为附属 CNI 与其他主 CNI 插件（如 Cilium、Calico 或 Flannel）一起使用。

## 概述

在非主 CNI 模式下，Kube-OVN 作为辅助 CNI 插件，为 Pod 提供额外的网络接口，而另一个 CNI 处理主网络接口（eth0）。这样可以：

- 在现有 CNI 基础上使用 Kube-OVN 的高级网络功能（VPC、子网、安全组）
- 实现网络分段和多租户
- 为 Pod 提供多个网络接口以实现不同用途
- 利用 Kube-OVN 的 VPC NAT 网关功能为次要网络提供外部连接

## 前置要求

### 必需组件

1. **主 CNI**：任何与 Kubernetes 兼容的 CNI（Cilium、Calico、Flannel 等）
2. **Multus CNI**：多网络支持所必需
3. **Kube-OVN**：配置为非主模式

### 安装顺序

1. 安装并配置主 CNI
2. 安装 Multus CNI
3. 以非主模式安装 Kube-OVN

## 安装

### 使用 Helm Chart v2

```yaml
# values.yaml
cni:
  nonPrimaryCNI: true
```

使用 Helm 安装：

```bash
helm install kube-ovn ./charts/kube-ovn-v2 \
  --namespace kube-system \
  --set cni.nonPrimaryCNI=true
```

### 使用 Helm Chart v1

```yaml
# values.yaml
cni_conf:
  NON_PRIMARY_CNI: true
```

使用 Helm 安装：

```bash
helm install kube-ovn ./charts/kube-ovn \
  --namespace kube-system \
  --set cni_conf.NON_PRIMARY_CNI=true
```

### 手动安装

在 kube-ovn-controller deployment 中添加以下标志：

```yaml
containers:
- name: kube-ovn-controller
  args:
  - --non-primary-cni-mode=true
```

## 配置

### 网络附件定义（NADs）

创建 NAD 以定义额外的网络接口：

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: kube-ovn-vpc-network
  namespace: default
spec:
  config: |
    {
      "cniVersion": "0.3.1",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "kube-ovn-vpc-network.default.ovn"
    }
```

### VPC 和子网配置

为次要网络创建 VPC 和子网资源：

```yaml
apiVersion: kubeovn.io/v1
kind: Vpc
metadata:
  name: vpc-secondary
spec:
  namespaces:
  - default
---
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: subnet-secondary
spec:
  vpc: vpc-secondary
  cidr: "10.100.0.0/16"
  gateway: "10.100.0.1"
  provider: kube-ovn-vpc-network.default.ovn
```

### Pod 配置

为 Pod 添加注解以请求额外的网络接口：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-network-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: default/kube-ovn-vpc-network
spec:
  containers:
  - name: app
    image: nginx
```

## 网络接口行为

### 主接口（eth0）

- 由主 CNI（Cilium、Calico 等）管理
- 用于集群网络、服务发现和默认路由
- 提供与 Kubernetes 服务和外部网络的连接

### 次要接口（net1、net2...）

- 由 Kube-OVN 管理
- 提供额外的网络连接
- 可以连接到不同的 VPC 和子网
- 支持 Kube-OVN 功能，如安全组、QoS 和 NAT

## 使用场景

### 1. 网络分段

将不同类型的流量分离到不同的网络接口：

```yaml
# 前端 Pod 可同时访问公共网络和内部网络
apiVersion: v1
kind: Pod
metadata:
  name: frontend
  annotations:
    k8s.v1.cni.cncf.io/networks: |
      [
        {"name": "default/public-network"},
        {"name": "default/internal-network"}
      ]
```

### 2. 多租户

提供租户特定的网络：

```yaml
# 租户 A Pod
apiVersion: v1
kind: Pod
metadata:
  name: tenant-a-app
  annotations:
    k8s.v1.cni.cncf.io/networks: default/tenant-a-network

---
# 租户 B Pod  
apiVersion: v1
kind: Pod
metadata:
  name: tenant-b-app
  annotations:
    k8s.v1.cni.cncf.io/networks: default/tenant-b-network
```

### 3. VPC NAT 网关

为次要网络启用外部连接：

```yaml
apiVersion: kubeovn.io/v1
kind: VpcNatGateway
metadata:
  name: vpc-nat-gw
spec:
  vpc: vpc-secondary
  subnet: subnet-secondary
  lanIp: "10.100.0.254"
```

## 高级功能

### 多个网络提供者

Pod 可以拥有来自多个提供者的接口：

```yaml
metadata:
  annotations:
    k8s.v1.cni.cncf.io/networks: |
      [
        {"name": "default/kube-ovn-network-1", "interface": "net1"},
        {"name": "default/kube-ovn-network-2", "interface": "net2"}
      ]
```

### IP 地址分配

控制次要接口的 IP 分配：

```yaml
# 静态 IP 分配
metadata:
  annotations:
    k8s.v1.cni.cncf.io/networks: |
      [{
        "name": "default/kube-ovn-network",
        "ips": ["10.100.0.100/16"]
      }]
```

### 服务质量（QoS）

对次要接口应用 QoS 策略：

```yaml
metadata:
  annotations:
    ovn.kubernetes.io/ingress_rate: "1000"
    ovn.kubernetes.io/egress_rate: "1000"
```

## 故障排查

### 常见问题

1. **Pod 无法获取次要接口**
   - 验证 NAD 是否在正确的命名空间中创建
   - 检查 kube-ovn-cni 日志中的错误
   - 确保 Multus 已正确安装

2. **次要接口无连接**
   - 验证子网和 VPC 配置
   - 检查 Pod 中的路由表
   - 确保安全组规则允许流量

3. **IP 地址冲突**
   - 验证子网 CIDR 范围不重叠
   - 检查静态 IP 冲突
   - 查看 IPAM 配置

### 调试命令

```bash
# 检查 Pod 网络状态
kubectl get pod <pod-name> -o yaml | grep -A 10 "networks-status"

# 查看 Pod 中的网络接口
kubectl exec <pod-name> -- ip addr show

# 检查路由表
kubectl exec <pod-name> -- ip route show

# 调试 kube-ovn-cni
kubectl logs -n kube-system daemonset/kube-ovn-cni
```

## 限制

1. **服务发现**：次要网络不参与 Kubernetes 服务发现
2. **网络策略**：Kubernetes NetworkPolicy 仅适用于主接口
3. **负载均衡**：服务负载均衡通常仅在主接口上工作
4. **DNS**：Pod DNS 解析通过主接口进行

## 最佳实践

1. **网络规划**：仔细规划网络拓扑以避免 IP 冲突
2. **资源管理**：监控资源使用情况，因为每个接口都会消耗额外的资源
3. **安全**：对次要网络应用适当的安全组规则
4. **文档**：记录网络架构和接口用途
5. **测试**：彻底测试不同网络段之间的连接性

## 参考

- [Multus CNI 文档](https://github.com/k8snetworkplumbingwg/multus-cni)
- [网络附件定义规范](https://github.com/k8snetworkplumbingwg/multi-net-spec)
- [Kube-OVN 架构](https://kubeovn.github.io/docs/stable/en/reference/architecture/)
