# Overlay Encapsulation NIC Selection

In some scenarios, users want the container Overlay network to use different NICs on the host for tunnel encapsulation, enabling:

- **Storage Network Separation**: Storage traffic goes through dedicated high-speed NICs while business traffic uses regular NICs.
- **Business Network Isolation**: Different business subnets use different physical NICs for physical-level network isolation.
- **Bandwidth Control**: Bandwidth isolation through physical NIC separation to prevent traffic interference.

## Default Encapsulation NIC Selection

When a node has multiple NICs, Kube-OVN by default selects the NIC corresponding to the Kubernetes Node IP as the NIC for cross-node container communication and establishes the corresponding tunnel.

If you need to select a different NIC for container tunnels, you can modify it in the installation script:

```bash
IFACE=eth1
```

This option supports comma-separated regular expressions, such as `ens[a-z0-9]*,eth[a-z0-9]*`.

After installation, you can also adjust it by modifying the `kube-ovn-cni` DaemonSet parameters:

```yaml
args:
- --iface=eth1
```

If each machine has different NIC names with no fixed pattern, you can use the node annotation `ovn.kubernetes.io/tunnel_interface` to configure each node individually. Nodes with this annotation will override the `iface` configuration and use the annotation value instead.

```bash
kubectl annotate node no1 ovn.kubernetes.io/tunnel_interface=ethx
```

## Per-Subnet Encapsulation NIC Selection

In addition to the global default encapsulation NIC configuration, Kube-OVN also supports specifying different host NIC IPs for tunnel encapsulation for different subnets, enabling container network traffic forwarding through different host NICs.

### Prerequisites

- The host needs to be configured with multiple NICs, each with an IP address assigned.
- Networks corresponding to each NIC should be interconnected (among hosts within the same network plane).
- This feature only supports Overlay type subnets.

### How It Works

1. Users declare multiple network planes and their corresponding encapsulation IPs on Nodes via annotations.
2. In Subnet, the `nodeNetwork` field specifies which network plane the subnet should use.
3. kube-ovn-daemon monitors node annotation changes and sets all encapsulation IPs to OVS.
4. When a Pod is created, if its subnet has `nodeNetwork` configured, the corresponding encapsulation IP will be set on the Pod's OVS port.

### Configure Node Networks

On nodes that require multi-network plane configuration, add the `ovn.kubernetes.io/node_networks` annotation. The annotation value is in JSON format, where key is the network name and value is the encapsulation IP for that network.

```bash
kubectl annotate node <node-name> ovn.kubernetes.io/node_networks='{"storage": "192.168.100.10", "app": "172.16.0.10"}'
```

The above command defines two network planes:

- `storage`: Uses IP `192.168.100.10` (assuming this IP is configured on a high-speed storage NIC)
- `app`: Uses IP `172.16.0.10` (assuming this IP is configured on a business NIC)

For multi-node clusters, you need to configure the corresponding network annotations on each node, ensuring that the same network name uses IPs from the same network plane on different nodes.

### Configure Subnet

When creating a subnet, specify the network plane through the `spec.nodeNetwork` field:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: storage-subnet
spec:
  protocol: IPv4
  cidrBlock: 10.100.0.0/16
  gateway: 10.100.0.1
  nodeNetwork: storage
```

This configuration indicates that Pods in the `storage-subnet` will use the `storage` network plane for tunnel encapsulation.

If the `nodeNetwork` field is not configured, the subnet will use the default encapsulation IP (the NIC IP specified by the `IFACE` parameter).

### Verify Configuration

#### Check OVS Encapsulation IP Configuration

Execute the following command on a node to view the OVS encapsulation IP configuration:

```bash
ovs-vsctl get open . external-ids:ovn-encap-ip
```

The output should contain all configured encapsulation IPs, for example:

```text
"192.168.1.10,192.168.100.10,172.16.0.10"
```

Check the default encapsulation IP:

```bash
ovs-vsctl get open . external-ids:ovn-encap-ip-default
```

#### Check Pod Port Encapsulation IP

After creating a Pod, you can check the encapsulation IP setting of the Pod's corresponding OVS port:

```bash
ovs-vsctl --columns=external_ids find interface external-ids:iface-id="<pod-name>.<namespace>"
```

If the subnet has `nodeNetwork` configured, the output should contain the `encap-ip` field:

```text
external_ids        : {encap-ip="192.168.100.10", iface-id="test-pod.default", ...}
```

### Usage Example

Here is a complete example of storage network separation:

#### 1. Configure Node Network Annotations

Assuming the cluster has two nodes, each with two NICs:

- `eth0`: Business NIC with IPs `192.168.1.10` and `192.168.1.11`
- `eth1`: Storage NIC with IPs `10.10.10.10` and `10.10.10.11`

```bash
kubectl annotate node node1 ovn.kubernetes.io/node_networks='{"storage": "10.10.10.10"}'
kubectl annotate node node2 ovn.kubernetes.io/node_networks='{"storage": "10.10.10.11"}'
```

#### 2. Create Storage Subnet

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: storage-net
spec:
  protocol: IPv4
  cidrBlock: 10.200.0.0/16
  gateway: 10.200.0.1
  nodeNetwork: storage
  namespaces:
  - storage-namespace
```

#### 3. Create a Pod Using the Storage Network

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
  namespace: storage-namespace
spec:
  containers:
  - name: app
    image: docker.io/library/nginx:alpine
```

The network traffic of this Pod will be forwarded through the storage NIC (`eth1`).

### Notes

1. Ensure all nodes within the same network plane can communicate with each other.
2. The IPs configured in node annotations must be valid IP addresses that actually exist on that node.
3. This feature only applies to Overlay type subnets; Underlay subnets do not support this configuration. For Underlay network configuration, please refer to [Underlay Network Installation](../start/underlay.md).
4. If a subnet does not have `nodeNetwork` configured, or if the configured network name does not exist on the node, the default encapsulation IP will be used.
5. If a Pod is scheduled to a node that does not have the annotation corresponding to the subnet's `nodeNetwork`, the Pod will fail to run. Ensure all nodes that may be scheduled have the corresponding network annotations configured.
6. When adding nodes or adjusting node networks, update the `ovn.kubernetes.io/node_networks` annotation on the corresponding nodes promptly to avoid Pod failures.
