# 生产环境诊断工具

生产版 Kube-OVN 镜像包含网络 daemon 和轻量的
`kubectl-ko-node-agent`。节点诊断由独立 agent 执行，agent 只为当前
`kubectl ko` 操作获取所需的权限。

生产基础镜像和 DPDK 镜像不包含下表中的通用诊断工具；debug 镜像可以继续
提供 `gdb`、`valgrind` 和抓包工具用于 CI 或交互式排障。

| 旧工具 | 生产环境替代方式 | 说明 |
| --- | --- | --- |
| `tcpdump` 和其他 sniffer | `kubectl ko capture` | agent 在目标网络命名空间中打开 `AF_PACKET` socket，可使用 `-w -` 输出 pcap，不启动 `nsenter` 或 tcpdump 进程。`-D` 列出接口；pcap 目前需要 Ethernet 接口。 |
| Wireshark | 在本地工作站读取 pcap | 节点只负责输出 pcap 流，图形界面不需要部署到节点。 |
| `netcat`/`ncat` | `kubectl ko diagnose connectivity` | 使用 Go TCP/UDP 探测报告端点可达性。 |
| `nmap` Geneve 探测 | agent 原生 UDP 探测 | `diagnose environment` 报告 `open`、`closed` 或 `unknown`；没有响应的 UDP 报文不能证明服务已就绪。 |
| `strace`、`readelf`、`gdb` | `kubectl ko` trace、日志、网络检查和性能命令 | 生产镜像不依赖这些工具；debug 镜像可以继续提供它们。 |

`capture` 支持 `-D`、`-i`、`-c`、`-s`、`-nn` 和 `-w -`。对于 Pod、Service/工作
负载以及 VM/VMI 目标，`-i IFACE` 在目标 Pod 的网络命名空间中解析接口，
因此可以选择 Multus 等 secondary interface，例如 `net1`：

```console
kubectl ko capture -n app pod/web -- -i net1 -c 10
```

该命令进入选中 Pod 的网络命名空间，从 `net1` 抓取 10 个报文。抓包输出可以
使用 `-w -` 保存到工作站，再由本地工具解析：

```console
kubectl ko capture -n app pod/web -- -i net1 -c 10 -w - > capture.pcap
```

agent 自己通过 `setns(2)` 进入已挂载的网络命名空间，使抓包与
`kube-ovn-cni`、`ovs-ovn` 和 `ovn-central` 容器相互独立。由于依赖 Linux 的
`AF_PACKET` 和 network namespace，节点侧 agent 仅支持 Linux；Windows 支持
的是 kubectl 客户端。
