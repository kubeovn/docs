# Cilium NetworkPolicy Support

Kube-OVN currently supports integration with Cilium, and the specific operation can refer to [Cilium integration](with-cilium.md).

After integrating Cilium, you can use Cilium's excellent network policy capabilities to control the access of Pods in the cluster.The following documents provide integration verification of Cilium L3 and L4 network policy capabilities.

## Verification Steps

### Create test Pod

Create namespace `test`. Refer to the following yaml, create Pod with label `app=test` in namespace `test` as the destination Pod for testing access.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: test
  name: test
  namespace: test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - image: docker.io/library/nginx:alpine
        imagePullPolicy: IfNotPresent
        name: nginx
```

Similarly, refer to the following yaml, create Pod with label `app=dynamic` in namespace `default` as the Pod for testing access.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: dynamic
  name: dynamic
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dynamic
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: dynamic
    spec:
      containers:
      - image: docker.io/library/nginx:alpine
        imagePullPolicy: IfNotPresent
        name: nginx
```

View the test Pod and Label information:

```bash
# kubectl get pod -o wide --show-labels
NAME                         READY   STATUS    RESTARTS   AGE   IP           NODE                     NOMINATED NODE   READINESS GATES   LABELS
dynamic-7d8d7874f5-9v5c4     1/1     Running   0          28h   10.16.0.35   kube-ovn-worker          <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
dynamic-7d8d7874f5-s8z2n     1/1     Running   0          28h   10.16.0.36   kube-ovn-control-plane   <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
# kubectl get pod -o wide -n test --show-labels
NAME                           READY   STATUS    RESTARTS   AGE     IP           NODE                     NOMINATED NODE   READINESS GATES   LABELS
dynamic-7d8d7874f5-6dsg6       1/1     Running   0          7h20m   10.16.0.2    kube-ovn-control-plane   <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
dynamic-7d8d7874f5-tjgtp       1/1     Running   0          7h46m   10.16.0.42   kube-ovn-worker          <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
label-test1-77b6764857-swq4k   1/1     Running   0          3h43m   10.16.0.12   kube-ovn-worker          <none>           <none>            app=test1,pod-template-hash=77b6764857

// As the destination Pod for testing access.
test-54c98bc466-mft5s          1/1     Running   0          8h      10.16.0.41   kube-ovn-worker          <none>           <none>            app=test,pod-template-hash=54c98bc466
```

### L3 Network Policy Test

Refer to the following yaml, create `CiliumNetworkPolicy` resource:

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: "l3-rule"
  namespace: test
spec:
  endpointSelector:
    matchLabels:
      app: test
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: dynamic
```

At this point, the test Pod in the default namespace cannot access the destination Pod, but the test Pod to the destination Pod in the test namespace is accessible.

Test results in the default namespace:

```bash
# kubectl exec -it dynamic-7d8d7874f5-9v5c4 -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss
```

Test results in the test namespace:

```bash
# kubectl exec -it -n test dynamic-7d8d7874f5-6dsg6 -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes
64 bytes from 10.16.0.41: seq=0 ttl=64 time=2.558 ms
64 bytes from 10.16.0.41: seq=1 ttl=64 time=0.223 ms
64 bytes from 10.16.0.41: seq=2 ttl=64 time=0.304 ms

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.223/1.028/2.558 ms
```

Look at the Cilium official document explanation, the `CiliumNetworkPolicy` resource limits the control at the `namespace` level. For more information, please refer to [Cilium Limitations](https://docs.cilium.io/en/stable/policy/kubernetes/).

If there is a network policy rule match, only the Pod in the **same namespace** can access according to the rule, and the Pod in the **other namespace** is denied access by default.

If you want to implement cross-namespace access, you need to specify the namespace information in the rule.

Refer to the document, modify the `CiliumNetworkPolicy` resource, and add namespace information:

```yaml
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: dynamic
        k8s:io.kubernetes.pod.namespace: default    // control the Pod access in other namespace
        
```

Look at the modified `CiliumNetworkPolicy` resource information:

```bash
# kubectl get cnp -n test  -o yaml l3-rule
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: l3-rule
  namespace: test
spec:
  endpointSelector:
    matchLabels:
      app: test
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: dynamic
    - matchLabels:
        app: dynamic
        k8s:io.kubernetes.pod.namespace: default
```

Test the Pod access in the default namespace again, and the destination Pod access is normal:

```bash
# kubectl exec -it dynamic-7d8d7874f5-9v5c4 -n test -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes
64 bytes from 10.16.0.41: seq=0 ttl=64 time=2.383 ms
64 bytes from 10.16.0.41: seq=1 ttl=64 time=0.115 ms
64 bytes from 10.16.0.41: seq=2 ttl=64 time=0.142 ms

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.115/0.880/2.383 ms
```

Using the standard Kubernetes network policy [networkpolicy](https://kubernetes.io/zh-cn/docs/concepts/services-networking/network-policies/), the test results show that Cilium also restricts access within the same namespace, and cross-namespace access is prohibited.

It is different from Kube-OVN implementation. Kube-OVN supports standard k8s network policy, which restricts the **destination Pod** in a specific namespace, but there is no namespace restriction on the source Pod. Any Pod that meets the restriction rules in any namespace can access the destination Pod.

### L4 Network Policy Test

Refer to the following yaml, create `CiliumNetworkPolicy` resource:

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: "l4-rule"
  namespace: test
spec:
  endpointSelector:
    matchLabels:
      app: test
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: dynamic
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
```

Test the access of the Pod that meets the network policy rules in the same namespace

```bash
# kubectl exec -it -n test dynamic-7d8d7874f5-6dsg6 -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss
bash-5.0#
bash-5.0# curl 10.16.0.41:80
<html>
<head>
        <title>Hello World!</title>
        <link href='//fonts.googleapis.com/css?family=Open+Sans:400,700' rel='stylesheet' type='text/css'>
        <style>
        body {
                background-color: white;
                text-align: center;
                padding: 50px;
                font-family: "Open Sans","Helvetica Neue",Helvetica,Arial,sans-serif;
        }
        #logo {
                margin-bottom: 40px;
        }
        </style>
</head>
<body>
                <h1>Hello World!</h1>
                                <h3>Links found</h3>
        <h3>I am on  test-54c98bc466-mft5s</h3>
        <h3>Cookie                  =</h3>
                                        <b>KUBERNETES</b> listening in 443 available at tcp://10.96.0.1:443<br />
                                                <h3>my name is hanhouchao!</h3>
                        <h3> RequestURI='/'</h3>
</body>
</html>
```

The Pod that does not meet the network policy rules in the same namespace cannot access

```bash
# kubectl exec -it -n test label-test1-77b6764857-swq4k -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss
bash-5.0#
bash-5.0# curl -v 10.16.0.41:80 --connect-timeout 10
*   Trying 10.16.0.41:80...
* After 10000ms connect time, move on!
* connect to 10.16.0.41 port 80 failed: Operation timed out
* Connection timeout after 10001 ms
* Closing connection 0
curl: (28) Connection timeout after 10001 ms
```

After the network policy takes effect, cross-namespace access is still prohibited, which is consistent with the L3 network policy test results.

After the L4 network policy takes effect, ping cannot be used, but TCP access that meets the policy rules can be executed normally.

About the restriction of ICMP, please refer to the official description [L4 Limitation Description](https://docs.cilium.io/en/stable/policy/language/#layer-4-examples).

### L7 Network Policy Test

chaining mode, L7 network policy currently has problems. In the Cilium official document, there is an explanation for this situation, please refer to [Generic Veth Chaining](https://docs.cilium.io/en/stable/gettingstarted/cni-chaining-generic-veth/).

This problem is tracked using [issue 12454](https://github.com/cilium/cilium/issues/12454), and it has not been resolved yet.
