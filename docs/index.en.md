# Kube-OVN

![Kube-OVN](static/kube-ovn-horizontal-color.svg){: style="width:40%"}

# What is Kube-OVN?

Kube-OVN is an enterprise-level cloud-native network orchestration system under CNCF that combines the capabilities of SDN with cloud-native technologies, providing the most functions, extreme performance and the easiest operation.

Kube-OVN uses Open Virtual Network (OVN) and OpenVswitch at the underlying layer to implement network orchestration and exposes its rich capabilities to Kubernetes networking. OVN and OVS have a long history, having emerged long before Kubernetes was born, and have become the de facto standard in the SDN field. Kube-OVN brings them into Kubernetes, significantly enhancing Kubernetes' networking capabilities.

# Why Kube-OVN?

As the workloads running on Kubernetes become more diverse and the scenarios increase, the demand for networking also grows. As long-established networking components, OVN and OVS provide all the functionalities you need.

If you need to run KubeVirt on Kubernetes or have multi-tenant networking requirements, you will find that Kube-OVN's capabilities perfectly match your scenarios. Kube-OVN combines SDN capabilities with cloud-native technologies, offering the most functions, extreme performance and the easiest operation.

**Most Functions:**

If you miss the rich networking capabilities of the SDN age but are struggling to find them in the cloud-native age,
Kube-OVN should be your best choice.

Leveraging the proven capabilities of OVS/OVN in the SDN,
Kube-OVN brings the rich capabilities of network virtualization to the cloud-native space.
It currently supports [Subnet Management](guide/subnet.en.md), [Static IP Allocation](guide/static-ip-mac.en.md),
[Distributed/Centralized Gateways](guide/subnet.en.md#overlay-subnet-gateway-settings), [Underlay/Overlay Hybrid Networks](start/underlay.en.md),
[VPC Multi-Tenant Networks](guide/vpc.en.md), [Cross-Cluster Interconnect](advance/with-ovn-ic.en.md), [QoS Management](guide/qos.en.md),
[Multi-NIC Management](advance/multi-nic.en.md), [ACL](guide/subnet.en.md#subnet-acl), [Traffic Mirroring](guide/mirror.en.md),
ARM Support, [Windows Support](advance/windows.en.md), and many more.

**Extreme Performance:**

If you're concerned about the additional performance loss associated with container networks,
then take a look at [How Kube-OVN is doing everything it can to optimize performance](advance/performance-tuning.en.md).

In the data plane, through a series of carefully optimized flow and kernel optimizations,
and with emerging technologies such as [eBPF](advance/with-cilium.en.md), [DPDK](advance/dpdk.en.md) and [SmartNIC Offload](advance/offload-mellanox.en.md),
Kube-OVN can approximate or exceed host network performance in terms of latency and throughput.

In the control plane, Kube-OVN can support large-scale clusters of thousands of nodes and tens of thousands of Pods
through the tailoring of OVN upstream flow tables and the use and tuning of various caching techniques.

In addition, Kube-OVN is continuously optimizing the usage of resources such as CPU and memory
to accommodate resource-limited scenarios such as the edge.

**Easiest Operation:**

If you're worried about container network operations, Kube-OVN has a number of
built-in tools to help you simplify your operations.

Kube-OVN provides [one-click installation scripts](start/one-step-install.en.md) to help users quickly build production-ready container networks.
Also built-in rich [monitoring metrics](reference/metrics.en.md) and [Grafana dashboard](guide/prometheus-grafana.en.md) help users to quickly set up monitoring system.

Powerful [command line tools](ops/kubectl-ko.en.md) simplify daily operations and maintenance for users.
By combining [with Cilium](advance/with-cilium.en.md), users can enhance the observability of their networks with eBPF capabilities.
In addition, the ability to [mirror traffic](guide/mirror.en.md) makes it easy to customize traffic monitoring and interface with traditional NPM systems.
