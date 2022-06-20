# 准备工作

Kube-OVN 是一个符合 CNI 规范的网络组件，其运行需要依赖 Kubernetes 环境及对应的内核网络模块。
以下是通过测试的操作系统和软件版本，环境配置和所需要开放的端口信息。

## 软件版本
- Kubernetes >= 1.16，推荐 1.19 以上版本。
- Docker >= 1.12.6, Containerd >= 1.3.4。
- 操作系统: CentOS 7/8, Ubuntu 16.04/18.04/20.04。
- 其他 Linux 发行版，需要检查一下内核模块是否存在 `geneve`, `openvswitch`, `ip_tables` 和 `iptable_nat`，Kube-OVN 正常工作依赖上述模块。

*注意事项*：

1. 如果内核版本为 3.10.0-862 内核 `netfilter` 模块存在 bug 会导致 Kube-OVN 内置负载均衡器无法工作，需要对内核升级，建议使用 CentOS 官方对应版本最新内核保证系统的安全。相关内核 bug 参考 [Floating IPs broken after kernel upgrade to Centos/RHEL 7.5 - DNAT not working](https://bugs.launchpad.net/neutron/+bug/1776778)。
2. 如果内核版本为 4.4 则对应的内核 `openvswitch` 模块存在问题，建议升级或手动编译 `openvswitch` 新版本模块进行更新
3. Geneve 隧道建立需要检查 IPv6，可通过 `cat /proc/cmdline` 检查内核启动参数， 相关内核 bug 请参考 [Geneve tunnels don't work when ipv6 is disabled](https://bugs.launchpad.net/ubuntu/+source/linux/+bug/1794232)

## 环境配置
- Kernel 启动需要开启 ipv6, 如果 kernel 启动参数包含 `ipv6.disable=1` 需要将其设置为 0。
- `kube-proxy` 正常工作，Kube-OVN 可以通过 SVC IP 访问到 `kube-apiserver`。
- 确认 kubelet 配置参数开启了 CNI，并且配置在标准路径下, kubelet 启动时应包含如下参数 `--network-plugin=cni --cni-bin-dir=/opt/cni/bin --cni-conf-dir=/etc/cni/net.d`。
- 确认未安装其他网络插件，或者其他网络插件已经被清除，检查 `/etc/cni/net.d/` 路径下无其他网络插件配置文件。如果之前安装过其他网络插件，建议删除后重启机器清理残留网络资源。

## 端口信息
| 组件          | 端口    | 用途                        |
|-------------|-------|---------------------------|
| ovn-central | 6641/tcp, 6642/tcp, 6643/tcp, 6644/tcp | ovn-db 和 raft server 监听端口 |
| ovs-ovn	   | Geneve 6081/udp, STT 7471/tcp, Vxlan 4789/udp	  | 隧道端口                      |
|kube-ovn-controller|10660/tcp| 监控监听端口                    |
|kube-ovn-daemon|10665/tcp| 监控监听端口                        |
|kube-ovn-monitor|10661/tcp| 监控监听端口                        |
