# Kube-OVN

![Kube-OVN](static/kube-ovn-horizontal-color.svg){: style="width:40%"}

## What is Kube-OVN?

Kube-OVN 是一款 CNCF 旗下的企业级云原生网络编排系统，将 SDN 的能力和云原生结合，提供丰富的功能，极致的性能以及良好的可运维性。

Kube-OVN 在底层使用 Open Virtual Network（OVN）和 OpenVswitch 来实现网络的编排，并将其丰富的能力暴露给 Kubernetes 网络。
OVN 和 OVS 有着悠久的历史，早在 Kubernetes 诞生前就已经出现，成为了 SDN 领域的事实标准。Kube-OVN 将它们引入到 Kubernetes 中，大幅增强了 Kubernetes 的网络能力。

## Why Kube-OVN?

随着在 Kubernetes 上运行的负载以及运行的场景越来越多样化，对网络的需求也越来越多。OVN 和 OVS 作为历史悠久的网络组件，你可以在他们身上找到所有你需要的功能。

如果你需要在 Kubernetes 上运行 KubeVirt, 或者有多租户网络的需求，你会发现 Kube-OVN 的能力将会完美契合你的场景。Kube-OVN 将 SDN 的能力和云原生结合，提供丰富的功能，极致的性能以及良好的可运维性。

**丰富的功能：**

如果你怀念 SDN 领域丰富的网络能力却在云原生领域苦苦追寻而不得，那么 Kube-OVN 将是你的最佳选择。

借助 OVS/OVN 在 SDN 领域成熟的能力，Kube-OVN 将网络虚拟化的丰富功能带入云原生领域。目前已支持[子网管理](guide/subnet.md)，
[静态 IP 分配](guide/static-ip-mac.md)，[分布式/集中式网关](guide/subnet.md#overlay)，[Underlay/Overlay 混合网络](start/underlay.md)，
[VPC 多租户网络](guide/vpc.md)，[跨集群互联网络](advance/with-ovn-ic.md)，[QoS 管理](guide/qos.md)，
[多网卡管理](advance/multi-nic.md)，[ACL 网络控制](guide/subnet.md#acl)，[流量镜像](guide/mirror.md)，ARM 支持，
[Windows 支持](advance/windows.md)等诸多功能。

**极致的性能：**

如果你担心容器网络会带来额外的性能损耗，那么来看一下 Kube-OVN 是如何极致的[优化性能](advance/performance-tuning.md)。

在数据平面，通过一系列对流表和内核的精心优化，并借助 [eBPF](advance/with-cilium.md)、[DPDK](advance/dpdk.md)、[智能网卡卸载](advance/offload-corigine.md)等新兴技术，
Kube-OVN 可以在延迟和吞吐量等方面的指标达到近似或超出宿主机网络性能的水平。在控制平面，通过对 [OVN 上游流表的裁剪](./reference/ovs-ovn-customized.md)，
各种缓存技术的使用和调优，Kube-OVN 可以支持大规模上千节点和上万 Pod 的集群。

此外 Kube-OVN 还在不断优化 CPU 和内存等资源的使用量，以适应边缘等资源有限场景。

**良好的可运维性：**

如果你对容器网络的运维心存忧虑，Kube-OVN 内置了大量的工具来帮助你简化运维操作。

Kube-OVN 提供了[一键安装脚本](start/one-step-install.md)，帮助用户迅速搭建生产就绪的容器网络。同时内置的丰富的[监控指标](reference/metrics.md)和 [Grafana 面板](guide/prometheus-grafana.md)，
可帮助用户建立完善的监控体系。强大的[命令行工具](ops/kubectl-ko.md)可以简化用户的日常运维操作。通过[和 Cilium 结合](advance/with-cilium.md)，利用 eBPF 能力用户可以
增强对网络的可观测性。此外[流量镜像](guide/mirror.md)的能力可以方便用户自定义流量监控，并和传统的 NPM 系统对接。
