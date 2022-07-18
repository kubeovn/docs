# Cilium NetworkPolicy 支持

Kube-OVN 当前已经支持与 Cilium 集成，具体操作可以参考 [Cilium集成](with-cilium.md)

在集成 Cilium 之后，就可以使用 Cilium 优秀的网络策略能力，实现对流量访问的控制。以下文档提供了对 Cilium L3 和 L4 网络策略能力的集成验证。

## 验证步骤
### 创建测试 Pod
创建 namespace `test`。参考以下 yaml，在 test namespace 中创建指定 label `app=test` 的 Pod，作为测试访问的目的 Pod。
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
      - image: qaimages:helloworld
        imagePullPolicy: IfNotPresent
        name: qaimages
```

同样参考以下 yaml，在 default namespace 下创建指定 label `app=dynamic` 的 Pod 为发起访问测试的 Pod。
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
      - image: qaimages:helloworld
        imagePullPolicy: IfNotPresent
        name: qaimages
```

查看测试 Pod 以及 Label 信息:
```bash
apple@bogon cilium % kubectl get pod -o wide --show-labels
NAME                         READY   STATUS    RESTARTS   AGE   IP           NODE                     NOMINATED NODE   READINESS GATES   LABELS
dynamic-7d8d7874f5-9v5c4     1/1     Running   0          28h   10.16.0.35   kube-ovn-worker          <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
dynamic-7d8d7874f5-s8z2n     1/1     Running   0          28h   10.16.0.36   kube-ovn-control-plane   <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
apple@bogon cilium %
apple@bogon cilium % kubectl get pod -o wide -n test --show-labels
NAME                           READY   STATUS    RESTARTS   AGE     IP           NODE                     NOMINATED NODE   READINESS GATES   LABELS
dynamic-7d8d7874f5-6dsg6       1/1     Running   0          7h20m   10.16.0.2    kube-ovn-control-plane   <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
dynamic-7d8d7874f5-tjgtp       1/1     Running   0          7h46m   10.16.0.42   kube-ovn-worker          <none>           <none>            app=dynamic,pod-template-hash=7d8d7874f5
label-test1-77b6764857-swq4k   1/1     Running   0          3h43m   10.16.0.12   kube-ovn-worker          <none>           <none>            app=test1,pod-template-hash=77b6764857

// 以下为测试访问目的 Pod
test-54c98bc466-mft5s          1/1     Running   0          8h      10.16.0.41   kube-ovn-worker          <none>           <none>            app=test,pod-template-hash=54c98bc466
apple@bogon cilium %
```

### L3 网络策略测试
参考以下 yaml，创建 `CiliumNetworkPolicy` 资源:
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

在 default namespace 下的测试 Pod 中，发起对目的 Pod 的访问，结果访问不通。
但是在 test namespace 下，测试到目录 Pod 的访问，测试正常。

default namespace 下测试结果
```bash
apple@bogon ovn-test % kubectl exec -it dynamic-7d8d7874f5-9v5c4 -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss
bash-5.0#
```

test namepsace 下 Pod 的访问，访问正常
```bash
apple@bogon cilium % kubectl exec -it -n test dynamic-7d8d7874f5-6dsg6 -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes
64 bytes from 10.16.0.41: seq=0 ttl=64 time=2.558 ms
64 bytes from 10.16.0.41: seq=1 ttl=64 time=0.223 ms
64 bytes from 10.16.0.41: seq=2 ttl=64 time=0.304 ms

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.223/1.028/2.558 ms
bash-5.0#
apple@bogon ovn-test %
```

查看 Cilium 官方文档解释，`CiliumNetworkPolicy` 资源将限制控制在了 `Namespace` 级别。详细信息可以查看 [Cilium 限制](https://docs.cilium.io/en/stable/policy/kubernetes/)。

在有网络策略规则匹配的情况下，只有`同一个 Namespace` 的 Pod ，才可以按照规则进行访问，默认拒绝`其他 Namespace` 的 Pod 进行访问。

如果想实现跨 Namespace 的访问，需要在规则中明确指定 Namespace 信息。

参考文档，修改 `CiliumNetworkPolicy` 资源，增加 namespace 信息:
```yaml
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: dynamic
        k8s:io.kubernetes.pod.namespace: default    // 控制其他 Namespace 下的 Pod 访问
```
查看修改后的 `CiliumNetworkPolicy` 资源信息:
```bash
apple@bogon cilium % kubectl get cnp -n test  -o yaml l3-rule
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
apple@bogon cilium %
```

再次测试 default namespace 下的 Pod 访问，目的 Pod 访问正常:
```bash
apple@bogon ovn-test % kubectl exec -it dynamic-7d8d7874f5-9v5c4 -n test -- bash
bash-5.0# ping -c 3 10.16.0.41
PING 10.16.0.41 (10.16.0.41): 56 data bytes
64 bytes from 10.16.0.41: seq=0 ttl=64 time=2.383 ms
64 bytes from 10.16.0.41: seq=1 ttl=64 time=0.115 ms
64 bytes from 10.16.0.41: seq=2 ttl=64 time=0.142 ms

--- 10.16.0.41 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.115/0.880/2.383 ms
bash-5.0#
```

使用标准的 k8s 网络策略 [networkpolicy](https://kubernetes.io/zh-cn/docs/concepts/services-networking/network-policies/)，测试结果显示 Cilium 同样将访问限制在同一个 Namespace 内，跨 Namespace 的访问是禁止的。

这点与 Kube-OVN 实现是不同的。Kube-OVN 支持标准的 k8s 网络策略，限制了具体 Namespace 下的`目的 Pod`，但是对源地址 Pod，是没有 Namespace 限制的，任何 Namespace 下符合限制规则的 Pod，都可以实现对目的 Pod 的访问。

### L4 网络策略测试
参考以下yaml，创建 L4 层的网络策略资源:
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

测试相同 Namespace 下，符合网络策略规则的 Pod 的访问
```bash
apple@bogon cilium % kubectl exec -it -n test dynamic-7d8d7874f5-6dsg6 -- bash
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
bash-5.0#
```

相同 Namespace 下，不符合网络策略规则的 Pod 访问测试
```bash
apple@bogon cilium % kubectl exec -it -n test label-test1-77b6764857-swq4k -- bash
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
bash-5.0#
```

网络策略生效后，跨 Namespace 的访问，依然是被禁止的，跟 L3 网络策略测试结果一致。

在 L4 网络规则生效后，ping 无法使用，但是符合策略规则的 TCP 访问，是可以正常执行的。

关于 ICMP 的限制，可以参考官方说明 [L4 限制说明](https://docs.cilium.io/en/stable/policy/language/#layer-4-examples)。

### L7 网络策略测试
chaining 模式下，L7 网络策略目前是存在问题的。在 cilium 官方文档中，对这种情况给出了说明，参考 [Generic Veth Chaining](https://docs.cilium.io/en/stable/gettingstarted/cni-chaining-generic-veth/)。

这个问题使用 [issue 12454](https://github.com/cilium/cilium/issues/12454) 跟踪，目前还没有解决。