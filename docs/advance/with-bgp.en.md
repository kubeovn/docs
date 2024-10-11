# BGP Support

Kube-OVN supports broadcasting the IP address of Pods/Subnets/Services/EIPs to the outside world via the BGP protocol.  

To use this feature on Pods/Subnets/Services, you need to install `kube-ovn-speaker` on specific (or all) nodes and
add the corresponding annotation to the Pod or Subnet that needs to be exposed to the outside world.  
Kube-OVN also supports broadcasting the IP address of services of type `ClusterIP` via the same annotation.

To use this feature on EIPs, you need to create your NAT Gateway with special parameters to enable the BGP speaker sidecar.
See [Publishing EIPs](#publishing-eips) for more information.

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

If you only have one switch: 

```yaml
- --neighbor-address=10.32.32.254
- --neighbor-ipv6-address=2409:AB00:AB00:2000::AFB:8AFE
- --neighbor-as=65030
- --cluster-as=65000
```

If you have a pair of switches: 

```yaml

- --neighbor-address=10.32.32.252,10.32.32.253
- --neighbor-ipv6-address=2409:AB00:AB00:2000::AFB:8AFC,2409:AB00:AB00:2000::AFB:8AFD
- --neighbor-as=65030
- --cluster-as=65000
```

- `neighbor-address`: The address of the BGP Peer, usually the router gateway address.
- `neighbor-as`: The AS number of the BGP Peer.
- `cluster-as`: The AS number of the container network.

Apply the YAML:

```bash
kubectl apply -f speaker.yaml
```

## Publishing Pod/Subnet Routes

To use BGP for external routing on subnets, first set `natOutgoing` to `false` for the corresponding Subnet to allow the Pod IP to enter the underlying network directly.

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

See [Announcement Policies](#announcement-policies) for the announcement behavior depending on the policy set in the annotation.

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

The speakers will all start announcing the `ClusterIP` of that service to the outside world.

## Publishing EIPs

EIPs can be announced by the NAT gateways to which they are attached.  
There are 2 announcement modes:

- **ARP**: the NAT gateway uses ARP to advertise the EIPs attached to itself, this mode is always enabled
- **BGP**: the NAT gateway provisions a sidecar to publish the EIPs to another BGP speaker

When BGP is enabled on a `VpcNatGateway` a new BGP speaker sidecar gets injected to it. When the gateway is in BGP mode, the behaviour becomes cumulative with the **ARP** mode. This means that EIPs will be announced by **BGP** but also keep being advertised using traditional **ARP**.

To add BGP capabilities to NAT gateways, we first need to create a new `NetworkAttachmentDefinition` that can be attached to our BGP speaker sidecars. This NAD will reference a provider shared by a `Subnet` in the default VPC (in which the Kubernetes API is running).  
This will enable the sidecar to reach the K8S API, automatically detecting new EIPs added to the gateway. This operation only needs to be done once.  All the NAT gateways will use this provider from now on. This is the same principle used for the CoreDNS in a custom VPC, which means you can reuse that NAD if you've already done that setup before.

Create a `NetworkAttachmentDefinition` and a `Subnet` with the same `provider`.
The name of the provider needs to be of the form `nadName.nadNamespace.ovn`:

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: api-ovn-nad
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "api-ovn-nad.default.ovn"
    }'
---
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: vpc-apiserver-subnet
spec:
  protocol: IPv4
  cidrBlock: 100.100.100.0/24
  provider: api-ovn-nad.default.ovn
```

The `ovn-vpc-nat-config` needs to be modified to reference our new provider and the image used by the BGP speaker:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-vpc-nat-config
  namespace: kube-system
data:
  apiNadProvider: api-ovn-nad.default.ovn              # What NetworkAttachmentDefinition provider to use so that the sidecar
                                                       # can access the K8S API, as it can't by default due to VPC segmentation
  bgpSpeakerImage: docker.io/kubeovn/kube-ovn:v1.13.0  # Sets the BGP speaker image used
  image: docker.io/kubeovn/vpc-nat-gateway:v1.13.0
```

Some RBAC needs to be added so that the NAT gateways can poll the Kubernetes API, apply the following configuration:  

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:vpc-nat-gw
rules:
  - apiGroups:
      - ""
    resources:
      - services
      - pods
    verbs:
      - list
      - watch
  - apiGroups:
      - kubeovn.io
    resources:
      - iptables-eips
      - subnets
      - vpc-nat-gateways
    verbs:
      - list
      - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: vpc-nat-gw
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:vpc-nat-gw
subjects:
  - kind: ServiceAccount
    name: vpc-nat-gw
    namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vpc-nat-gw
  namespace: kube-system
```

The NAT gateway(s) now needs to be created with BGP enabled so that the speaker sidecar gets created along it:

```yaml
kind: VpcNatGateway
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-natgw
spec:
  vpc: vpc1
  subnet: net1
  lanIp: 10.0.1.10
  bgpSpeaker:
    enabled: true
    asn: 65500
    remoteAsn: 65000
    neighbors:
      - 100.127.4.161
      - fd:01::1
    enableGracefulRestart: true # Optional
    routerId: 1.1.1.1           # Optional
    holdTime: 1m                # Optional
    password: "password123"     # Optional
    extraArgs:                  # Optional, passed directly to the BGP speaker
      - -v5                     # Enables verbose debugging of the BGP speaker sidecar
  selector:
    - "kubernetes.io/os: linux"
  externalSubnets:
  - ovn-vpc-external-network # Network on which we'll speak BGP and receive/send traffic to the outside world
                             # BGP neighbors need to be on that network
```

This gateway is now capable of announcing any EIP that gets attached to it as long as it has the BGP annotation:

```yaml
kubectl annotate eip sample ovn.kubernetes.io/bgp=true
```

## Announcement policies

There are 2 policies used by `kube-ovn-speaker` to announce the routes:

- **Cluster**: this policy makes the Pod IPs/Subnet CIDRs be announced from every speaker, whether there's Pods
that have that specific IP or that are part of the Subnet CIDR on that node. In other words, traffic may enter from
any node hosting a speaker, and then be internally routed in the cluster to the actual Pod. In this configuration
extra hops might be used. This is the default policy for Pods and Subnets.
- **Local**: this policy makes the Pod IPs be announced only from speakers on nodes that are actively hosting
them. In other words, traffic will only enter from the node hosting the Pod marked as needing BGP advertisement,
or from the node hosting a Pod with an IP belonging to a Subnet marked as needing BGP advertisement.
This makes the network path shorter as external traffic arrives directly to the physical host of the Pod.

**NOTE**: You'll probably need to run `kube-ovn-speaker` on every node for the`Local` policy to work.
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

## BGP routes debug

```bash

# show peer neighbor
gobgp neighbor

# show announced routes to one peer
gobgp neighbor 10.32.32.254 adj-out

```
