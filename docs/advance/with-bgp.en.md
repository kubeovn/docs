# BGP Support

Kube-OVN supports broadcasting the IP address of the Pod or Subnet to the outside world via BGP protocol,
so that the outside world can access the Pod directly through the Pod IP.
To use this feature, you need to install `kube-ovn-speaker` on specific nodes and
add the corresponding annotation to the Pod or Subnet that needs to be exposed to the outside world.

## Install kube-ovn-speaker

`kube-ovn-speaker` use [GoBGP](https://osrg.github.io/gobgp/) to publish routing information to the outside world and
set the next-hop route to itself.

Since the node where `kube-ovn-speaker` is deployed needs to carry return traffic, specific labeled nodes need to be selected for deployment:

```bash
kubectl label nodes speaker-node-1 ovn.kubernetes.io/bgp=true
kubectl label nodes speaker-node-2 ovn.kubernetes.io/bgp=true
```

> When there are multiple instances of kube-ovn-speaker,
> each of them will publish routes to the outside world, the upstream router needs to support multi-path ECMP.

Download the corresponding yaml:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/yamls/speaker.yaml
```

Modify the corresponding configuration in yaml:

```yaml
--neighbor-address=10.32.32.1
--neighbor-as=65030
--cluster-as=65000
```

- `neighbor-address`: The address of the BGP Peer, usually the router gateway address.
- `neighbor-as`: The AS number of the BGP Peer.
- `cluster-as`: The AS number of the container network.

Deploy yaml:

```bash
kubectl apply -f speaker.yaml
```

## Publish Pod/Subnet Routes

To use BGP for external routing, first set `natOutgoing` to `false` for the corresponding Subnet to allow the Pod IP to enter the underlying network directly.

Add annotation to publish routes:

```bash
kubectl annotate pod sample ovn.kubernetes.io/bgp=true
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp=true
```

Delete annotation to disable the publishing:

```bash
kubectl annotate pod perf-ovn-xzvd4 ovn.kubernetes.io/bgp-
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp-
```

## BGP Advance Options

`kube-ovn-speaker` supports more BGP parameters for advanced configuration, which can be adjusted by users according to their network environment:

- `announce-cluster-ip`: Whether to publish Service routes to the public, default is `false`.
- `auth-password`: The access password for the BGP peer.
- `holdtime`: The heartbeat detection time between BGP neighbors. Neighbors with no messages after the change time will be removed, the default is 90 seconds.
- `graceful-restart`: Whether to enable BGP Graceful Restart.
- `graceful-restart-time`: BGP Graceful restart time refer to RFC4724 3.
- `graceful-restart-deferral-time`: BGP Graceful restart deferral time refer to RFC4724 4.1.
- `passivemode`: The Speaker runs in Passive mode and does not actively connect to the peer.
- `ebgp-multihop`: The TTL value of EBGP Peer, default is 1.
