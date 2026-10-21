# Webhook 使用

使用 Webhook 可以对 Kube-OVN 内的核心资源与 CRD 进行准入校验（Validating Webhook）。目前 Webhook 覆盖了以下维度的严格校验与防护：

- **IP 与静态地址冲突校验**：拦截 Pod 静态 IP/MAC、IPPool 以及 IP CRD 的重复与冲突分配。
- **子网（Subnet）合法性校验**：检测子网 CIDR 重叠、网关与排除 IP 合法性，以及 VLAN/ProviderNetwork 绑定的有效性。
- **虚拟 IP（VIP）安全保护**：防止 VIP 冲突，保护被关联的子网免于误删除。
- **VPC 与 VPC NAT 网关关联校验**：校验 VPC 路由器端口、VpcNatGateway 的 LAN IP 与引流子网配置的合法性，防止错误配置导致转发中断。

由于 Webhook 会拦截所有的 Subnet 和 Pod 创建的请求，因此需要先部署 Kube-OVN
后部署 Webhook 避免无法创建 Pod。

## Cert-Manager 安装

Webhook 部署需要相关证书加密，我们使用 cert-manager 生成相关证书。部署 Webhook 前需先在集群中部署 cert-manager（建议使用 cert-manager 最新稳定版）：

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml
```

更多 cert-manager 使用请参考 [cert-manager 文档](https://cert-manager.io/docs/){: target = "_blank" }。

## 安装 Webhook

下载 Webhook 对应的 yaml 进行安装:

```bash
# kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/yamls/webhook.yaml
deployment.apps/kube-ovn-webhook created
service/kube-ovn-webhook created
validatingwebhookconfiguration.admissionregistration.k8s.io/kube-ovn-webhook created
certificate.cert-manager.io/kube-ovn-webhook-serving-cert created
issuer.cert-manager.io/kube-ovn-webhook-selfsigned-issuer created
```

## 验证 Webhook 生效

查看已运行 Pod，得到 Pod IP `10.16.0.15`：

```bash
# kubectl get pod -o wide
NAME                      READY   STATUS    RESTARTS   AGE     IP           NODE              NOMINATED NODE   READINESS GATES
static-7584848b74-fw9dm   1/1     Running   0          2d13h   10.16.0.15   kube-ovn-worker   <none> 
```

编写 yaml 创建相同 IP 的 Pod：

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/ip_address: 10.16.0.15
    ovn.kubernetes.io/mac_address: 00:00:00:53:6B:B6
  labels:
    app: static
  managedFields:
  name: staticip-pod
  namespace: default
spec:
  containers:
  - image: docker.io/library/nginx:alpine
    imagePullPolicy: IfNotPresent
    name: qatest
```

使用以上 yaml 创建静态地址 Pod 的时候，提示 IP 地址冲突：

```bash
# kubectl apply -f pod-static.yaml
Error from server (annotation static-ip 10.16.0.15 is conflict with ip crd static-7584848b74-fw9dm.default, ip 10.16.0.15): error when creating "pod-static.yaml": admission webhook "pod-ip-validating.kube-ovn.io" denied the request: annotation static-ip 10.16.0.15 is conflict with ip crd static-7584848b74-fw9dm.default, ip 10.16.0.15
```
