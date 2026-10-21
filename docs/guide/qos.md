# 容器网络 QoS 配置

Kube-OVN 支持两种层面的 QoS 配置：

- **Pod 级别 QoS**：通过 Pod Annotation 动态调整单个 Pod 的带宽限制，或通过 `linux-netem` 模拟网络时延、抖动与丢包。
- **集群级与子网级 QoS 策略**：通过 [QoSPolicy CRD](../reference/kube-ovn-api.md#qospolicy) 对整个子网、VPC NAT 网关或特定工作负载应用统一的共享带宽限制与流分类。

> 说明：如需在子网、命名空间或 NAT 网关级别配置共享 QoS 策略，请参考 [QoSPolicy API](../reference/kube-ovn-api.md#qospolicy)。本文档主要介绍基于 Pod Annotation 的轻量级动态 QoS 配置方法。

## 基于最大带宽限制的 QoS

该类型的 QoS 可以通过 Pod annotation 动态配置，可以在不中断 Pod 运行的情况下进行调整。
带宽限速的单位为 `Mbit/s`。

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
    image: docker.io/library/nginx:alpine
```

使用 annotation 动态调整 QoS：

```bash
kubectl annotate --overwrite  pod nginx-74d5899f46-d7qkn ovn.kubernetes.io/ingress_rate=3
```

在通过 Multus 使用多网卡的场景下，可使用 `<provider>.kubernetes.io/` 前缀为特定附属网卡单独配置限速：

- `<provider>.kubernetes.io/ingress_rate`：多网卡指定网卡流入限速，单位为 `Mbit/s`
- `<provider>.kubernetes.io/egress_rate`：多网卡指定网卡流出限速，单位为 `Mbit/s`
- `<provider>.kubernetes.io/ingress_burst`：多网卡指定网卡流入 burst 上限
- `<provider>.kubernetes.io/egress_burst`：多网卡指定网卡流出 burst 上限

### 测试 QoS 调整

部署性能测试需要的容器：

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
        image: docker.io/kubeovn/perf
```

进入其中一个 Pod 并开启 iperf3 server：

```bash
# kubectl exec -it perf-4n4gt -n ls1 sh
# iperf3 -s
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------

```

进入另一个 Pod 请求之前的 Pod：

```bash
# kubectl exec -it perf-d4mqc -n ls1 sh
# iperf3 -c 10.66.0.12
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
```

修改第一个 Pod 的入口带宽 QoS：

```bash
kubectl annotate --overwrite  pod perf-4n4gt -n ls1 ovn.kubernetes.io/ingress_rate=30
```

再次从第二个 Pod 测试第一个 Pod 带宽：

```bash
# iperf3 -c 10.66.0.12
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
```

## linux-netem QoS

> RHEL 系列操作系统需要安装 netem 相关模块：
> yum install -y kernel-modules-extra && modprobe sch_netem

Pod 可以使用如下 annotation 配置 `linux-netem` 类型 QoS，由于 netem 本身的实现限制，以下 QoS 都只对 Pod 的 Ingress 方向流量生效：

- `ovn.kubernetes.io/latency`：设置 Pod 流量延迟，取值为整数，单位为 ms。
- `ovn.kubernetes.io/jitter`：设置 Pod 流量延迟抖动，取值为整数，单位为 ms。
- `ovn.kubernetes.io/limit`： 为 `qdisc` 队列可容纳的最大数据包数，取值为整形数值，例如 1000。
- `ovn.kubernetes.io/loss`： 为设置的报文丢包概率，取值为 float 类型，例如取值为 20，则为设置 20% 的丢包概率。

在多网卡场景下，可通过 `<provider>.kubernetes.io/latency`、`<provider>.kubernetes.io/jitter`、`<provider>.kubernetes.io/limit`、`<provider>.kubernetes.io/loss` 为特定网卡独立注入网络损伤。
