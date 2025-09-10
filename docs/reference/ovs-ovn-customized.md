# 对上游 OVS/OVN 修改

上游 OVN/OVS 最初设计目标为通用 SDN 控制器和数据平面。由于 Kubernetes 网络存在一些特殊的用法，
并且 Kube-OVN 只重点使用了部分功能，为了达到更好的性能、稳定性和特定的功能，Kube-OVN 对上游
OVN/OVS 做了部分修改。用户如果使用自己的 OVN/OVS 配合 Kube-OVN 的控制器进行工作时需要注意
下述的改动可能造成的影响。

未合入上游修改：

- [4228eab1d7](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/4228eab1d722087ba795e310eadc9e25c4513ec1.patch) 修复 vswitchd ofport_usage 内存泄露并定期修剪内存。
- [54056ea65d](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/54056ea65dc28aa1c4c721a2a34d7913f79f8376.patch) 调整选举 timer，避免大规模集群选举抖动。
- [6b4dcb311f](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/6b4dcb311f171d81a5d40ea51a273fc356c123db.patch) 添加 fdb 更新日志。
- [f627b7721e](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/f627b7721ec282f2edaf798913b1559b939687f0.patch) 修复 hairpin 环境下 fdb 学习错误的问题。
- [3f3e3a436f](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/3f3e3a436ff5eb2eaafbeeae8ea9dc0c514fe8a3.patch) 为 ovsdb-tool 的 join-cluster 子命令添加 Server ID 参数。
- [a6cb8215a8](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/a6cb8215a80635129e4fada4c0d25c25fb746bf7.patch) 修复 QoS 内存泄露问题。
- [d4d76ddb2e](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/d4d76ddb2e12cdd9e73bb5e008ebb9fd1b4d6ca6.patch) ovsdb-tool：添加 fix-cluster 命令。
- [ffd2328d4a](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/ffd2328d4a55271569e2b89e54a2c18f4e186af8.patch) netdev：减少获取设备地址的 CPU 利用率。
- [d088c5d8c2](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/d088c5d8c263552c5a31d87813991aee30ab74de.patch) ovs-router：跳过获取 kube-ipvs0 的源地址。
- [1b31f07dc6](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/1b31f07dc60c016153fa35d936cdda0e02e58492.patch) 增加大规模集群的默认探测间隔。
- [54b7678229](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/54b767822916606dbb78335a3197983f435b5b8a.patch) 更新 ovs-sandbox 以支持 docker run。
- [9ee66bd91b](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/9ee66bd91be65605cffb9a490b4dba3bc13358e9.patch) 修改源路由优先级。
- [e889d46924](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e889d46924085ca0fe38a2847da973dfe6ea100e.patch) 修复 Underlay 模式下达到 resubmit 限制的问题。
- [f9e97031b5](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/f9e97031b56ab5747b5d73629198331a6daacdfd.patch) ovn-controller：不为 Kube-OVN 端口在 localnet 上发送 GARP。
- [78cade0187](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/78cade01874292e2c101c39b975290ef6c812a50.patch) 添加有条件跳过 conntrack 的支持。
- [85aa6263ad](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/85aa6263ad5b3648eb7ceec90c812328dbb7c6c0.patch) northd：访问节点本地 DNS IP 时跳过 conntrack。
- [34dc3e3fcf](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/34dc3e3fcfacec6597293765ecd6e20fe15581f1.patch) lflow：不将 lport 之间的直接流量发送到 conntrack。
- [a297b840c2](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/a297b840c2c9f118c7ce6133077087b5999f12dd.patch) 在逻辑交换机入口管道中将 DNAT 数据包直接输出到 lsp。
- [03e35ed9c5](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/03e35ed9c5b4de0fa8acbc2c057cdd5957a8d605.patch) ovn-controller：使激活策略在单机箱环境下工作。
- [e7d3ba53cd](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e7d3ba53cdcbc524bb29c54ddb07b83cc4258ed7.patch) 设置 ACL 时跳过节点本地 DNS IP 的 conntrack。
- [9286e1fd57](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/9286e1fd578fdb8f565a0f4aa9066b538295e1ac.patch) 优先选择本地后端。
- [e5916eb53a](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e5916eb53abc3b7d28c407c3c47566c46116090a.patch) 修复具有多个分布式网关端口的 lr-lb DNAT 问题。
- [e4e6ea9c5f](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e4e6ea9c5f4ba080b719924e470daa8094ff38a7.patch) 支持专用的 BFD LRP。
- [e76880e792](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e76880e792af56b2a3836098105079f5f8f1ff26.patch) northd：添加 nb 选项 version_compatibility。
- [477695a010](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/477695a010affe56efdd66b60510fa612f8704c1.patch) northd：跳过从 localnet 端口对 lrp 地址的 arp/nd 请求。

已合入上游修改：

- [20626ea909](https://github.com/ovn-org/ovn/commit/20626ea9097020194fa558865ee8d64ba9ca0816) 组播流量绕过 LB 和 ACL 处理阶段，以提高特定数据链路性能。
- [a2d9ff3ccd](https://github.com/ovn-org/ovn/commit/a2d9ff3ccd4e12735436b0578ce0020cb62f2c27) Deb 构建增加编译优化选项。
