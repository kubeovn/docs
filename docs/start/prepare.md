# 准备工作

Kube-OVN 是一个符合 CNI 规范的网络组件，其运行需要依赖 Kubernetes 环境及对应的内核网络模块。
以下是通过测试的操作系统和软件版本、环境配置以及所需要开放的端口信息。

## 软件版本

- Kubernetes >= 1.29。
- Containerd >= 1.7，或其他符合 CRI 规范的容器运行时（自 Kubernetes 1.24 起 dockershim 已被移除，不再直接支持 Docker）。
- 操作系统：建议使用仍在维护期的发行版，例如 RHEL 9 / Rocky Linux 9 / AlmaLinux 9、Ubuntu 22.04 / 24.04、Debian 12、openEuler 22.03+ 等。CentOS 7/8 与 Ubuntu 16.04/18.04/20.04 已 EOL，不建议在生产环境使用。
- 内核版本建议使用 5.10 及以上版本以获得完整的 OVS/OVN 支持。
- 其他 Linux 发行版，需要检查一下内核模块是否存在 `geneve`, `openvswitch`, `ip_tables` 和 `iptable_nat`，Kube-OVN 正常工作依赖上述模块。

*注意事项*：

1. Rocky Linux 8.6 的内核 4.18.0-372.9.1.el8.x86_64 存在 TCP 通信问题 [TCP connection failed in Rocky Linux 8.6](https://github.com/kubeovn/kube-ovn/issues/1647){: target="_blank" }，请升级内核至 4.18.0-372.13.1.el8_6.x86_64 或更高版本。
2. Geneve 隧道建立需要检查 IPv6，可通过 `cat /proc/cmdline` 检查内核启动参数， 相关内核 bug 请参考 [Geneve tunnels don't work when ipv6 is disabled](https://bugs.launchpad.net/ubuntu/+source/linux/+bug/1794232){: target="_blank" }。

## 环境配置

- 内核启动需要开启 IPv6，如果内核启动参数包含 `ipv6.disable=1` 需要将其设置为 0。
- `kube-proxy` 正常工作，Kube-OVN 可以通过 Service ClusterIP 访问到 `kube-apiserver`。
- 确认 kubelet 配置使用的 CNI 路径正确（默认 bin 路径 `/opt/cni/bin`，conf 路径 `/etc/cni/net.d`）。Kubernetes 1.24 起已移除 `--network-plugin`/`--cni-bin-dir`/`--cni-conf-dir` 等命令行参数，相关配置改由各容器运行时（如 containerd 的 `/etc/containerd/config.toml`）承担。
- 确认未安装其他网络插件，或者其他网络插件已经被清除，检查 `/etc/cni/net.d/` 路径下无其他网络插件配置文件。如果之前安装过其他网络插件，建议删除后重启机器清理残留网络资源。

## 端口信息

| 组件 | 端口 | 用途 |
| ------------------- | --------------------------------------------- | ------------------------------ |
| ovn-central | 6641/tcp | ovn nb db server 监听端口 |
| ovn-central | 6642/tcp | ovn sb db server 监听端口 |
| ovn-central | 6643/tcp | ovn northd server 监听端口 |
| ovn-central | 6644/tcp | ovn raft server 监听端口 |
| ovn-ic | 6645/tcp | ovn ic nb db server 监听端口 |
| ovn-ic | 6646/tcp | ovn ic sb db server 监听端口 |
| ovs-ovn | Geneve 6081/udp, STT 7471/tcp, Vxlan 4789/udp | 隧道端口 |
| kube-ovn-controller | 10660/tcp | 监控监听端口 |
| kube-ovn-daemon | 10665/tcp | 监控监听端口 |
| kube-ovn-monitor | 10661/tcp | 监控监听端口 |

如果节点上运行了 firewalld，您还需要开启 Packet Forwarding 以及 Masquerade：

```bash
# 开启 Packet Forwarding
firewall-cmd --add-forward --permanent
# 开启 IPv4 Masquerade
firewall-cmd --add-masquerade --permanent
# 为 Kube-OVN IPv6/双栈 子网开启 Masquerade，如果您的子网配置不同请按需调整
firewall-cmd --permanent --add-rich-rule 'rule family="ipv6" source address="fd00:10:16::/112" masquerade'

firewall-cmd --reload
```
