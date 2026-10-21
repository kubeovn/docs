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

Port security is disabled by default and can be enabled globally at the Subnet level or individually at the Pod level.

### Enable Port Security at Subnet Level

You can set `spec.portSecurity: true` when creating or updating a Subnet, enabling port security by default for all Pods created under that Subnet:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: secure-subnet
spec:
  cidrBlock: 10.16.0.0/16
  portSecurity: true
```

### Enable Port Security for Individual Pods

Enable port security for a single Pod by adding the `ovn.kubernetes.io/port_security` annotation:

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

For multi-NIC Pods added via Multus, use `<provider>.kubernetes.io/port_security: "true"` to enable port security on specific secondary interfaces.

### Allow Extra Addresses with AAP (e.g. Keepalived / VRRP)

When a Pod with port security enabled needs to send packets using additional floating IPs (VIPs), such as running Keepalived or VRRP, default port security drops the traffic. You can whitelist allowed extra IP/MAC addresses using the `ovn.kubernetes.io/aaps` (Additional Allowed Address Pairs) annotation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: vrrp-pod
  annotations:
    ovn.kubernetes.io/port_security: "true"
    ovn.kubernetes.io/aaps: "10.16.0.250"
spec:
  containers:
  - name: keepalived
    image: docker.io/library/nginx:alpine
```
