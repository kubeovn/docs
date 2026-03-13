# SecurityGroup Usage

Kube-OVN supports security groups to control network access rules for a group of Pods.

!!! warning

    Kube-OVN supports four types of access control: [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/), [Network Policy API](https://network-policy-api.sigs.k8s.io/), [Subnet ACL](../guide/subnet.en.md#subnet-acl), and Security Group. All of these are implemented through OVN ACLs at the underlying level. Among them, NetworkPolicy and Network Policy API are designed with rule layering in mind, ensuring no priority conflicts. However, mixing other types of access control methods may lead to priority conflicts. We recommend avoiding the simultaneous use of multiple access control rules to prevent rule confusion caused by priority conflicts.

## SecurityGroup Example

```yaml
apiVersion: kubeovn.io/v1
kind: SecurityGroup
metadata:
  name: sg-example
spec:
  allowSameGroupTraffic: true
  egressRules:
  - ipVersion: ipv4
    policy: allow
    priority: 1
    protocol: all
    remoteAddress: 10.16.0.13 # 10.16.0.0/16 Configure network segment
    remoteType: address
  ingressRules:
  - ipVersion: ipv4
    policy: deny
    priority: 1
    protocol: icmp
    remoteAddress: 10.16.0.14
    remoteType: address
```

The specific meaning of each field of the SecurityGroup can be found in the [Kube-OVN API Reference](../reference/kube-ovn-api.en.md).

Pods bind security groups by adding the `ovn.kubernetes.io/security_groups` annotation:

```yaml
    ovn.kubernetes.io/security_groups: sg-example
```

For port security feature, please refer to the [Port Security documentation](../guide/port-security.en.md).

## Tiered Security Groups

Security groups support multi-tier ACL processing via the optional `tier` field. This allows you to stack multiple security groups to perform hierarchical ACL evaluation.

- **`tier`**: An integer value of `0` or `1` (default `0`). Rules in tier `0` are evaluated first. If a rule in tier `0` matches with `policy: pass`, ACL processing continues to tier `1`.
- **`policy: pass`**: A policy action (in addition to `allow` and `deny`) that forwards packet evaluation to the next tier instead of making a final decision. The `pass` policy cannot be used when the security group tier is set to the maximum value (`1`), since there is no subsequent tier to pass to.

This enables use cases such as a broad tier-0 security group that passes certain traffic to a more specific tier-1 security group for further filtering.

### Tiered SecurityGroup Example

Create two security groups, one for each tier:

```yaml
apiVersion: kubeovn.io/v1
kind: SecurityGroup
metadata:
  name: sg-tier0
spec:
  tier: 0
  allowSameGroupTraffic: true
  ingressRules:
  - ipVersion: ipv4
    policy: pass
    priority: 1
    protocol: tcp
    remoteAddress: 10.16.0.0/16
    remoteType: address
  - ipVersion: ipv4
    policy: deny
    priority: 2
    protocol: all
    remoteAddress: 0.0.0.0/0
    remoteType: address
---
apiVersion: kubeovn.io/v1
kind: SecurityGroup
metadata:
  name: sg-tier1
spec:
  tier: 1
  allowSameGroupTraffic: true
  ingressRules:
  - ipVersion: ipv4
    policy: allow
    priority: 1
    protocol: tcp
    remoteAddress: 10.16.0.0/16
    remoteType: address
    portRangeMin: 80
    portRangeMax: 443
```

In this example, `sg-tier0` passes all TCP traffic from `10.16.0.0/16` to tier 1 and denies everything else. `sg-tier1` then only allows TCP traffic on ports 80–443 from that same range.

To apply both security groups to a Pod, list them as a comma-separated value in the annotation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: web
  annotations:
    ovn.kubernetes.io/security_groups: 'sg-tier0,sg-tier1'
  name: multi-tier-pod
  namespace: default
spec:
  nodeName: kube-ovn-worker
  containers:
  - image: docker.io/library/nginx:alpine
    imagePullPolicy: IfNotPresent
    name: nginx
```

## Local Address and Source Port Filtering

Security group rules support optional `localAddress` and source port range fields for more granular matching:

- **`localAddress`**: A local IP address or CIDR to match against. This allows rules to apply only when the local (source for egress, destination for ingress) address matches.
- **`sourcePortRangeMin`** / **`sourcePortRangeMax`**: Define a source port range (1–65535) to match against. These are only applicable for TCP and UDP protocols.

### Local Address Filtering Example

```yaml
apiVersion: kubeovn.io/v1
kind: SecurityGroup
metadata:
  name: sg-local-filter
spec:
  allowSameGroupTraffic: true
  ingressRules:
  - ipVersion: ipv4
    policy: allow
    priority: 1
    protocol: tcp
    remoteAddress: 10.16.0.0/16
    remoteType: address
    portRangeMin: 8080
    portRangeMax: 8080
    localAddress: 10.16.0.100
    sourcePortRangeMin: 1024
    sourcePortRangeMax: 65535
```

This rule allows inbound TCP traffic to `10.16.0.100` on port 8080 from `10.16.0.0/16` with source ports in the range 1024–65535.

## Caution

- Security groups are implemented by setting ACL rules. As mentioned in the OVN documentation, if two ACL rules match with the same priority, it is uncertain which ACL will actually work. Therefore, when setting up security group rules, you need to be careful to differentiate the priority.
- When configuring a security group, the `priority` value ranges from 1 to 16384, with smaller values indicating higher priority. When implementing a security group through ACLs, the security group's priority is mapped to the ACL priority. Therefore, it is essential to distinguish between the priorities of security groups and subnet ACLs.
- The `tier` field accepts values `0` or `1`. The `policy: pass` action is only valid in tier `0`; using it in tier `1` will result in a validation error.
- When adding a security group, it is important to know what restrictions are being added. As a CNI, Kube-OVN will perform a Pod-to-Gateway connectivity test after creating a Pod. If the gateway is not accessible, the Pod will remain in the ContainerCreating state and cannot switch to Running state.

## Actual test

Create a Pod using the following YAML, and specify the security group in the annotation for the pod.

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: static
  annotations:
    ovn.kubernetes.io/security_groups: 'sg-example'
  name: sg-test-pod
  namespace: default
spec:
  nodeName: kube-ovn-worker
  containers:
  - image: docker.io/library/nginx:alpine
    imagePullPolicy: IfNotPresent
    name: qatest
```

The actual test results show as follows:

```bash
# kubectl get pod -o wide
NAME READY STATUS RESTARTS AGE IP NODE NOMINATED NODE READINESS GATES
sg-test-pod 0/1 ContainerCreating 0 5h32m <none> kube-ovn-worker <none> <none>
test-99fff7f86-52h9r 1/1 Running 0 5h41m 10.16.0.14 kube-ovn-control-plane <none> <none>
test-99fff7f86-qcgjw 1/1 Running 0 5h43m 10.16.0.13 kube-ovn-worker <none> <none>
```

Execute `kubectl describe pod` to see information about the pod, and you can see the error message:

```bash
# kubectl describe pod sg-test-pod
Name: sg-test-pod
Namespace: default
Priority: 0
Node: kube-ovn-worker/172.18.0.2
Start Time: Tue, 28 Feb 2023 10:29:36 +0800
Labels: app=static
Annotations: ovn.kubernetes.io/allocated: true
              ovn.kubernetes.io/cidr: 10.16.0.0/16
              ovn.kubernetes.io/gateway: 10.16.0.1
              ovn.kubernetes.io/ip_address: 10.16.0.15
              ovn.kubernetes.io/logical_router: ovn-cluster
              ovn.kubernetes.io/logical_switch: ovn-default
              ovn.kubernetes.io/mac_address: 00:00:00:FA:17:97
              ovn.kubernetes.io/pod_nic_type: veth-pair
              ovn.kubernetes.io/port_security: true
              ovn.kubernetes.io/routed: true
              ovn.kubernetes.io/security_groups: sg-allow-reject
Status: Pending
IP:
IPs: <none>
-
- -
- -
Events:
  Type Reason Age From Message
  ---- ------ ---- ---- -------
  Warning FailedCreatePodSandBox 5m3s (x70 over 4h59m) kubelet (combined from similar events): Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox "40636e0c7f1ade5500fa958486163d74f2e2300051a71522a9afd7ba0538afb6": plugin type="kube-ovn" failed ( add): RPC failed; request ip return 500 configure nic failed 10.16.0.15 network not ready after 200 ping 10.16.0.1
```

Modify the rules for the security group to add access rules to the gateway, refer to the following:

```yaml
apiVersion: kubeovn.io/v1
kind: SecurityGroup
metadata:
  name: sg-gw-both
spec:
  allowSameGroupTraffic: true
  egressRules:
  - ipVersion: ipv4
    policy: allow
    priority: 2
    protocol: all
    remoteAddress: 10.16.0.13
    remoteType: address
  - ipVersion: ipv4
    policy: allow
    priority: 1
    protocol: all
    remoteAddress: 10.16.0.1
    remoteType: address
  ingressRules:
  - ipVersion: ipv4
    policy: deny
    priority: 2
    protocol: icmp
    remoteAddress: 10.16.0.14
    remoteType: address
  - ipVersion: ipv4
    policy: allow
    priority: 1
    protocol: icmp
    remoteAddress: 10.16.0.1
    remoteType: address
```

In the inbound and outbound rules respectively, add a rule to allow access to the gateway, and set the rule to have the highest priority.

Deploying with the following yaml to bind security group, confirm that the Pod is operational:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: static
  annotations:
    ovn.kubernetes.io/security_groups: 'sg-gw-both'
  name: sg-gw-both
  namespace: default
spec:
  nodeName: kube-ovn-worker
  containers:
  - image: docker.io/library/nginx:alpine
    imagePullPolicy: IfNotPresent
    name: qatest
```

To view Pod information after deployment:

```bash
# kubectl get pod -o wide
NAME READY STATUS RESTARTS AGE IP NODE NOMINATED NODE READINESS GATES
sg-test-pod 0/1 ContainerCreating 0 5h41m <none> kube-ovn-worker <none> <none>
sg-gw-both 1/1 Running 0 5h37m 10.16.0.19 kube-ovn-worker <none> <none>
```

So for the use of security groups, be particularly clear about the effect of the added restriction rules. If it is simply to restrict traffic access, consider using a network policy instead.
