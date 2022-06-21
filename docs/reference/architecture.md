# 总体架构

本文档将介绍 Kube-OVN 的总体架构，和各个组件的功能以及其之间的交互。

总体来看，Kube-OVN 作为 Kubernetes 和 OVN 之间的一个桥梁，将成熟的 SDN 和云原生相结合。
这意味着 Kube-OVN 不仅通过 OVN 实现了 Kubernetes 下的网络规范，例如 CNI，Service 和 Networkpolicy，还将大量的 SDN 
领域能力带入云原生，例如逻辑交换机，逻辑路由器，VPC，网关，QoS，ACL 和流量镜像。

同时 Kube-OVN 还保持了良好的开放性可以和诸多技术方案集成，例如 Cilium，Submariner，Prometheus，KubeVirt 等等。

## 组件介绍

Kube-OVN 的组件可以大致分为三类：
* 上游 OVN/OVS 组件。
* 核心控制器和 Agent。
* 监控，运维工具和扩展组件。

### 上游 OVN/OVS 组件

该类型组件来自 OVN/OVS 社区，并针对 Kube-OVN 的使用场景做了特定修改。 OVN/OVS 本身是一套成熟的管理虚机和容器的 SDN 系统，我们强烈建议
对 Kube-OVN 实现感兴趣的用户先去读一下 [ovn-architecture(7)](https://www.mankier.com/7/ovn-architecture) 来了解什么是 OVN 以及
如何和它进行集成。Kube-OVN 使用 OVN 的北向接口创建和调整虚拟网络，并将其中的网络概念映射到 Kubernetes 之内。

所有 OVN/OVS 相关组件都已打包成对应镜像，并可在 Kubernetes 中运行。

#### ovn-central

`ovn-central` Deployment 运行 OVN 的管理平面组件，包括 `ovn-nb`, `ovn-sb`, 和 `ovn-northd`。

- `ovn-nb`： 保存虚拟网络配置，并提供 API 进行虚拟网络管理。`kube-ovn-controller` 将会主要和 `ovn-nb` 进行交互配置虚拟网络。
- `ovn-sb`： 保存从 `ovn-nb` 的逻辑网络生成的逻辑流表，以及各个节点的实际物理网络状态。
- `ovn-northd`：将 `ovn-nb` 的虚拟网络翻译成 `ovn-sb` 中的逻辑流表。 

多个 `ovn-central` 实例会通过 Raft 协议同步数据保证高可用。

### ovs-ovn

`ovs-ovn` 以 DaemonSet 形式运行在每个节点，在 Pod 内运行了 `openvswitch`, `ovsdb`, 和 `ovn-controller`。这些组件作为 `ovn-central`
的 Agent 将逻辑流表翻译成真实的网络配置。

### 核心控制器和 Agent

These are the core components in Kube-OVN that act as the bridge between Kubernetes and OVN and implement all the advanced network functions.

The code entrypoint of the components below can be found in `/cmd`.

#### kube-ovn-controller
It's a deployment that runs all the logic that translates the Kubernetes network concept into OVN.
You can treat it as the control plane of Kube-OVN.

It watches all network-related events in Kubernetes APIServer like Pod creation/deletion, Service/Endpoint modification, Networkpolicy changes, and so on.
Then the controller translates them into OVN logical network changes.
It also watches and updates CRDs that belong to Kube-OVN like VPC/Subnet/Vlan/IP to implement advanced network functions.

The basic function of kube-ovn-controller is watching pod creation events.
When the event comes the controller uses the embedded in-memory IPAM to allocate an address and call ovn-central to update the logical network,
in the pod creation case, it will create a logical switch port, add static routes and update ACL rules.
Then the controller writes the allocated address and other options like cidr, gateway, routes into Pod's annotations for the `kube-ovn-daemon` to use.
As the controller has a global ipam, it can allocate addresses in a global view.

#### kube-ovn-cni
It's a binary that acts as a thin shim between kubelet and `kube-ovn-daemon`.
It implements the CNI specification and passes the argument from kubelet to `kube-ovn-daemon` to do the real node-level network configuration works.

The binary is contained in the kube-ovn-cni daemonset and will be placed into `/opt/cni/bin` by `kube-ovn-daemon`.

#### kube-ovn-daemon
It's a daemonset run in every node and does all the stuff that really touches the network.

The main works include:
1. Bootstrap ovn-controller and ovs-vswitchd on every node
2. Handle CNI actions like add/del
    1. Create/Delete veth pair and plug them into Pod and OVS
    2. Configure the OVS port
    3. Update iptables/ipset/routes rules on the host network
3. Dynamically update the Pod bandwidth
4. Create `ovn0` for Pod-Host connectivity
5. Configure host network interface for Vlan/Underlay/EIP functions
6. Dynamically update the inter-cluster network gateway

### 监控，运维工具和扩展组件

These components are extensions of Kube-OVN main functions.
They provide monitoring, diagnosis, productive tools for Kube-OVN maintenance.

#### kube-ovn-speaker
It's a BGP speaker that can announce container networks to external BGP routers or switches so that workloads outside the Kubernetes cluster can visit the container network directly.

For more usage you can read [BGP support](../advance/with-bgp.md).

#### kube-ovn-pinger
该组件为一个 Daemonset 运行在每个节点上收集 OVS 运行信息，节点网络质量，网络延迟等信息，收集的监控指标可参考 [Kube-OVN 监控指标](./metrics.md)。

#### kube-ovn-monitor
该组件为一个 Deployment 收集 OVN 的运行信息，收集的监控指标可参考 [Kube-OVN 监控指标](./metrics.md)。

#### kubectl-ko
该组件为 kubectl 插件，可以快速运行常见运维操作，更多使用请参考 [kubectl 插件使用](../ops/kubectl-ko.md)。
