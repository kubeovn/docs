# Domain-based Access Control

Kubernetes native NetworkPolicy only supports network access control through L3 and L4 protocols. Through [AdminNetworkPolicy (ANP)](https://network-policy-api.sigs.k8s.io/api-overview/), domain-level control of egress traffic can be achieved, allowing administrators to manage cluster Pod access to external services through domain names. This feature needs to be used in conjunction with the [DNSNameResolver](https://github.com/kubeovn/dnsnameresolver) CoreDNS plugin.

## Implementation Principles

Compared to native NetworkPolicy that can directly use AddressSet in OVN to record the IP list for access control, domain-based access control needs to dynamically convert domain names to IP addresses and add them to OVN's AddressSet to achieve DNS access control.

Implementation process:

1. kube-ovn-controller generates DNSNameResolver CR resources based on domain rule information in AdminNetworkPolicy.
2. During DNS resolution, CoreDNS matches against all DNSNameResolver CR resources. Once a resolution record matches, it updates the corresponding IP address information of the domain name to the DNSNameResolver status.
3. kube-ovn-controller updates the corresponding AddressSet based on the status information of DNSNameResolver CR resources.

## Usage Limitations

Since the mapping relationship between domain names and IPs is determined during resolution, there is a delay in rule effectiveness, which may cause the first access to succeed for Deny rules and the first access to fail for Allow rules. To avoid security leakage issues, we recommend using only Allow rules for domain-based access control, combined with default Deny rules, and applications should have retry mechanisms.

## Prerequisites

### Deploy ANP and BANP CRDs

First, deploy AdminNetworkPolicy related CRDs:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/network-policy-api/refs/heads/main/config/crd/experimental/policy.networking.k8s.io_adminnetworkpolicies.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/network-policy-api/refs/heads/main/config/crd/experimental/policy.networking.k8s.io_baselineadminnetworkpolicies.yaml
```

### Deploy DNSNameResolver Components

Deploy DNSNameResolver related resources:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubeovn/dnsnameresolver/refs/heads/main/manifest/crd.yaml
kubectl apply -f https://raw.githubusercontent.com/kubeovn/dnsnameresolver/refs/heads/main/manifest/rbac.yaml
kubectl apply -f https://raw.githubusercontent.com/kubeovn/dnsnameresolver/refs/heads/main/manifest/cm.yaml
```

### Deploy CoreDNS Image

Update CoreDNS with the pre-built DNSNameResolver image:

```bash
kubectl set image deployment/coredns coredns=kubeovn/dnsnameresolver:dev -n kube-system
```

Verify that CoreDNS is running properly:

```bash
kubectl get pod -n kube-system -l k8s-app=kube-dns
```

### Enable ANP Feature

Add the following parameters to the kube-ovn-controller deployment:

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
        # ... other parameters
```

## Usage

### Basic Configuration

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

Field Description:

| Field | Description |
| ------- | ------------- |
| `priority` | Policy priority, lower values have higher priority |
| `subject` | Policy target, supports selection by namespace, Pod labels, etc. |
| `egress` | Egress rule configuration |
| `action` | Action to execute, supports `Allow`, `Deny`, `Pass` |
| `domainNames` | Target domain name list, supports wildcards, must end with `.` |

## Verification Testing

Test connectivity using kube-ovn-pinger:

```bash
# Test access to blocked domains
kubectl exec -it -n kube-system kube-ovn-pinger-xxxxx -- ping baidu.com
```

> Note: The first access may succeed because DNS resolution and ACL rule application require time.

Check DNSNameResolver status:

```bash
# kubectl get dnsnameresolver
NAME                                 DNS NAME        RESOLVED IPS
anp-deny-external-domains-88dc32ab   *.google.com.
anp-deny-external-domains-fb3029ce   *.baidu.com.    220.181.7.203
```
