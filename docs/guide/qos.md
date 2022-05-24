# 容器网络 QoS 配置

Kube-OVN 支持三种不同类型的 QoS

- 最大带宽限制 QoS
- linux-htb，基于优先级的 QoS
- linux-netem，模拟设备干扰丢包等的 QoS

其中 linux-htb 和 linux-netem 两种 QoS 无法同时生效，若两种 QoS 都配置到了同一个 Pod 上，
只有 linux-htb QoS 生效。

## 基于最大带宽限制的 QoS
该类型的 QoS 可以通过 Pod annotation 动态进行配置，可以在不中断 Pod 运行的情况下进行调整。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: qos
  namespace: ls1
  annotations:
    ovn.kubernetes.io/ingress_rate: "3"
    ovn.kubernetes.io/egress_rate: "1"
spec:
  containers:
  - name: qos
    image: nginx:alpine
```

### 动态调整 QoS

```bash
kubectl annotate --overwrite  pod nginx-74d5899f46-d7qkn ovn.kubernetes.io/ingress_rate=3
```

### 测试 QoS 调整

部署性能测试需要的容器
```yaml
kind: DaemonSet
apiVersion: apps/v1
metadata:
  name: perf
  namespace: ls1
  labels:
    app: perf
spec:
  selector:
    matchLabels:
      app: perf
  template:
    metadata:
      labels:
        app: perf
    spec:
      containers:
      - name: nginx
        image: kubeovn/perf
```

进入其中一个 Pod 并开启 iperf3 server

```bash
[root@node2 ~]# kubectl exec -it perf-4n4gt -n ls1 sh
/ # iperf3 -s
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------

```

进入另一个 Pod 请求之前的 Pod
```bash
[root@node2 ~]# kubectl exec -it perf-d4mqc -n ls1 sh
/ # iperf3 -c 10.66.0.12
Connecting to host 10.66.0.12, port 5201
[  4] local 10.66.0.14 port 51544 connected to 10.66.0.12 port 5201
[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd
[  4]   0.00-1.00   sec  86.4 MBytes   725 Mbits/sec    3    350 KBytes
[  4]   1.00-2.00   sec  89.9 MBytes   754 Mbits/sec  118    473 KBytes
[  4]   2.00-3.00   sec   101 MBytes   848 Mbits/sec  184    586 KBytes
[  4]   3.00-4.00   sec   104 MBytes   875 Mbits/sec  217    671 KBytes
[  4]   4.00-5.00   sec   111 MBytes   935 Mbits/sec  175    772 KBytes
[  4]   5.00-6.00   sec   100 MBytes   840 Mbits/sec  658    598 KBytes
[  4]   6.00-7.00   sec   106 MBytes   890 Mbits/sec  742    668 KBytes
[  4]   7.00-8.00   sec   102 MBytes   857 Mbits/sec  764    724 KBytes
[  4]   8.00-9.00   sec  97.4 MBytes   817 Mbits/sec  1175    764 KBytes
[  4]   9.00-10.00  sec   111 MBytes   934 Mbits/sec  1083    838 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  1010 MBytes   848 Mbits/sec  5119             sender
[  4]   0.00-10.00  sec  1008 MBytes   846 Mbits/sec                  receiver

iperf Done.
/ #
```

修改第一个 Pod 的入口带宽 QoS

```bash
[root@node2 ~]# kubectl annotate --overwrite  pod perf-4n4gt -n ls1 ovn.kubernetes.io/ingress_rate=30
```

再次从第二个 Pod 测试第一个 Pod 带宽
```bash
/ # iperf3 -c 10.66.0.12
Connecting to host 10.66.0.12, port 5201
[  4] local 10.66.0.14 port 52372 connected to 10.66.0.12 port 5201
[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd
[  4]   0.00-1.00   sec  3.66 MBytes  30.7 Mbits/sec    2   76.1 KBytes
[  4]   1.00-2.00   sec  3.43 MBytes  28.8 Mbits/sec    0    104 KBytes
[  4]   2.00-3.00   sec  3.50 MBytes  29.4 Mbits/sec    0    126 KBytes
[  4]   3.00-4.00   sec  3.50 MBytes  29.3 Mbits/sec    0    144 KBytes
[  4]   4.00-5.00   sec  3.43 MBytes  28.8 Mbits/sec    0    160 KBytes
[  4]   5.00-6.00   sec  3.43 MBytes  28.8 Mbits/sec    0    175 KBytes
[  4]   6.00-7.00   sec  3.50 MBytes  29.3 Mbits/sec    0    212 KBytes
[  4]   7.00-8.00   sec  3.68 MBytes  30.9 Mbits/sec    0    294 KBytes
[  4]   8.00-9.00   sec  3.74 MBytes  31.4 Mbits/sec    0    398 KBytes
[  4]   9.00-10.00  sec  3.80 MBytes  31.9 Mbits/sec    0    526 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  35.7 MBytes  29.9 Mbits/sec    2             sender
[  4]   0.00-10.00  sec  34.5 MBytes  29.0 Mbits/sec                  receiver

iperf Done.
/ #
```


## linux-htb Qos
linux-htb QoS 是基于优先级的 QoS 设置。新增了一个 CRD 资源，用于设置 QoS 的优先级。
CRD 定义如下：

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: htbqoses.kubeovn.io
spec:
  group: kubeovn.io
  versions:
    - name: v1
      served: true
      storage: true
      additionalPrinterColumns:
      - name: PRIORITY
        type: string
        jsonPath: .spec.priority
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                priority:
                  type: string					# Value in range 0 to 4,294,967,295.
  scope: Cluster
  names:
    plural: htbqoses
    singular: htbqos
    kind: HtbQos
    shortNames:
      - htbqos
```
CRD spec 参数只有一个字段，即 htbqoses.spec.priority，参数取值代表了优先级的大小。在镜像初始化中预置了三个 CRD 实例，分别是

```
mac@bogon kube-ovn % kubectl get htbqos
NAME            PRIORITY
htbqos-high     100
htbqos-low      300
htbqos-medium   200
```
优先级顺序是相对的，priority 取值越小，QoS 优先级越高。

subnet crd 增加了字段 subnet.Spec.HtbQos，用于指定 subnet 绑定的 HtbQos 实例，取值参考如下

```
mac@bogon kube-ovn % kubectl get subnet test -o yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: test
spec:
  cidrBlock: 192.168.0.0/16
  default: false
  gatewayType: distributed
  htbqos: htbqos-high
  ...
```
当 subnet 绑定了 HtbQos 实例之后，该 subnet 下的所有 Pod 都拥有相同的优先级设置。

Pod 新增了 annotation `ovn.kubernetes.io/priority`，取值内容为具体的 priority 数值，如`ovn.kubernetes.io/priority: "50"`，可以用于单独设置 Pod 的 QoS 优先级参数。

当 Pod 所在 subnet 指定了 HtbQos 参数，同时 Pod 又设置了 QoS 优先级 annotation 时，以 Pod annotation 取值为准。

对于带宽设置，仍然是基于Pod单独设置的，使用之前的 annotation `ovn.kubernetes.io/ingress_rate` 和 `ovn.kubernetes.io/egress_rate`，用于控制 Pod 的双向带宽。

## linux-netem QoS
Pod新增 annotation `ovn.kubernetes.io/latency`、`ovn.kubernetes.io/limit`和
`ovn.kubernetes.io/loss`，用于 linux-netem 类型 QoS 参数设置。

- latency 为设置的pod流量延迟参数，取值为整形数值，单位为 ms。
- limit 为qdisc队列可容纳的最大数据包数，取值为整形数值，例如 1000。
- loss 为设置的报文丢包概率，取值为float类型，例如取值为 0.2，则为设置 20% 的丢包概率。
