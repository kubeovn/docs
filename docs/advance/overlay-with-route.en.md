# Interconnection with Routes in Overlay Mode

In some scenarios, the network environment does not support Underlay mode,
but still need Pods and external devices directly access through IP,
then you can use the routing method to connect the container network and the external.

> Only Overlay Subnets in default VPC support this method. In this case, the Pod IP goes directly to the underlying network,
> which needs to disable IP checks for source and destination addresses.

## Prerequisites

- In this mode, the host needs to open the `ip_forward`.
- Check if there is a `Drop` rule in the forward chain in the host iptables that should be modified for container-related traffic.
- Due to the possibility of asymmetric routing, the host needs to allow packets with a ct status of `INVALID`.

## Steps

For subnets that require direct external routing, you need to set `natOutgoing` of the subnet to `false`
to turn off nat mapping and make the Pod IP directly accessible to the external network.

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: routed
spec:
  protocol: IPv4
  cidrBlock: 10.166.0.0/16
  default: false
  excludeIps:
  - 10.166.0.1
  gateway: 10.166.0.1
  gatewayType: distributed
  natOutgoing: false
```

At this point, the Pod's packets can reach the peer node via the host route,
but the peer node does not yet know where the return packets should be sent to and needs to add a return route.

If the peer host and the container host are on the same Layer 2 network,
we can add a static route directly to the peer host to point the next hop of the container network to any machine in the Kubernetes cluster.

```bash
ip route add 10.166.0.0/16 via 192.168.2.10 dev eth0
```

`10.166.0.0/16` is the container subnet CIDR, and `192.168.2.10` is one node in the Kubernetes cluster.

If the peer host and the container host are not in the same layer 2 network, you need to configure the corresponding rules on the router.

*Note*: Specifying an IP for a single node may lead to single point of failure. To achieve fast failover, Keepalived can be used to set up a VIP for multiple nodes, and the next hop of the route can be directed to the VIP.

In some virtualized environments, the virtual network identifies asymmetric traffic as illegal traffic and drops it.
In this case, you need to adjust the `gatewayType` of the Subnet to `centralized` and set the next hop to the IP of the `gatewayNode` node during route setup.

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: routed
spec:
  protocol: IPv4
  cidrBlock: 10.166.0.0/16
  default: false
  excludeIps:
  - 10.166.0.1
  gateway: 10.166.0.1
  gatewayType: centralized
  gatewayNode: "node1"
  natOutgoing: false
```
