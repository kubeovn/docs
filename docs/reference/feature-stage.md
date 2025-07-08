# 功能成熟度

在 Kube-OVN 中根据功能使用度，文档完善程度和测试覆盖程度将功能成熟度分为 **Alpha**，**Beta** 和 **GA** 三个阶段。

## 成熟度定义

对于 **Alpha** 功能：

- 该功能没有完整的文档和完善的测试覆盖。
- 该功能未来可能会发生变化甚至整体移除。
- 该功能 API 不保证稳定，可能会被移除。
- 该功能的社区支持优先级较低，且无法保证长期支持。
- 由于功能稳定性和长期支持无法保证，可以进行测试验证，但不推荐生产使用。

对于 **Beta** 功能：

- 该功能有部分文档和测试，但是不保证完整的覆盖。
- 该功能未来可能发生变化，升级可能会影响网络，但不会被整体移除。
- 该功能 API 未来可能会发生变化，字段可能会进行调整，但不会整体移除。
- 该功能会得到社区的长期支持。
- 由于功能会得到长期支持，可以在非关键业务上进行使用，但是由于功能和 API 存在变化的可能，可能会在升级中出现中断，不推荐在关键生产业务上使用。

对于 **GA** 功能：

- 该功能有完整的文档和测试覆盖。
- 该功能会保持稳定，升级会保证平滑。
- 该功能 API 不会发生破坏性变化。
- 该功能会得到社区高优先级支持，并会保证长期支持。

## 成熟度列表

本列表统计从 v1.8 版本中包含的功能对应成熟度。

| 功能                              | 默认开启  | 状态    | 开始（Since） | 结束（Until） |
|---------------------------------|-------|-------|-----------|-----------|
| [Namespaced Subnet](../guide/subnet.md) | true  | GA    | 1.8       |           |
| [分布式网关](../guide/subnet.md) | true  | GA    | 1.8       |           |
| [主从模式集中式网关](../guide/subnet.md) | true  | GA    | 1.8       |           |
| [ECMP 模式集中式网关](../guide/setup-options.md) | false | Beta  | 1.8       |           |
| [子网 ACL](../guide/subnet.md) | true  | Alpha | 1.9       |           |
| [子网隔离 (未来会和子网 ACL 合并)](../guide/subnet.md) | true  | Beta  | 1.8       |           |
| [Underlay 子网](../start/underlay.md) | true  | GA    | 1.8       |           |
| [多网卡管理](../advance/multi-nic.md) | true  | Beta  | 1.8       |           |
| [子网 DHCP](../kubevirt/dhcp.md) | false | Alpha | 1.10      |           |
| [子网设置外部网关](../advance/external-gateway.md) | false | Alpha | 1.8       |           |
| [使用 OVN-IC 进行集群互联](../advance/with-ovn-ic.md) | false | Beta  | 1.8       |           |
| [使用 Submariner 进行集群互联](../advance/with-submariner.md) | false | Alpha | 1.9       |           |
| [子网 VIP 预留](../advance/vip.md) | true  | Alpha | 1.10      |           |
| [创建自定义 VPC](../vpc/vpc.md) | true  | Beta  | 1.8       |           |
| [自定义 VPC 浮动 IP/SNAT/DNAT](../vpc/vpc.md) | true  | Alpha | 1.10      |           |
| [自定义 VPC 静态路由](../vpc/vpc.md) | true  | Alpha | 1.10      |           |
| [自定义 VPC 策略路由](../vpc/vpc.md) | true  | Alpha | 1.10      |           |
| [自定义 VPC 安全组](../vpc/security-group.md) | true  | Alpha | 1.10      |           |
| [容器最大带宽 QoS](../guide/qos.md) | true  | GA    | 1.8       |           |
| [linux-netem QoS](../guide/qos.md) | true  | Alpha | 1.9       |           |
| [Prometheus 集成](../guide/prometheus.md) | false | GA    | 1.8       |           |
| [Grafana 集成](../guide/prometheus-grafana.md) | false | GA    | 1.8       |           |
| [双栈网络](../guide/dual-stack.md) | false | GA    | 1.8       |           |
| [默认 VPC EIP/SNAT](../guide/eip-snat.md) | false | Beta  | 1.8       |           |
| [流量镜像](../guide/mirror.md) | false | GA    | 1.8       |           |
| [NetworkPolicy](../guide/setup-options.md) | true  | Beta  | 1.8       |           |
| [Webhook](../guide/webhook.md) | false | Alpha | 1.10      |           |
| [性能调优](../advance/performance-tuning.md) | false | Beta  | 1.8       |           |
| [Overlay 子网静态路由对外暴露](../advance/overlay-with-route.md) | false | Alpha | 1.8       |           |
| [Overlay 子网 BGP 对外暴露](../advance/with-bgp.md) | false | Alpha | 1.9       |           |
| [Cilium 集成](../advance/with-cilium.md) | false | Alpha | 1.10      |           |
| [自定义 VPC 互联](../vpc/vpc-peering.md) | false | Alpha | 1.10      |           |
| [Mellanox Offload](../advance/offload-mellanox.md) | false | Alpha | 1.8       |           |
| [芯启源 Offload](../advance/offload-corigine.md) | false | Alpha | 1.10      |           |
| [DPDK 支持](../advance/dpdk.md) | false | Alpha | 1.10      |           |
| [OpenStack 集成](../advance/dpdk.md) | false | Alpha | 1.9       |           |
| [单个 Pod 固定 IP/Mac](../guide/static-ip-mac.md) | true  | GA    | 1.8       |           |
| [Workload 固定 IP](../guide/static-ip-mac.md) | true  | GA    | 1.8       |           |
| [StatefulSet 固定 IP](../guide/static-ip-mac.md) | true  | GA    | 1.8       |           |
| [VM 固定 IP](../guide/static-ip-mac.md) | false | Beta  | 1.9       |           |
| [默认 VPC Load Balancer 类型 Service](../guide/loadbalancer-service.md) | false | Alpha | 1.11      |           |
| [自定义 VPC 内部 DNS](../vpc/vpc-internal-dns.md) | false | Alpha | 1.11      |           |
| [Underlay 和 Overlay 互通](../start/underlay.md) | false | Beta | 1.12      |           |
| [VPC Egress Gateway](../vpc/vpc-egress-gateway.md) | true | Alpha | 1.14      |           |
