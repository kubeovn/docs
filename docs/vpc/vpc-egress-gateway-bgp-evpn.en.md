# Egress Gateway BGP and EVPN Support

!!! warning "Experimental Feature"

    BGP and EVPN support is currently an experimental feature and may change in future releases. We welcome more usage and feedback to help improve this feature.

    The following limitations currently apply:

    - Only L3VPN is implemented; L2VPN is not yet supported
    - FRR hot reload is not supported (configuration changes require Pod restart)
    - BFD for BGP is not supported

## Overview

[VPC Egress Gateway](./vpc-egress-gateway.en.md) supports establishing dynamic routing with external networks through BGP and EVPN/VXLAN. The main architecture involves running an FRR (Free Range Routing) container within the Egress Gateway Pod to handle the BGP and EVPN control and data planes. The gateway init container automatically renders FRR configuration from BgpConf and EvpnConf resources.

When BGP is enabled, the Egress Gateway establishes BGP neighbor relationships with external routers to advertise and learn routes. When EVPN is enabled, the init script creates Linux VRF, bridge, and VXLAN devices within the Pod, using the L2VPN EVPN address family for route exchange. VXLAN encapsulation only takes place in the Egress Gateway Pod; the network between Kubernetes nodes still uses Geneve.

> This feature is different from the [BGP Support](../advance/with-bgp.en.md) in advanced features, which uses kube-ovn-speaker for Pod/Subnet/Service route advertisement.

## Requirements

Before using BGP/EVPN, ensure that the [VPC Egress Gateway](./vpc-egress-gateway.en.md) requirements are met, including the deployment of [Multus-CNI](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/quickstart.md){: target="_blank" }.

Additionally, an external router or network device that supports BGP (and optionally EVPN) is required as a BGP neighbor.

## Usage

### Creating a BgpConf Resource

BgpConf is a cluster-scoped resource used to define BGP configuration. Example:

```yaml
apiVersion: kubeovn.io/v1
kind: BgpConf
metadata:
  name: bgp-conf-6502
spec:
  localASN: 65002
  peerASN: 65001
  neighbours:
    - 10.0.1.1
  holdTime: 90s
  keepaliveTime: 30s
  connectTime: 10s
  ebgpMultiHop: true
```

The above resource defines a BGP configuration with local AS number 65002, peer AS number 65001, neighbor address 10.0.1.1, and EBGP Multi-Hop enabled.

### Creating an EvpnConf Resource

EvpnConf is a cluster-scoped resource used to define EVPN configuration. EvpnConf must be used together with BgpConf and cannot be used standalone. Example:

```yaml
apiVersion: kubeovn.io/v1
kind: EvpnConf
metadata:
  name: evpn-conf-1016
spec:
  vni: 1016
  routeTargets:
    - "65000:1016"
```

The above resource defines an EVPN configuration with VNI 1016 and Route Target `65000:1016`.

### Creating a VPC Egress Gateway with BGP/EVPN

First, create the NetworkAttachmentDefinition and corresponding subnet following the [VPC Egress Gateway](./vpc-egress-gateway.en.md) documentation.

Then reference the corresponding configuration resources via the `bgpConf` and `evpnConf` fields in the VpcEgressGateway `.spec`. Example:

```yaml
apiVersion: kubeovn.io/v1
kind: VpcEgressGateway
metadata:
  name: gateway1
  namespace: default
spec:
  vpc: ovn-cluster
  replicas: 1
  externalIPs:
    - 10.0.1.13
  internalIPs:
    - 10.16.0.13
  externalSubnet: macvlan1
  bgpConf: bgp-conf-6502
  evpnConf: evpn-conf-1016
  policies:
    - snat: false
      subnets:
        - ovn-default
    - snat: false
      ipBlocks:
        - 10.17.0.0/16
```

The above resource creates a VPC Egress Gateway with BGP and EVPN enabled. An FRR container runs inside the Gateway Pod, exchanging routing information with external routers via BGP EVPN and forwarding traffic through VXLAN tunnels. Since routing is managed by BGP/EVPN, `snat` in the policies is set to `false`.

### Using BGP Only (Without EVPN)

If you only need BGP for route advertisement without EVPN/VXLAN, set only the `bgpConf` field without setting `evpnConf`. In this mode, FRR runs pure BGP with the IPv4 Unicast address family. Example:

```yaml
apiVersion: kubeovn.io/v1
kind: VpcEgressGateway
metadata:
  name: gateway-bgp-only
  namespace: default
spec:
  vpc: ovn-cluster
  replicas: 1
  externalSubnet: macvlan1
  bgpConf: bgp-conf-6502
  policies:
    - snat: true
      subnets:
        - ovn-default
```

## Configuration Parameters

### BgpConf

| Fields | Type | Optional | Default Value | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `localASN` | `uint32` | No | - | Local AS number. | `65002` |
| `peerASN` | `uint32` | No | - | Peer AS number. | `65001` |
| `routerId` | `string` | Yes | Pod IP | BGP Router ID. | `10.0.1.13` |
| `neighbours` | `string array` | No | - | List of BGP neighbor IP addresses. | `10.0.1.1` |
| `password` | `string` | Yes | - | BGP authentication password. | `secret` |
| `holdTime` | `string (duration)` | Yes | - | BGP Hold time. | `90s` |
| `keepaliveTime` | `string (duration)` | Yes | - | BGP Keepalive time. | `30s` |
| `connectTime` | `string (duration)` | Yes | - | BGP connect timer. | `10s` |
| `ebgpMultiHop` | `boolean` | Yes | `false` | Whether to enable EBGP Multi-Hop. | `true` |

### EvpnConf

| Fields | Type | Optional | Default Value | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `vni` | `uint32` | No | - | VXLAN Network Identifier. | `1016` |
| `routeTargets` | `string array` | No | - | List of Route Targets for import and export. | `65000:1016` |

### New VpcEgressGateway Fields

The following fields are BGP/EVPN-related additions to the VpcEgressGateway `.spec`. For the complete VpcEgressGateway configuration parameters, refer to [Egress Gateway Configuration Parameters](./vpc-egress-gateway.en.md#configuration-parameters).

| Fields | Type | Optional | Default Value | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bgpConf` | `string` | Yes | - | Name of the referenced BgpConf resource. Enables BGP in the Egress Gateway. | `bgp-conf-6502` |
| `evpnConf` | `string` | Yes | - | Name of the referenced EvpnConf resource. Requires `bgpConf` to be set. Enables EVPN/VXLAN in the Egress Gateway. | `evpn-conf-1016` |
