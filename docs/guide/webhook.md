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
  - image: nginx:alpine
    imagePullPolicy: IfNotPresent
    name: qatest
```

使用以上 yaml 创建静态地址 Pod 的时候，提示 IP 地址冲突：

```bash
# kubectl apply -f pod-static.yaml
Error from server (annotation ip address 10.16.0.15 is conflict with ip crd static-7584848b74-fw9dm.default 10.16.0.15): error when creating "pod-static.yaml": admission webhook "pod-ip-validaing.kube-ovn.io" denied the request: annotation ip address 10.16.0.15 is conflict with ip crd static-7584848b74-fw9dm.default 10.16.0.15
```
