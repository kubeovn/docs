# Kube-OVN

![Kube-OVN](static/kube-ovn-horizontal-color.svg){: style="width:40%"}

## What is Kube-OVN?

Kube-OVN is an enterprise-level cloud-native network orchestration system under CNCF that combines the capabilities of SDN with cloud-native technologies, providing the most functions, extreme performance and the easiest operation.

Kube-OVN uses Open Virtual Network (OVN) and OpenVswitch at the underlying layer to implement network orchestration and exposes its rich capabilities to Kubernetes networking. OVN and OVS have a long history, having emerged long before Kubernetes was born, and have become the de facto standard in the SDN field. Kube-OVN brings them into Kubernetes, significantly enhancing Kubernetes' networking capabilities.

## Why Kube-OVN?

As the workloads running on Kubernetes become more diverse and the scenarios increase, the demand for networking also grows. As long-established networking components, OVN and OVS provide all the functionalities you need.

If you need to run KubeVirt on Kubernetes or have multi-tenant networking requirements, you will find that Kube-OVN's capabilities perfectly match your scenarios. Kube-OVN combines SDN capabilities with cloud-native technologies, offering the most functions, extreme performance and the easiest operation.

**Most Functions:**

If you miss the rich networking capabilities of the SDN age but are struggling to find them in the cloud-native age,
Kube-OVN should be your best choice.

Leveraging the proven capabilities of OVS/OVN in the SDN,
Kube-OVN brings the rich capabilities of network virtualization to the cloud-native space.
It currently supports [Subnet Management](guide/subnet.en.md), [Static IP Allocation](guide/static-ip-mac.en.md),
[Distributed/Centralized Gateways](guide/subnet.en.md#overlay-subnet-gateway-settings), [Underlay/Overlay Hybrid Networks](start/underlay.en.md),
[VPC Multi-Tenant Networks](vpc/vpc.en.md), [Cross-Cluster Interconnect](advance/with-ovn-ic.en.md), [QoS Management](guide/qos.en.md),
[Multi-NIC Management](advance/multi-nic.en.md), [ACL](guide/subnet.en.md#subnet-acl), [Traffic Mirroring](guide/mirror.en.md),
ARM Support, and many more.

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

## CNI Selection Recommendations

The Kubernetes community offers many excellent CNI projects, which can make selection difficult for users. We recommend first identifying your actual requirements, then evaluating how different projects address those needs - rather than comparing all products first and then deciding which one fits. This approach makes sense for two reasons:

1. Project maintainers primarily focus on their own projects and solving their community's problems - not tracking what other projects are doing or understanding their implementation details. Therefore, maintainers can't provide accurate comparison charts, and it's even harder for outsiders to do this.
2. For end users, understanding your internal needs is far more important than understanding the differences between external projects.

Creating a comparison chart under the Kube-OVN project that recommends Kube-OVN would inevitably be subjective and potentially inaccurate. Instead, we'll list scenarios where you **SHOULD NOT** choose Kube-OVN and provide our recommendations.

### When You Need an eBPF Solution

Choose [Cilium](https://cilium.io/) or Calico eBPF.

Kube-OVN uses Open vSwitch as its data plane, which is a relatively older network virtualization technology.

### When You Need an All-in-One Solution (CNI, Ingress, Service Mesh, and Observability)

Choose [Cilium](https://cilium.io/).

Kube-OVN primarily focuses on CNI-level networking capabilities, requiring you to combine it with other ecosystem projects for these additional features.

### When Running on OpenShift

Choose [ovn-kubernetes](https://ovn-kubernetes.io/).

Using third-party CNIs on OpenShift requires adapting to the [Cluster Network Operator](https://github.com/openshift/cluster-network-operator) specifications, which Kube-OVN currently doesn't plan to support. Additionally, third-party network plugins won't receive official Red Hat support, and since networking is critical in Kubernetes, you'd need to coordinate between multiple vendors for solution design and troubleshooting.

### When Using Public Cloud Kubernetes (EKS/AKS/GKE, etc.)

Choose the default CNI provided by your Kubernetes vendor, for the same reasons as above.

### When Running AI Training and Inference Workloads

Use Hostnetwork or [host-device](https://www.cni.dev/plugins/current/main/host-device/) to assign physical devices directly to containers.

AI workloads demand extremely low network latency, making any additional container network operations unnecessary.

## Concepts Clarification: OVN/ovn-kubernetes/Kube-OVN

Due to the similarity of these terms and some abbreviations, confusion often arises in communication. Here’s a brief clarification:

### OVN

[OVN](https://www.ovn.org/en/) is a virtual network controller maintained by the Open vSwitch community, providing foundational abstractions for virtual networking. It is platform-agnostic and can offer networking services to multiple CMS (Cloud Management Systems) such as OpenStack and Kubernetes. Both *ovn-kubernetes* and *Kube-OVN* rely on OVN’s networking capabilities to provide network functionality for Kubernetes.

### ovn-kubernetes

[ovn-kubernetes](https://ovn-kubernetes.io/) was initially a project launched by OVN maintainers to provide CNI networking capabilities for Kubernetes using OVN. It is now the default network for OpenShift and is widely used in OpenShift environments. It offers advanced features such as:

- [UDN (User-Defined Networks)](https://ovn-kubernetes.io/okeps/okep-5193-user-defined-networks/)
- [Multihoming](https://ovn-kubernetes.io/features/multiple-networks/multi-homing/)
- [Hardware Acceleration](https://ovn-kubernetes.io/features/hardware-offload/ovs-doca/)

### Kube-OVN

Kube-OVN was originally developed to address issues like static IP allocation, namespace-based address space assignment, and centralized gateways by building on OVN. In its early stages, it heavily borrowed design principles and architecture from *ovn-kubernetes*, such as:

- Using annotations to pass Pod network information.
- Leveraging *join* networks to bridge container and host networks.

With community contributions, it has evolved to support advanced features like Underlay networking, VPC, and KubeVirt integration.
