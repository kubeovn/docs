# Webhook 使用

使用 Webhook 可以对 Kube-OVN 内的 CRD 资源进行校验，目前 Webhook 主要完成
固定 IP 地址冲突检测和 Subnet CIDR 的冲突检测，并在这类资源创建冲突时提示错误。

由于 Webhook 会拦截所有的 Subnet 和 Pod 创建的请求，因此需要先部署 Kube-OVN
后部署 Webhook 避免无法创建 Pod。

## Cert-Manager 安装

Webhook 部署需要相关证书加密，我们使用 cert-manager 生成相关证书，我们需要在部署
Webhook 前先部署 cert-manager。

可以使用下面的命令来部署 cert-manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.8.0/cert-manager.yaml
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

对于新安装，请先创建 Certificate 并等待签发完成，再使用
`validatingWebhook.certificate.create: false` 启用 Webhook：

```bash
kubectl apply -f webhook-certificate.yaml
kubectl wait --for=condition=Ready certificate/kube-ovn-webhook-serving-cert \
  -n kube-system --timeout=120s
```

Secret 必须包含 `tls.crt` 和 `tls.key`，Webhook 才能提供 HTTPS 服务；
服务端进程本身不需要 `ca.crt`。另一方面，CA 注入组件使用外部 Certificate
填充 Webhook 的 CA 证书包。请确保 Certificate 的 Secret 在 `ca.crt` 中提供
注入组件所需的 CA 数据，以便 API server 验证服务端证书。
确认 Webhook Deployment 已就绪，且 CA 证书包不为空：

```bash
kubectl rollout status deployment/kube-ovn-webhook -n kube-system
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
