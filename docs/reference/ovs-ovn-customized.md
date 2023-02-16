# 对上游 OVS/OVN 修改

上游 OVN/OVS 最初设计目标为通用 SDN 控制器和数据平面。由于 Kubernetes 网络存在一些特殊的用法，
并且 Kube-OVN 只重点使用了部分功能，为了 达到更好的性能、稳定性和特定的功能，Kube-OVN 对上游
OVN/OVS 做了部分修改。用户如果使用自己的 OVN/OVS 配合 Kube-OVN 的控制器进行工作时需要注意
下述的改动可能造成的影响。

未合入上游修改：

- [38df6fa3f7](https://github.com/kubeovn/ovs/commit/38df6fa3f721dc53464fcff61dbc2bc79c710ab1) 调整选举 timer，避免大规模集群选举抖动。
- [d4888c4e75](https://github.com/kubeovn/ovs/commit/d4888c4e75f2288d8ff4f04ee57538659f118f5b) 添加 fdb 更新日志。
- [d4888c4e75](https://github.com/kubeovn/ovs/commit/403fbd0f6561c8985302734608c2de659671c563) 修复 hairpin 环境下 fdb 学习错误的问题。
- [9a81b91368](https://github.com/kubeovn/ovs/commit/9a81b91368b27afda97657a8864b729dc2e029e2) 为 ovsdb-tool 的 join-cluster 子命令添加 Server ID 参数。
- [62d4969877](https://github.com/kubeovn/ovn/commit/62d4969877712c26fe425698d898b440f91b44bf) 修复开启 SSL 后 OVSDB 监听地址错误的问题。
- [0700cb90f9](https://github.com/kubeovn/ovn/commit/0700cb90f950db1fb43490545dd4fc41afa46d70) 目的地址非 Service 流量绕过 conntrack 以提高特定数据链路性能。
- [c48049a64f](https://github.com/kubeovn/ovn/commit/c48049a64fedb1278f9158770a12751ee5bfc358) ECMP 算法由 dp_hash 调整为 hash，避免部分内核出现的哈希错误问题。
- [64383c14a9](https://github.com/kubeovn/ovs/commit/64383c14a9c25e9e0ca53c6758d9499c60132536) 修复 Windows 下内核 Crash 问题。
- [08a95db2ca](https://github.com/kubeovn/ovs/commit/08a95db2ca506fce4d89fdf4fafab74607b2bb9f) 支持 Windows 下的 github action 构建。
- [680e77a190](https://github.com/kubeovn/ovs/commit/680e77a190ae7df3086bc35bb6150238e97f9020) Windows 下默认使用 tcp 监听。
- [05e57b3227](https://github.com/kubeovn/ovn/commit/05e57b322758461c54d5cad030486c3d25942c73) 支持 Windows 编译。
- [b3801ecb73](https://github.com/kubeovn/ovs/commit/b3801ecb732a788efd2380a7daca4e2a7726128e) 修改源路由的优先级。
- [977e569539](https://github.com/kubeovn/ovs/commit/977e569539893460cd27b2287d6042b62079ea65) 修复 Underlay 模式下 Pod 数量过多导致 OVS 流表 resubmit 次数超过上限的问题。
- [45a4a22161](https://github.com/kubeovn/ovn/commit/45a4a22161e42f17f21baee9106a45964dfd3a1b) ovn-nbctl：vips 为空时不删除 Load Balancer。
- [540592b9ff](https://github.com/kubeovn/ovn/commit/540592b9fff8c5574ae605086fdaa16b718551f7) DNAT 后替换 Mac 地址为目标地址，减少额外性能开销。
- [10972d9632](https://github.com/kubeovn/ovs/commit/10972d963208490c5fe6ff66247b86b947136da6) 修复 vswitchd ofport_usage 内存泄露。

已合入上游修改：

- [20626ea909](https://github.com/ovn-org/ovn/commit/20626ea9097020194fa558865ee8d64ba9ca0816) 组播流量绕过 LB 和 ACL 处理阶段，以提高特定数据链路性能。
- [a2d9ff3ccd](https://github.com/ovn-org/ovn/commit/a2d9ff3ccd4e12735436b0578ce0020cb62f2c27) Deb 构建增加编译优化选项。
