# Kube-OVN

![Kube-OVN](static/kube-ovn-horizontal-color.svg)

Kube-OVN, a CNCF Sandbox Project, bridges the SDN into Cloud Native. 
It offers an advanced Container Network Fabric for Enterprises with the most functions, 
extreme performance and the easiest operation.

**Most Functions:**

如果你怀念 SDN 领域丰富的网络能力却在云原生领域苦苦追寻而不得，那么 Kube-OVN 应该是你的最佳选择。

借助 OVS/OVN 在 SDN 领域成熟的能力，Kube-OVN 将网络虚拟化的丰富功能带入云原生领域。目前已支持子网管理，
静态 IP 分配，分布式/集中式网关，Underlay/Overlay 混合网络，VPC 多租户网络，跨集群互联网络，QoS 管理，
多网卡管理，ACL 网络控制，流量镜像，ARM 支持， Windows 支持等诸多功能。

**Extreme Performance:**

如果你担心容器网络会带来额外的性能损耗，那么来看一下 Kube-OVN 是如何极致的优化性能。

在数据平面，通过一系列对流表和内核的精心优化，并借助 eBPF、DPDK、智能网卡卸载等新兴技术，Kube-OVN 可以在延迟和吞吐量
等方面的指标达到近似或超出宿主机网络性能的水平。 在控制平面，通过对 OVN 上游流表的裁剪，各种缓存技术的使用和调优，
Kube-OVN 可以支持大规模上千节点和上万 Pod 的集群。

此外 Kube-OVN 还在不断优化 CPU 和内存等资源的使用量，以适应边缘等资源有限场景。

**Easiest Operation**

如果你对容器网络的运维心存忧虑，Kube-OVN 内置了大量的工具来帮助你简化运维操作。

Kube-OVN 提供了一键安装脚本，帮助用户迅速搭建生产就绪的容器网络。 同时内置的丰富的监控指标和 Grafana 面板，
可帮助用户建立完善的监控体系。强大的命令行工具可以简化用户的日常运维操作。通过和 Cilium 结合，利用 eBPF 能力用户可以
增强对网络的可观测性。 此外流量镜像的能力可以方便用户自定义流量监控，并和传统的 NPM 系统对接。
