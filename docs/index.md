# Kube-OVN

![Kube-OVN](static/kube-ovn-horizontal-color.svg)

Kube-OVN 是一款 CNCF 旗下的企业级云原生网络编排系统，提供丰富的功能，极致的性能以及良好的可运维性。

**丰富的功能：**
借助 OVS/OVN 在 SDN 领域成熟的能力，Kube-OVN 将网络虚拟化的丰富功能带入云原生领域。 目前已支持子网管理，
静态 IP 分配，分布式/集中式网关，Underlay/Overlay 混合子网，VPC 多租户网络，跨集群互联网络，QoS 管理，
多网卡管理，ACL 网络控制，流量镜像，ARM 支持， Windows 支持等诸多功能。

** 极致的性能：**
通过一系列对流表和内核的优化，并借助 eBPF、DPDK、智能网卡卸载等技术，Kube-OVN 可以在物理机和虚拟机环境下
在延迟和吞吐量的性能表现上达到接近或超过宿主机网络性能的水平。

** 良好的可运维性：**
Kube-OVN 提供了丰富的网络质量监控指标并内置 Grafana 面板，同时可以和 Cilium 结合利用 eBPF 能力增强可观测性。
此外还支持流量镜像的能力，方便用户自定义流量监控。

## 联系我们

如需加入微信用户交流群，请扫描下方二维码并填写表单：

![img.png](static/user-wechat.png)

如需获得商业支持和咨询服务，请使用下方连接或扫描二维码填写表单：

[商业版支持](https://ma.alauda.cn/p/2f53a)

![img.png](static/enterprise-qr.png)
