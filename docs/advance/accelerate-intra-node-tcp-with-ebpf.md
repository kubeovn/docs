# 使用 eBPF 加速节点内 TCP 通信

在一些边缘和 5G 的场景下，同节点内的 Pod 之间会进行大量的 TCP 通信，通过使用 Intel 开源的 [istio-tcpip-bypass](https://github.com/intel/istio-tcpip-bypass){: target="_blank" }
项目，Pod 可以借助 eBPF 的能力绕过主机的 TCP/IP 协议栈，直接进行 socket 通信，从而大幅降低延迟并提升吞吐量。

## 基本原理

在当前的实现下，同主机的两个 Pod 进行 TCP 进行通信需要经过大量的网络栈，包括 TCP/IP, netfilter，OVS 等如下图所示：

![without eBPF](../static/intra-node-without-ebpf.png)

istio-tcpip-bypass 插件可以自动分析并识别出同主机内的 TCP 通信，并绕过复杂的内核栈从而可以直接进行 socket 间的数据传输，
来降低网络栈处理开销，如下图所示：

![with eBPF](../static/intra-node-with-ebpf.png)

由于该组件可以自动识别同主机内的 TCP 通信，并进行优化。在基于代理模式的 Service Mesh 环境下，该组件也可以增强 Service Mesh 的性能表现。

更多技术实现细节可以参考 [Tanzu Service Mesh Acceleration using eBPF](https://blogs.vmware.com/networkvirtualization/2022/08/tanzu-service-mesh-acceleration-using-ebpf.html/){: target="_blank" }。

## 环境准备

eBPF 对内核版本有一定要求，推荐使用 Ubuntu 20.04 和 Linux 5.4.0-74-generic 版本内核进行实验。

## 实验步骤

在同一个节点上部署两个性能测试 Pod，若集群内存在多台机器需要指定 `nodeSelector`：

```bash
# kubectl create deployment perf --image=kubeovn/perf:dev --replicas=2
deployment.apps/perf created
# kubectl get pod -o wide
NAME                    READY   STATUS    RESTARTS   AGE   IP           NODE     NOMINATED NODE   READINESS GATES
perf-7697bc6ddf-b2cpv   1/1     Running   0          28s   100.64.0.3   sealos   <none>           <none>
perf-7697bc6ddf-p2xpt   1/1     Running   0          28s   100.64.0.2   sealos   <none>           <none>
```

进入其中一个 Pod 开启 qperf server，在另一个 Pod 中启动 qperf client 进行性能测试：

```bash
# kubectl exec -it perf-7697bc6ddf-b2cpv sh
/ # qperf

# kubectl exec -it perf-7697bc6ddf-p2xpt sh
/ # qperf -t 60 100.64.0.3 -ub -oo msg_size:1:16K:*4 -vu tcp_lat tcp_bw
```

部署 istio-tcpip-bypass 插件：

```bash
kubectl apply -f https://raw.githubusercontent.com/intel/istio-tcpip-bypass/main/bypass-tcpip-daemonset.yaml
```

再次进入 perf client 容器进行性能测试：

```bash
# kubectl exec -it perf-7697bc6ddf-p2xpt sh
/ # qperf -t 60 100.64.0.3 -ub -oo msg_size:1:16K:*4 -vu tcp_lat tcp_bw
```

## 测试结果

根据测试结果 TCP 延迟在不同数据包大小的情况下会有 40% ~ 60% 的延迟下降，在数据包大于 1024 字节时吞吐量会有 40% ~ 80% 提升。

| Packet Size (byte) | eBPF tcp_lat (us) | Default tcp_lat (us) | eBPF tcp_bw (Mb/s) | Default tcp_bw(Mb/s) |
|--------------------|-------------------|----------------------|--------------------|----------------------|
| 1                  | 20.2              | 44.5                 | 1.36               | 4.27                 |
| 4                  | 20.2              | 48.7                 | 5.48               | 16.7                 |
| 16                 | 19.6              | 41.6                 | 21.7               | 63.5                 |
| 64                 | 18.8              | 41.3                 | 96.8               | 201                  |
| 256                | 19.2              | 36                   | 395                | 539                  |
| 1024               | 18.3              | 42.4                 | 1360               | 846                  |
| 4096               | 16.5              | 62.6                 | 4460               | 2430                 |
| 16384              | 20.2              | 58.8                 | 9600               | 6900                 |

> 在测试的硬件环境下，数据包小于 512 字节时，使用 eBPF 优化吞吐量指标会低于默认配置下的吞吐量。
> 该情况可能和默认配置下网卡开启 TCP 聚合优化相关。如果应用场景对小包吞吐量敏感，需要在相应环境下
> 进行测试判断是否开启 eBPF 优化。我们也会后续对 eBPF TCP 小包场景的吞吐量进行优化。

## 参考资料

1. [istio-tcpip-bypass](https://github.com/intel/istio-tcpip-bypass){: target="_blank" }
2. [Deep Dive TCP/IP Bypass with eBPF in Service Mesh](https://events.istio.io/istiocon-2022/sessions/tcpip-bypass-ebpf/){: target="_blank" }
3. [Tanzu Service Mesh Acceleration using eBPF](https://blogs.vmware.com/networkvirtualization/2022/08/tanzu-service-mesh-acceleration-using-ebpf.html/){: target="_blank" }
