# EIP and SNAT

> This configuration is for the network under the default VPC. User-defined VPCs support two types of NAT. Please refer to:

- [VPC Iptables NAT Gateway](../vpc/vpc.md)
- [VPC OVN NAT Gateway](../vpc/ovn-eip-fip-snat.md)

> Any VPC supports the use of any one or more external subnets, but some factors need to be considered:

- If the user only needs to use the OVN NAT function for subnets under the default VPC and uses it through the pod annotation method, please refer to the current documentation.

- If the subnets under any VPC of the user need to use the OVN NAT function, or wish to maintain one or more external networks through provider network, vlan, subnet CRD, as well as through OVN-EIP, OVN-DNAT, OVN-FIP, For maintaining EIP and NAT, please refer to ovn-snat CRD [VPC OVN NAT Gateway](../vpc/ovn-eip-fip-snat.md).

- If the subnets under any VPC of the user need to use the Iptables NAT function, please refer to [VPC Iptables NAT Gateway](../vpc/vpc.md).

Kube-OVN supports SNAT and EIP functionality at the Pod level using the L3 Gateway feature in OVN.
By using SNAT, a group of Pods can share an IP address for external access. With the EIP feature, a Pod can be directly associated with an external IP.
External services can access the Pod directly through the EIP, and the Pod will also access external services through this EIP.

![](../static/eip-snat.png)

## Advanced Configuration

> To support this feature, if you need to directly specify a default external subnet name, you may need to set startup arguments for kube-ovn-controller.
Some args of `kube-ovn-controller` allow for advanced configuration of SNAT and EIP:

- `--external-gateway-config-ns`: The Namespace of Configmap `ovn-external-gw-config`, default is `kube-system`.
- `--external-gateway-net`: The name of the bridge to which the physical NIC is bridged, default is `external`.
- `--external-gateway-vlanid`: Physical network Vlan Tag number, default is 0, i.e. no Vlan is used.

## Preparation

- In order to use the OVN's L3 Gateway capability, a separate NIC must be bridged into the OVS bridge for overlay and underlay network communication.
  The host must have other NICs for management.
- Since packets passing through NAT will go directly to the Underlay network, it is important to confirm that such packets can pass safely on the current network architecture.
- Currently, there is no conflict detection for EIP and SNAT addresses, and an administrator needs to manually assign them to avoid address conflicts.

## Create Config

Create ConfigMap `ovn-external-gw-config` in `kube-system` Namespace:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-external-gw-config
  namespace: kube-system
data:
  enable-external-gw: "true"
  # external-gw-switch: "external"
  external-gw-nodes: "kube-ovn-worker"
  external-gw-nic: "eth1"
  external-gw-addr: "172.56.0.1/16"
  nic-ip: "172.56.0.254/16"
  nic-mac: "16:52:f3:13:6a:25"
```

- `enable-external-gw`: Whether to enable SNAT and EIP functions.
- `type`: `centralized` or `distributed`, Default is `centralized` If `distributed` is used, all nodes of the cluster need to have the same name NIC to perform the gateway function.
- `external-gw-nodes`: In `centralized` mode, the names of the node performing the gateway role, comma separated.
- `external-gw-nic`: The name of the NIC that performs the role of a gateway on the node.
- `external-gw-addr`: The IP and mask of the physical network gateway.
- `nic-ip`,`nic-mac`: The IP and Mac assigned to the logical gateway port needs to be an unoccupied IP and Mac for the physical subnet.
- `external-gw-switch`: Reuse the name of an existing underlay subnet logical switch. If you are using the default external of `--external-gateway-net`, then this value is omitted. But if you want to reuse an existing underlay subnet CR, then you can just configure `external-gw-switch: "your-subnet-name"`, and the others can be left unconfigured, because the network has already been maintained through the underlay subnet.

## Confirm the Configuration Take Effect

Check the OVN-NB status to confirm that the `ovn-external` logical switch exists and that the correct address and
chassis are bound to the `ovn-cluster-ovn-external` logical router port.

```bash
# kubectl ko nbctl show
switch 3de4cea7-1a71-43f3-8b62-435a57ef16a6 (external)
    port localnet.external
        type: localnet
        addresses: ["unknown"]
    port external-ovn-cluster
        type: router
        router-port: ovn-cluster-external
router e1eb83ad-34be-4ed5-9a02-fcc8b1d357c4 (ovn-cluster)
    port ovn-cluster-external
        mac: "ac:1f:6b:2d:33:f1"
        networks: ["172.56.0.100/16"]
        gateway chassis: [a5682814-2e2c-46dd-9c1c-6803ef0dab66]
```

Check the OVS status to confirm that the corresponding NIC is bridged into the `br-external` bridge:

```bash
# kubectl ko vsctl ${gateway node name} show
e7d81150-7743-4d6e-9e6f-5c688232e130
    Bridge br-external
        Port br-external
            Interface br-external
                type: internal
        Port eth1
            Interface eth1
        Port patch-localnet.external-to-br-int
            Interface patch-localnet.external-to-br-int
                type: patch
                options: {peer=patch-br-int-to-localnet.external}
```

## Config EIP and SNAT on Pod

SNAT and EIP can be configured by adding the `ovn.kubernetes.io/snat` or `ovn.kubernetes.io/eip` annotation to the Pod, respectively:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-snat
  annotations:
    ovn.kubernetes.io/snat: 172.56.0.200
spec:
  containers:
  - name: pod-snat
    image: docker.io/library/nginx:alpine
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-eip
  annotations:
    ovn.kubernetes.io/eip: 172.56.0.233
spec:
  containers:
  - name: pod-eip
    image: docker.io/library/nginx:alpine
```

The EIP or SNAT rules configured by the Pod can be dynamically adjusted via kubectl or other tools,
remember to remove the `ovn.kubernetes.io/routed` annotation to trigger the routing change.

```bash
kubectl annotate pod pod-gw ovn.kubernetes.io/eip=172.56.0.221 --overwrite
kubectl annotate pod pod-gw ovn.kubernetes.io/routed-
```

When the EIP or SNAT takes into effect, the `ovn.kubernetes.io/routed` annotation will be added back.
