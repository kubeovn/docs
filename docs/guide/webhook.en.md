# Webhook

Using Webhook, you can perform admission validation (Validating Webhook) for core Kube-OVN resources and CRDs. Currently, Webhook covers comprehensive validation across the following dimensions:

- **IP and Static Address Conflict Validation**: Intercept duplicate and conflicting assignments for Pod static IP/MAC, IPPools, and IP CRDs.
- **Subnet Validity Validation**: Detect Subnet CIDR overlaps, gateway and excluded IP validity, and VLAN/ProviderNetwork binding integrity.
- **Virtual IP (VIP) Safety Protection**: Prevent VIP conflicts and protect associated subnets from accidental deletion.
- **VPC and VPC NAT Gateway Association Validation**: Validate VPC router ports, VpcNatGateway LAN IPs, and internal routed subnets to prevent routing disruptions caused by misconfigurations.

Since Webhook intercepts all Subnet and Pod creation requests,
you need to deploy Kube-OVN first and Webhook later.

## Install Cert-Manager

Webhook deployment requires certificates; we use cert-manager to generate the required certificates. You need to deploy cert-manager before deploying Webhook (latest stable release recommended):

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml
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
