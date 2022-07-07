# EIP and SNAT

> This configuration is for the network under default VPC, 
> for custom VPC please refer to [VPC Gateway](./vpc.en.md#create-vpc-nat-gateway)

Kube-OVN supports SNAT and EIP functionality at the Pod level using the L3 Gateway feature in OVN.
By using SNAT, a group of Pods can share an IP address for external access. With the EIP feature, a Pod can be directly associated with an external IP.
External services can access the Pod directly through the EIP, and the Pod will also access external services through this EIP.

![](../static/eip-snat.png)

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
  external-gw-nodes: "kube-ovn-worker"
  external-gw-nic: "eth1"
  external-gw-addr: "172.56.0.1/16"
  nic-ip: "172.56.0.254/16"
  nic-mac: "16:52:f3:13:6a:25"
```

- `enable-external-gw`: Whether to enable SNAT and EIP functions.
- `type`: `centrailized` or `distributed`， Default is `centralized` If `distributed` is used, all nodes of the cluster need to have the same name NIC to perform the gateway function.
- `external-gw-nodes`: In `centralized` mode，The names of the node performing the gateway role, comma separated.
- `external-gw-nic`: The name of the NIC that performs the role of a gateway on the node.
- `external-gw-addr`: The IP and mask of the physical network gateway.
- `nic-ip`,`nic-mac`: The IP and Mac assigned to the logical gateway port needs to be an unoccupied IP and Mac for the physical subnet.

## Confirm the Configuration Take Effect

Check the OVN-NB status to confirm that the `ovn-external` logical switch exists and that the correct address and 
chassis are bound to the `ovn-cluster-ovn-external` logical router port.

```bash
# kubectl ko nbctl show
switch 3de4cea7-1a71-43f3-8b62-435a57ef16a6 (ovn-external)
    port ln-ovn-external
        type: localnet
        addresses: ["unknown"]
    port ovn-external-ovn-cluster
        type: router
        router-port: ovn-cluster-ovn-external
router e1eb83ad-34be-4ed5-9a02-fcc8b1d357c4 (ovn-cluster)
    port ovn-cluster-ovn-external
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
        Port eno2
            Interface eno2
        Port patch-ln-ovn-external-to-br-int
            Interface patch-ln-ovn-external-to-br-int
                type: patch
                options: {peer=patch-br-int-to-ln-ovn-external}
```

## Config EIP amd SNAT on Pod

SNAT and EIP can be configured by adding the `ovn.kubernetes.io/snat` or `ovn.kubernetes.io/eip` annotation to the Pod, respectively:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-gw
  annotations:
    ovn.kubernetes.io/snat: 172.56.0.200
spec:
  containers:
  - name: snat-pod
    image: nginx:alpine
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-gw
  annotations:
    ovn.kubernetes.io/eip: 172.56.0.233
spec:
  containers:
  - name: eip-pod
    image: nginx:alpine
```

The EIP or SNAT rules configured by the Pod can be dynamically adjusted via kubectl or other tools, 
remember to remove the `ovn.kubernetes.io/routed` annotation to trigger the routing change.

```bash
kubectl annotate pod pod-gw ovn.kubernetes.io/eip=172.56.0.221 --overwrite
kubectl annotate pod pod-gw ovn.kubernetes.io/routed-
```

## Advanced Configuration

Some args of `kube-ovn-controller` allow for advanced configuration of SNAT and EIP:

- `--external-gateway-config-ns`: The Namespace of Configmap `ovn-external-gw-config`, default is `kube-system`。
- `--external-gateway-net`: The name of the bridge to which the physical NIC is bridged, default is `external`.
- `--external-gateway-vlanid`: Physical network Vlan Tag number, default is 0, i.e. no Vlan is used.
