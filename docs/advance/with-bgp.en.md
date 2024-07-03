# BGP Support

Kube-OVN supports broadcasting the IP address of Pods/Subnets to the outside world via the BGP protocol,
so that the outside world can access the Pods directly through their Pod IP.
To use this feature, you need to install `kube-ovn-speaker` on specific nodes and
add the corresponding annotation to the Pod or Subnet that needs to be exposed to the outside world.

Kube-OVN also supports broadcasting the IP address of services of type `ClusterIP` via the same annotation.

## Installing `kube-ovn-speaker`

`kube-ovn-speaker` uses [GoBGP](https://osrg.github.io/gobgp/) to publish routing information to the outside world and to
set the `next-hop` route to itself.

Since the nodes where `kube-ovn-speaker` is deployed need to carry return traffic, specific labeled nodes need to be selected for deployment:

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

Apply the YAML:

```bash
kubectl apply -f speaker.yaml
```

## Publishing Pod/Subnet Routes

To use BGP for external routing, first set `natOutgoing` to `false` for the corresponding Subnet to allow the Pod IP to enter the underlying network directly.

Add annotation to publish routes:

```bash
kubectl annotate pod sample ovn.kubernetes.io/bgp=true
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp=true
```

Delete annotation to disable the publishing:

```bash
kubectl annotate pod sample ovn.kubernetes.io/bgp-
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp-
```

## Publishing Services of type `ClusterIP`

To announce the ClusterIP of services to the outside world, the `kube-ovn-speaker` option `announce-cluster-ip` needs to be set to `true`.
See the advanced options for more details.

Set the annotation to enable publishing:

```bash
kubectl annotate service sample ovn.kubernetes.io/bgp=true
```

Delete annotation to disable the publishing:

```bash
kubectl annotate service sample ovn.kubernetes.io/bgp-
```

## Announcement policies

There are 2 policies used by `kube-ovn-speaker` to announce the routes:

- **Cluster**: this policy makes the Pod IPs/Subnet CIDRs be announced from every speaker, whether there's Pods
that have that specific IP or that are part of the Subnet CIDR on that node. In other words, traffic may enter from
any node hosting a speaker, and then be internally routed in the cluster to the actual Pod. In this configuration
extra hops might be used. This is the default policy to Pods and Subnets.
- **Local**: this policy makes the Pod IPs be announced only from speakers on nodes that are actively hosting
them. In other words, traffic will only enter from the node hosting the Pod marked as needing BGP advertisement,
or from the node hosting a Pod with an IP belonging to a Subnet marked as needing BGP advertisement.
This makes the network path shorter as external traffic arrives directly to the physical host of the Pod.

NOTE: You'll probably need to run `kube-ovn-speaker` on every node for the`Local` policy to work.
If a Pod you're trying to announce lands on a node with no speaker on it, its IP will simply not be announced.

The default policy used is `Cluster`. Policies can be overridden for each Pod/Subnet using the `ovn.kubernetes.io/bgp` annotation:

- `ovn.kubernetes.io/bgp=cluster` or the default `ovn.kubernetes.io/bgp=yes` will use policy `Cluster`
- `ovn.kubernetes.io/bgp=local` will use policy `Local`

NOTE: Announcement of Services of type `ClusterIP` doesn't support any policy other than `Cluster` as routing to the actual pod
is handled by a daemon such as `kube-proxy`. The annotation for Services only supports value `yes` and not `cluster`.

## BGP Advanced Options

`kube-ovn-speaker` supports more BGP parameters for advanced configuration, which can be adjusted by users according to their network environment:

- `announce-cluster-ip`: Whether to publish routes for Services of type `ClusterIP` to the public, default is `false`.
- `auth-password`: The access password for the BGP peer.
- `holdtime`: The heartbeat detection time between BGP neighbors. Neighbors with no messages after the change time will be removed, the default is 90 seconds.
- `graceful-restart`: Whether to enable BGP Graceful Restart.
- `graceful-restart-time`: BGP Graceful restart time refer to RFC4724 3.
- `graceful-restart-deferral-time`: BGP Graceful restart deferral time refer to RFC4724 4.1.
- `passivemode`: The Speaker runs in Passive mode and does not actively connect to the peer.
- `ebgp-multihop`: The TTL value of EBGP Peer, default is 1.
