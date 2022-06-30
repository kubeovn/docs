# OVS/OVN Customization

上游 OVN/OVS 最初设计目标为通用 SDN 控制器和数据平面。由于 Kubernetes 网络存在一些特殊的用法，
并且 Kube-OVN 只重点使用了部分功能，为了 达到更好的性能、稳定性和特定的功能，Kube-OVN 对上游 
OVN/OVS 做了部分修改。用户如果使用自己的 OVN/OVS 配合 Kube-OVN 的控制器进行工作时需要 注意
下述的改动可能造成的影响。

未合并入上游修改：

- [22ea22c40b](https://github.com/kubeovn/ovs/commit/22ea22c40b46ee5adeae977ff6cfca81b3ff25d7) 调整选举 timer，避免大规模集群选举抖动。
- [d26ae4de0a](https://github.com/kubeovn/ovn/commit/d26ae4de0ab070f6b602688ba808c8963f69d5c4) 目的地址非 Service 流量绕过 conntrack 以提高特定数据链路性能。
- [ab923b2522](https://github.com/kubeovn/ovn/commit/ab923b252271cbbcccc8091e338ee7efe75e5fcd) ECMP 算法由 dp_hash 调整为 hash，避免部分内核出现的哈希错误问题。
- [64383c14a9](https://github.com/kubeovn/ovs/commit/64383c14a9c25e9e0ca53c6758d9499c60132536) 修复 Windows 下内核 Crash 问题。
- [08a95db2ca](https://github.com/kubeovn/ovs/commit/08a95db2ca506fce4d89fdf4fafab74607b2bb9f) 支持 Windows 下的 github action 构建。
- [680e77a190](https://github.com/kubeovn/ovs/commit/680e77a190ae7df3086bc35bb6150238e97f9020) Windows 下默认使用 tcp 监听。
- [94b73d939c](https://github.com/kubeovn/ovn/commit/94b73d939cd33b0531fa9a3422c999cd83ead087) DNAT 后替换 Mac 地址为目标地址，减少额外性能开销。

已合入上游修改：
- [20626ea909](https://github.com/ovn-org/ovn/commit/20626ea9097020194fa558865ee8d64ba9ca0816) 组播流量绕过 LB 和 ACL 处理阶段，以提高特定数据链路性能。
- [a2d9ff3ccd](https://github.com/ovn-org/ovn/commit/a2d9ff3ccd4e12735436b0578ce0020cb62f2c27) Deb 构建增加编译优化选项。
