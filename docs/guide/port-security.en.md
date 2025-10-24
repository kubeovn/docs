# Port Security

Port security is used to prevent Pods from performing source address spoofing attacks. When port security is enabled, Pods can only send network packets using the MAC address and IP address assigned by Kube-OVN IPAM. Any packets using unauthorized addresses will be intercepted. This is very useful in multi-tenant environments or scenarios requiring strict network security policies.

Typical use cases include:

- Preventing malicious Pods from spoofing source IP addresses to launch attacks
- Preventing Pods from spoofing MAC addresses for ARP spoofing
- Meeting security isolation requirements in multi-tenant environments

## Implementation

Port security is implemented based on OVN's Port Security mechanism. When port security is enabled for a Pod, Kube-OVN configures the corresponding security policy on the OVN logical switch port:

- Sets the allowed MAC address list and IP address list on the logical switch port
- OVN checks the source MAC address and source IP address of all packets sent from that port
- Only packets with source addresses matching the IPAM-assigned addresses can pass through
- Non-matching packets are dropped directly by OVN

This mechanism is implemented at the OVN data plane level with minimal performance overhead and can effectively prevent various source address spoofing attacks.

## Usage

This feature is disabled by default and needs to be enabled by adding the `ovn.kubernetes.io/port_security` annotation to the Pod.

### Enable Port Security

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  annotations:
    ovn.kubernetes.io/port_security: "true"
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

