# SecurityGroup Usage

Kube-OVN has support for the configuration of security-groups through the SecurityGroup CRD.

Kube-OVN also supports **port security** to prevent MAC and IP spoofing by allowing only L2/L3 source addresses matching the ones allocated by the IPAM.

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

Pods bind security-groups by adding annotations, two annotations are used:

- `port_security`: Source address verification. If this function is enabled, only packets with L2/L3 addresses assigned by Kube-OVN's IPAM can be exported from the pod network adapter. After this function is disabled, any L2/L3 address can be exported.

- security_groups: indicates a security group that contains a series of ACL rules
  
  - When configuring a security group, the `priority` value ranges from 1 to 200, with smaller values indicating higher priority. When implementing a security group through ACLs, the security group's priority is mapped to the ACL priority. The specific mapping relationship is as follows:
  ACL priority=2300−Security group priority，therefore, it is essential to distinguish between the priorities of security groups and subnet ACLs.

> These two annotations are responsible for functions that are independent of each other.

```yaml
    ovn.kubernetes.io/port_security: "true"
    ovn.kubernetes.io/security_groups: sg-example
```

## Caution

- Security-groups are finally restricted by setting ACL rules, and as mentioned in the OVN documentation, if two ACL rules match with the same priority, it is uncertain which ACL will actually work. Therefore, when setting up security-group rules, you need to be careful to differentiate the priority.

- When adding a security-group, it is important to know what restrictions are being added. As a CNI, Kube-OVN will perform a Pod-to-Gateway connectivity test after creating a Pod.

## Actual test

Create a Pod using the following YAML, and specify the security-group in the annotation for the pod.

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: static
  annotations:
    ovn.kubernetes.io/port_security: 'true'
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
    ovn.kubernetes.io/port_security: 'true'
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
