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

More cert-manager usage please refer to [cert-manager document](https://cert-manager.io/docs/){: target = "_blank" }.

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
Error from server (annotation ip address 10.16.0.15 is conflict with IP CRD static-7584848b74-fw9dm.default 10.16.0.15): error when creating "pod-static.yaml": admission webhook "pod-ip-validaing.kube-ovn.io" denied the request: annotation ip address 10.16.0.15 is conflict with IP CRD static-7584848b74-fw9dm.default 10.16.0.15
```
