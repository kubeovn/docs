# Underlay Installation

By default, the default subnet uses Geneve to encapsulate cross-host traffic,
and build an overlay network on top of the infrastructure.

For the case that you want the container network to use the physical network address directly,
you can set the default subnet of Kube-OVN to work in Underlay mode,
which can directly assign the address resources in the physical network to the containers,
achieving better performance and connectivity with the physical network.

![topology](../static/vlan-topology.png)

## Limitation

Since the container network in this mode uses physical network directly for L2 packet forwarding,
L3 functions such as SNAT/EIP, distributed gateway/centralized gateway in Overlay mode cannot be used.

## Comparison with Macvlan

The Underlay mode of Kube-OVN is very similar to the Macvlan, with the following major differences in functionality and performance:

1. Macvlan performs better in terms of throughput and latency performance metrics due to its shorter kernel path and the fact that it does not require OVS for packet processing.
2. Kube-OVN provides arp-proxy functionality through flow tables to mitigate the risk of arp broadcast storms on large-scale networks.
3. Since Macvlan works at the bottom of the kernel and bypasses the host netfilter, Service and NetworkPolicy functionality requires additional development.
   Kube-OVN provides Service and NetworkPolicy capabilities through the OVS flow table.
4. Kube-OVN Underlay mode provides additional features such as address management, fixed IP and QoS compared to Macvlan.

## Environment Requirements

In Underlay mode, the OVS will bridge a node NIC to the OVS bridge and send packets directly through that node NIC,
relying on the underlying network devices for L2/L3 level forwarding capabilities. You need to configure the corresponding gateway,
Vlan and security policy in the underlying network device in advance.

1. For OpenStack VM environments, you need to turn off `PortSecurity` on the corresponding network port.
2. For VMware vswtich networks, `MAC Address Changes`, `Forged Transmits` and `Promiscuous Mode Operation` should be set to `allow`.
3. The network interface that is bridged into ovs can not be type of Linux Bridge.

For management and container networks using the same NIC, Kube-OVN will transfer the NIC's Mac address, IP address, route,
and MTU to the corresponding OVS Bridge to support single NIC deployment of Underlay networks.
OVS Bridge name format is `br-PROVIDER_NAME`，`PROVIDER_NAME` is the name of `ProviderNetwork` (Default: provider).

## Specify Network Mode When Deploying

This deployment mode sets the default subnet to Underlay mode,
and all Pods with no subnet specified will run in the Underlay network by default.

### Download Script

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install.sh
```

#### Modify Configuration Options

```bash
NETWORK_TYPE          # set to vlan
VLAN_INTERFACE_NAME   # set to the NIC that carries the Underlay traffic, e.g. eth1
VLAN_ID               # The VLAN Tag need to be added，if set 0 no vlan tag will be added
POD_CIDR              # The Underlay network CIDR， e.g. 192.168.1.0/24
POD_GATEWAY           # Underlay physic gatewa address, e.g. 192.168.1.1
EXCLUDE_IPS           # Exclude ranges to avoid conflicts between container network and IPs already in use on the physical network, e.g. 192.168.1.1..192.168.1.100
```

### Run the Script

```bash
bash install.sh
```

## Dynamically Create Underlay Networks via CRD

This approach dynamically creates an Underlay subnet that Pod can use after installation.

### Create ProviderNetwork

ProviderNetwork provides the abstraction of host NIC to physical network mapping, unifies the management of NICs belonging to the same network,
and solves the configuration problems in complex environments with multiple NICs on the same machine, inconsistent NIC names and
inconsistent corresponding Underlay networks.

Create ProviderNetwork as below:

```yml
apiVersion: kubeovn.io/v1
kind: ProviderNetwork
metadata:
  name: net1
spec:
  defaultInterface: eth1
  customInterfaces:
    - interface: eth2
      nodes:
        - node1
  excludeNodes:
    - node2
```

**Note: The length of the ProviderNetwork resource name must not exceed 12.**

- `defaultInterface`: The default node NIC name. When the ProviderNetwork is successfully created, an OVS bridge named br-net1 (in the format `br-NAME`) is created in each node (except excludeNodes) and the specified node NIC is bridged to this bridge.
- `customInterfaces`: Optionally, you can specify the NIC to be used for a specific node.
- `excludeNodes`: Optional, to specify nodes that do not bridge the NIC. Nodes in this list will be added with the `net1.provider-network.ovn.kubernetes.io/exclude=true` tag.

Other nodes will be added with the following tags:

| Key                                               | Value | Description                                                 |
| ------------------------------------------------- | ----- |-------------------------------------------------------------|
| net1.provider-network.ovn.kubernetes.io/ready     | true  | bridge work finished, ProviderNetwork is ready on this node |
| net1.provider-network.ovn.kubernetes.io/interface | eth1  | The name of the bridged NIC in the node.                    |
| net1.provider-network.ovn.kubernetes.io/mtu       | 1500  | MTU of bridged NIC in node                                  |

> If an IP has been configured on the node NIC, the IP address and the route on the NIC are transferred to the corresponding OVS bridge.

### Create VLAN

Vlan provides an abstraction to bind Vlan Tag and ProviderNetwork.

Create a VLAN as below:

```yml
apiVersion: kubeovn.io/v1
kind: Vlan
metadata:
  name: vlan1
spec:
  id: 0
  provider: net1
```

- `id`: VLAN ID/Tag，Kube-OVN will add this Vlan tag to traffic, if set 0, no tag is added.
- `provider`: The name of ProviderNetwork. Multiple VLAN can use a same ProviderNetwork.

### Create Subnet

Bind Vlan to a Subnet as below：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
   name: subnet1
spec:
   protocol: IPv4
   cidrBlock: 172.17.0.0/16
   gateway: 172.17.0.1
   vlan: vlan1
```

Simply specify the value of `vlan` as the name of the VLAN to be used. Multiple subnets can refer to the same VLAN.

## Create Pod

You can create containers in the normal way, check whether the container IP is in the specified range
and whether the container can interoperate with the physical network.

For fixed IP requirements, please refer to [Fixed Addresses](../guide/static-ip-mac.en.md)

## Logical Gateway

For cases where no gateway exists in the physical network, Kube-OVN supports the use of logical gateways configured in the subnet in Underlay mode.
To use this feature, set `spec.logicalGateway` to `true` for the subnet:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
   name: subnet1
spec:
   protocol: IPv4
   cidrBlock: 172.17.0.0/16
   gateway: 172.17.0.1
   vlan: vlan1
   logicalGateway: true
```

When this feature is turned on, the Pod does not use an external gateway,
but a Logical Router created by Kube-OVN to forward cross-subnet communication.
