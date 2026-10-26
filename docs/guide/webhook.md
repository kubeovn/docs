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

## 使用 v2 Helm Chart 管理证书

本节适用于提供 `validatingWebhook.certificate.create` 配置项的 `kube-ovn-v2` Helm Chart，
不改变上文通过清单安装的方式。

当 `validatingWebhook.enabled` 为 `true` 时，Chart 默认创建 cert-manager Certificate
和自签名 Issuer。布尔配置项 `validatingWebhook.certificate.create` 的默认值为 `true`。
将其设置为 `false`，可以在 Chart 外部管理 Certificate，同时保留 Webhook 的
Deployment、Service 和 ValidatingWebhookConfiguration：

```yaml
validatingWebhook:
  enabled: true
  certificate:
    create: false
```

当 `validatingWebhook.enabled` 为 `false` 时，无论 `validatingWebhook.certificate.create`
的值是什么，都不会部署任何 Webhook 资源。

### 提供外部 Certificate

启用 Webhook 前，请安装 cert-manager 及其 CA 注入组件，并确保集群网络正常。
此配置项不会移除对 cert-manager 的依赖。
请在 Certificate 所在的命名空间中创建 Issuer，或使用已有的 ClusterIssuer。

通过父 Chart 或 GitOps 等方式单独管理替代的 Certificate。
Certificate 和 Secret 的名称必须与 Chart 中已有的引用一致：

| 资源 | 必需名称 | 用途 |
| --- | --- | --- |
| Certificate | `kube-ovn-webhook-serving-cert` | 由 Webhook 的 `cert-manager.io/inject-ca-from` 注解引用。 |
| Secret | `kube-ovn-webhook-secret` | 由 Webhook Deployment 挂载，提供服务端证书和私钥。 |

这两个资源必须位于 Chart 的 `namespace` 配置项指定的命名空间中。
当命名空间为默认值 `kube-system`，且 `clusterDomain` 为默认值 `cluster.local` 时，
将以下内容保存为 `webhook-certificate.yaml`：

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: kube-ovn-webhook-serving-cert
  namespace: kube-system
spec:
  secretName: kube-ovn-webhook-secret
  dnsNames:
    - kube-ovn-webhook.kube-system
    - kube-ovn-webhook.kube-system.svc
    - kube-ovn-webhook.kube-system.svc.cluster.local
  issuerRef:
    group: cert-manager.io
    kind: Issuer
    name: existing-webhook-issuer
```

将 `existing-webhook-issuer` 替换为实际的签发者名称。
如果使用 ClusterIssuer，还需将 `issuerRef.kind` 改为 `ClusterIssuer`。
根据 Chart 配置调整命名空间和 DNS 名称，并按证书策略添加有效期、续期、
私钥、主题和用途等字段。

请将下方命令中的 `<chart-namespace>` 替换为 Chart 配置的 `namespace` 值。
该值必须与 `webhook-certificate.yaml` 中的 `metadata.namespace` 一致。

对于新安装，请先创建 Certificate 并等待签发完成，再使用
`validatingWebhook.certificate.create: false` 启用 Webhook：

```bash
kubectl apply -f webhook-certificate.yaml
kubectl wait --for=condition=Ready certificate/kube-ovn-webhook-serving-cert \
  -n "<chart-namespace>" --timeout=120s
```

Webhook 需要 `kube-ovn-webhook-secret` 中的 `tls.crt` 和 `tls.key` 才能提供
HTTPS 服务。服务端进程不需要 `ca.crt`。

cert-manager 的 CA 注入组件通过 Webhook 的 `cert-manager.io/inject-ca-from`
注解找到名为 `kube-ovn-webhook-serving-cert` 的 Certificate。
该组件将 Certificate 关联的 Secret 中的 `ca.crt` 复制到 Webhook 的 `caBundle`，
API server 使用该 CA 证书包验证 Webhook 的服务端证书。

确认 Webhook Deployment 已就绪，且 CA 证书包不为空：

```bash
kubectl rollout status deployment/kube-ovn-webhook -n "<chart-namespace>"
kubectl get validatingwebhookconfiguration kube-ovn-webhook \
  -o jsonpath='{.webhooks[0].clientConfig.caBundle}'
```

### 迁移已有安装

禁用 Chart 管理的证书创建功能前，请先规划 Certificate 的所有权转移。
Helm 升级时会删除此前由其管理的 Certificate 和自签名 Issuer。
仅应用同名的 Certificate 不会转移其所有权。
Secret 是否被删除还取决于 cert-manager 的 Certificate 所有者引用配置。
更改 Helm 配置前，请安排迁移方案，确保证书持续可用，
并建立对替代 Certificate 的独立管理。

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
