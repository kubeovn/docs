# Accelerate TCP Communication in Node with eBPF

At some edge and 5G scenarios, there will be a lot of TCP communication between Pods on the same node. By using the open source
[istio-tcpip-bypass](https://github.com/intel/istio-tcpip-bypass){: target="_blank" } project from Intel, Pods can use the ability of eBPF to bypass the host's TCP/IP protocol stack and communicate directly through sockets, thereby greatly reducing latency and improving throughput.

## Basic Principle

At present, two Pods on the same host need to go through a lot of network stacks, including TCP/IP, netfilter, OVS, etc., as shown in the following figure:

![without eBPF](../static/intra-node-without-ebpf.png)

istio-tcpip-bypass plugin can automatically analyze and identify TCP communication within the same host, and bypass the complex kernel stack so that socket data transmission can be performed directly to reduce network stack processing overhead, as shown in the following figure:

![with eBPF](../static/intra-node-with-ebpf.png)

Due to the fact that this component can automatically identify TCP communication within the same host and optimize it. In the Service Mesh environment based on the proxy mode, this component can also enhance the performance of Service Mesh.

For more technical implementation details, please refer to [Tanzu Service Mesh Acceleration using eBPF](https://blogs.vmware.com/networkvirtualization/2022/08/tanzu-service-mesh-acceleration-using-ebpf.html/){: target="_blank" }.

## Prerequisites

eBPF requires a kernel version of at least 5.4.0-74-generic. It is recommended to use Ubuntu 20.04 and Linux 5.4.0-74-generic kernel version for testing.

## Experimental Steps

Deploy two performance test Pods on the same node. If there are multiple machines in the cluster, you need to specify `nodeSelector`:

```bash
# kubectl create deployment perf --image=kubeovn/perf:dev --replicas=2
deployment.apps/perf created
# kubectl get pod -o wide
NAME                    READY   STATUS    RESTARTS   AGE   IP           NODE     NOMINATED NODE   READINESS GATES
perf-7697bc6ddf-b2cpv   1/1     Running   0          28s   100.64.0.3   sealos   <none>           <none>
perf-7697bc6ddf-p2xpt   1/1     Running   0          28s   100.64.0.2   sealos   <none>           <none>
```

Enter one of the Pods to start the qperf server, and start the qperf client in another Pod for performance testing:

```bash
# kubectl exec -it perf-7697bc6ddf-b2cpv sh
/ # qperf

# kubectl exec -it perf-7697bc6ddf-p2xpt sh
/ # qperf -t 60 100.64.0.3 -ub -oo msg_size:1:16K:*4 -vu tcp_lat tcp_bw
```

Deploy the istio-tcpip-bypass plugin:

```bash
kubectl apply -f https://raw.githubusercontent.com/intel/istio-tcpip-bypass/main/bypass-tcpip-daemonset.yaml
```

Enter the perf client container again for performance testing:

```bash
# kubectl exec -it perf-7697bc6ddf-p2xpt sh
/ # qperf -t 60 100.64.0.3 -ub -oo msg_size:1:16K:*4 -vu tcp_lat tcp_bw
```

## Test Results

According to the test results, the TCP latency will decrease by 40% ~ 60% under different packet sizes, and the throughput will increase by 40% ~ 80% when the packet size is greater than 1024 bytes.

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

> In the hardware environment under test, when the packet size is less than 512 bytes, the throughput indicator optimized by eBPF is lower than the throughput under the default configuration.
> This situation may be related to the TCP aggregation optimization of the network card under the default configuration. If the application scenario is sensitive to small packet throughput, you need to test in the corresponding environment
> Determine whether to enable eBPF optimization. We will also optimize the throughput of eBPF TCP small packet scenarios in the future.

## References

1. [istio-tcpip-bypass](https://github.com/intel/istio-tcpip-bypass){: target="_blank" }
2. [Deep Dive TCP/IP Bypass with eBPF in Service Mesh](https://events.istio.io/istiocon-2022/sessions/tcpip-bypass-ebpf/){: target="_blank" }
3. [Tanzu Service Mesh Acceleration using eBPF](https://blogs.vmware.com/networkvirtualization/2022/08/tanzu-service-mesh-acceleration-using-ebpf.html/){: target="_blank" }
