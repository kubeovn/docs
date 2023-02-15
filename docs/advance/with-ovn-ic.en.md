# Cluster Inter-Connection with OVN-IC

Kube-OVN supports interconnecting two Kubernetes cluster Pod networks via [OVN-IC](https://docs.ovn.org/en/latest/tutorials/ovn-interconnection.html),
and the Pods in the two clusters can communicate directly via Pod IPs .
Kube-OVN uses tunnels to encapsulate cross-cluster traffic, allowing container networks to interconnect between two clusters
as long as there is a set of IP reachable machines.

> This mode of multi-cluster interconnection is for Overlay network.
> For Underlay network, it needs the underlying infrastructure to do the inter-connection work.

![](../static/inter-connection.png)

## Prerequisites

1. The subnet CIDRs within OpenStack and Kubernetes cannot overlap with each other in auto-interconnect mode.
   If there is overlap, you need to refer to the subsequent manual interconnection process, which can only connect non-overlapping Subnets.
2. A set of machines needs to exist that can be accessed by each cluster over the network and used to deploy controllers that interconnect across clusters.
3. Each cluster needs to have a set of machines that can access each other across clusters via IP as the gateway nodes.
4. This solution only connects to the Kubernetes default VPCs.

## Deploy a single-node OVN-IC DB

Deploy the `OVN-IC` DB on a machine accessible by `kube-ovn-controller`, This DB will hold the network configuration information synchronized up from each cluster.

An environment deploying `docker` can start the `OVN-IC` DB with the following command.

```bash
docker run --name=ovn-ic-db -d --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

For deploying a `containerd` environment instead of `docker` you can use the following command:

```bash
ctr -n k8s.io run -d --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

## Automatic Routing Mode

In auto-routing mode, each cluster synchronizes the CIDR information of the Subnet under its own default VPC to `OVN-IC`,
so make sure there is no overlap between the Subnet CIDRs of the two clusters.

Create `ovn-ic-config` ConfigMap in `kube-system` Namespace:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-ic-config
  namespace: kube-system
data:
  enable-ic: "true"
  az-name: "az1" 
  ic-db-host: "192.168.65.3"
  ic-nb-port: "6645" 
  ic-sb-port: "6646"
  gw-nodes: "az1-gw"
  auto-route: "true"
```

- `enable-ic`: Whether to enable cluster interconnection.
- `az-name`: Distinguish the cluster names of different clusters, each interconnected cluster needs to be different.
- `ic-db-host`: Address of the node where the `OVN-IC` DB is deployed.
- `ic-nb-port`: `OVN-IC` Northbound Database port, default 6645.
- `ic-sb-port`: `OVN-IC` Southbound Database port, default 6645.
- `gw-nodes`: The name of the nodes in the cluster interconnection that takes on the work of the gateways, separated by commas.
- `auto-route`: Whether to automatically publish and learn routes.

**Note:** To ensure the correct operation, the ConfigMap `ovn-ic-config` is not allowed to be modified.
If any parameter needs to be changed, please delete this ConfigMap, modify it and then apply it again.

Check if the interconnected logical switch `ts` has been established in the `ovn-ic` container with the following command：

```bash
# ovn-ic-sbctl show
availability-zone az1
    gateway deee03e0-af16-4f45-91e9-b50c3960f809
        hostname: az1-gw
        type: geneve
            ip: 192.168.42.145
        port ts-az1
            transit switch: ts
            address: ["00:00:00:50:AC:8C 169.254.100.45/24"]
availability-zone az2
    gateway e94cc831-8143-40e3-a478-90352773327b
        hostname: az2-gw
        type: geneve
            ip: 192.168.42.149
        port ts-az2
            transit switch: ts
            address: ["00:00:00:07:4A:59 169.254.100.63/24"]
```

At each cluster observe if logical routes have learned peer routes:

```bash
# kubectl ko nbctl lr-route-list ovn-cluster
IPv4 Routes
                10.42.1.1            169.254.100.45 dst-ip (learned)
                10.42.1.3                100.64.0.2 dst-ip
                10.16.0.2                100.64.0.2 src-ip
                10.16.0.3                100.64.0.2 src-ip
                10.16.0.4                100.64.0.2 src-ip
                10.16.0.6                100.64.0.2 src-ip
             10.17.0.0/16            169.254.100.45 dst-ip (learned)
            100.65.0.0/16            169.254.100.45 dst-ip (learned)
```

Next, you can try `ping` a Pod IP in Cluster 1 directly from a Pod in Cluster 2 to see if you can work.

For a subnet that does not want to automatically publish routes to the other end,
you can disable route broadcasting by modifying `disableInterConnection` in the Subnet spec.

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: no-advertise
spec:
  cidrBlock: 10.199.0.0/16
  disableInterConnection: true
```

## Manual Routing Mode

For cases where there are overlapping CIDRs between clusters,
and you only want to do partial subnet interconnection, you can manually publish subnet routing by following the steps below.

Create `ovn-ic-config` ConfigMap in `kube-system` Namespace, and set `auto-route` to `false`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-ic-config
  namespace: kube-system
data:
  enable-ic: "true"
  az-name: "az1" 
  ic-db-host: "192.168.65.3"
  ic-nb-port: "6645" 
  ic-sb-port: "6646"
  gw-nodes: "az1-gw"
  auto-route: "false"
```

Find the address of the remote logical ports in each cluster separately, for later manual configuration of the route:

```bash
[root@az1 ~]# kubectl ko nbctl show
switch a391d3a1-14a0-4841-9836-4bd930c447fb (ts)
    port ts-az1
        type: router
        router-port: az1-ts
    port ts-az2
        type: remote
        addresses: ["00:00:00:4B:E2:9F 169.254.100.31/24"]

[root@az2 ~]# kubectl ko nbctl show
switch da6138b8-de81-4908-abf9-b2224ec4edf3 (ts)
    port ts-az2
        type: router
        router-port: az2-ts
    port ts-az1
        type: remote
        addresses: ["00:00:00:FB:2A:F7 169.254.100.79/24"]        
        
```

The output above shows that the remote address from cluster `az1` to cluster `az2` is `169.254.100.31`
and the remote address from `az2` to `az1` is `169.254.100.79`.

In this example, the subnet CIDR within cluster `az1` is `10.16.0.0/24` and the subnet CIDR within cluster `az2` is `10.17.0.0/24`.

Set up a route from cluster `az1` to cluster `az2` in cluster `az1`:

```bash
kubectl ko nbctl lr-route-add ovn-cluster 10.17.0.0/24 169.254.100.31
```

Set up a route to cluster `az1` in cluster `az2`:

```bash
kubectl ko nbctl lr-route-add ovn-cluster 10.16.0.0/24 169.254.100.79
```

## Highly Available OVN-IC DB Installation

A highly available cluster can be formed between `OVN-IC` DB via the Raft protocol, which requires a minimum of 3 nodes for this deployment model.

First start the leader of the `OVN-IC` DB on the first node.

Users deploying a `docker` environment can use the following command:

```bash
docker run --name=ovn-ic-db -d --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn -e LOCAL_IP="192.168.65.3"  -e NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"   kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

If you are  using `containerd` you can use the following command:

```bash
ctr -n k8s.io run -d --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw"  --env="NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"" --env="LOCAL_IP="192.168.65.3"" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

- `LOCAL_IP`： The IP address of the node where the current container is located.
- `NODE_IPS`： The IP addresses of the three nodes running the `OVN-IC` database, separated by commas.

Next, deploy the follower of the `OVN-IC` DB on the other two nodes.

`docker` environment can use the following command.

```bash
docker run --name=ovn-ic-db -d --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn -e LOCAL_IP="192.168.65.2"  -e NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1" -e LEADER_IP="192.168.65.3"  kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

If using `containerd` you can use the following command:

```bash
ctr -n k8s.io run -d --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw"  --env="NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"" --env="LOCAL_IP="192.168.65.2"" --env="LEADER_IP="192.168.65.3"" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

- `LOCAL_IP`： The IP address of the node where the current container is located.
- `NODE_IPS`： The IP addresses of the three nodes running the `OVN-IC` database, separated by commas.
- `LEADER_IP`: The IP address of the `OVN-IC` DB leader node.

Specify multiple `OVN-IC` database node addresses when creating `ovn-ic-config` for each cluster:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-ic-config
  namespace: kube-system
data:
  enable-ic: "true"
  az-name: "az1" 
  ic-db-host: "192.168.65.3,192.168.65.2,192.168.65.1"
  ic-nb-port: "6645"
  ic-sb-port: "6646"
  gw-nodes: "az1-gw"
  auto-route: "true"
```

## Manual Reset

In some cases, the entire interconnection configuration needs to be cleaned up due to configuration errors,
you can refer to the following steps to clean up your environment.

Delete the current `ovn-ic-config` Configmap:

```bash
kubectl -n kube-system delete cm ovn-ic-config
```

Delete `ts` logical switch:

```bash
kubectl-ko nbctl ls-del ts
```

Repeat the same steps at the peer cluster.
