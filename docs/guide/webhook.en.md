# Webhook

Using Webhook, you can verify CRD resources within Kube-OVN. Currently,
Webhook mainly performs fixed IP address conflict detection and Subnet CIDR conflict detection,
and prompts errors when such conflicts happen.

Since Webhook intercepts all Subnet and Pod creation requests,
you need to deploy Kube-OVN first and Webhook later.

## Install Cert-Manager

Webhook deployment requires certificate, we use cert-manager to generate the associated certificate,
we need to deploy cert-manager before deploying Webhook.

You can use the following command to deploy cert-manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.8.0/cert-manager.yaml
```

For more cert-manager usage, please refer to [cert-manager document](https://cert-manager.io/docs/){: target="_blank" }.

## Install Webhook

Download Webhook yaml and install:

```bash
# kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/yamls/webhook.yaml
deployment.apps/kube-ovn-webhook created
service/kube-ovn-webhook created
validatingwebhookconfiguration.admissionregistration.k8s.io/kube-ovn-webhook created
certificate.cert-manager.io/kube-ovn-webhook-serving-cert created
issuer.cert-manager.io/kube-ovn-webhook-selfsigned-issuer created
```

## Manage Certificates with the v2 Helm Chart

This section applies to versions of the `kube-ovn-v2` Helm chart that provide
`validatingWebhook.certificate.create`. It does not change the manifest installation above.

When `validatingWebhook.enabled` is `true`, the chart creates a cert-manager Certificate
and self-signed Issuer by default. The Boolean `validatingWebhook.certificate.create` defaults to `true`.
Set it to `false` to manage the Certificate outside the chart while retaining the webhook
Deployment, Service, and ValidatingWebhookConfiguration:

```yaml
validatingWebhook:
  enabled: true
  certificate:
    create: false
```

Setting `validatingWebhook.enabled` to `false` disables all webhook resources,
regardless of `validatingWebhook.certificate.create`.

### Supply an External Certificate

Install cert-manager, including its CA injector, and ensure the cluster networking is working
before enabling the webhook. The setting does not remove the cert-manager dependency.
Create an Issuer in the Certificate namespace, or use an existing ClusterIssuer.

Manage the replacement Certificate separately, for example in a parent chart or through GitOps.
The Certificate and Secret names must match the chart's existing references:

| Resource | Required name | Purpose |
| --- | --- | --- |
| Certificate | `kube-ovn-webhook-serving-cert` | Referenced by the webhook's `cert-manager.io/inject-ca-from` annotation. |
| Secret | `kube-ovn-webhook-secret` | Mounted by the webhook Deployment for its serving certificate and private key. |

Both resources must be in the namespace configured by the chart's `namespace` value.
For the default namespace `kube-system` and `clusterDomain` value `cluster.local`,
save the following as `webhook-certificate.yaml`:

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

Replace `existing-webhook-issuer` with your issuer name. For a ClusterIssuer, also change
`issuerRef.kind` to `ClusterIssuer`. Adjust the namespace and DNS names to match your chart values.
Add any certificate lifetime, renewal, private key, subject, and usage fields required by your policy.

Replace `<chart-namespace>` in the commands below with the chart's configured `namespace` value.
It must match `metadata.namespace` in `webhook-certificate.yaml`.

For a new installation, apply the Certificate and wait for issuance before enabling the webhook
with `validatingWebhook.certificate.create: false`:

```bash
kubectl apply -f webhook-certificate.yaml
kubectl wait --for=condition=Ready certificate/kube-ovn-webhook-serving-cert \
  -n "<chart-namespace>" --timeout=120s
```

The webhook requires `tls.crt` and `tls.key` in `kube-ovn-webhook-secret`
to serve HTTPS. The serving process does not require `ca.crt`.

cert-manager's CA injector uses the webhook's `cert-manager.io/inject-ca-from`
annotation to locate the Certificate named `kube-ovn-webhook-serving-cert`.
It copies `ca.crt` from that Certificate's backing Secret into the webhook's
`caBundle`, which the API server uses to verify the webhook's serving certificate.

Verify that the webhook Deployment is ready and that the CA bundle is populated:

```bash
kubectl rollout status deployment/kube-ovn-webhook -n "<chart-namespace>"
kubectl get validatingwebhookconfiguration kube-ovn-webhook \
  -o jsonpath='{.webhooks[0].clientConfig.caBundle}'
```

### Migrate an Existing Installation

Plan the Certificate ownership transfer before disabling chart-managed certificate creation.
Helm removes its previously managed Certificate and self-signed Issuer on upgrade.
Applying a Certificate with the same name does not transfer its ownership.
Secret deletion also depends on cert-manager's Certificate owner-reference configuration.
Arrange a migration that preserves certificate availability and establishes separate management
of the replacement Certificate before changing the Helm value.

## Verify Webhook Take Effect

Check the running Pod and get the Pod IP `10.16.0.15`:

```bash
# kubectl get pod -o wide
NAME                      READY   STATUS    RESTARTS   AGE     IP           NODE              NOMINATED NODE   READINESS GATES
static-7584848b74-fw9dm   1/1     Running   0          2d13h   10.16.0.15   kube-ovn-worker   <none> 
```

Write yaml to create a Pod with the same IP:

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

When using the above YAML to create a fixed address Pod, it prompts an IP address conflict:

```bash
# kubectl apply -f pod-static.yaml
Error from server (annotation static-ip 10.16.0.15 is conflict with ip crd static-7584848b74-fw9dm.default, ip 10.16.0.15): error when creating "pod-static.yaml": admission webhook "pod-ip-validating.kube-ovn.io" denied the request: annotation static-ip 10.16.0.15 is conflict with ip crd static-7584848b74-fw9dm.default, ip 10.16.0.15
```
