# Cluster Inter-Connection with OVN-IC

Kube-OVN supports interconnecting two Kubernetes cluster Pod networks via [OVN-IC](https://docs.ovn.org/en/latest/tutorials/ovn-interconnection.html),
and the Pods in the two clusters can communicate directly via Pod IPs.
Kube-OVN uses tunnels to encapsulate cross-cluster traffic, allowing container networks to interconnect between two clusters
as long as there is a set of IP reachable machines.

> This mode of multi-cluster interconnection is for Overlay network.
> For Underlay network, it needs the underlying infrastructure to do the inter-connection work.

![](../static/inter-connection.png)

!!! note "Limitation"

    The OVN-IC method can only achieve cross-cluster connectivity for Pod IPs and cannot complete cross-cluster connectivity for Services, DNS, and NetworkPolicies. If cross-cluster service discovery capabilities are needed, please consider using Istio or other cross-cluster service governance projects.

## Prerequisites

1. Clusters configured in versions after 1.11.16 have the cluster interconnection switch turned off by default. You need to mark the following in the configuration script `install.sh`:

    ````bash
    ENABLE_IC=true
    ````

    After opening the switch and deploying the cluster, the component deployment ovn-ic-controller will appear.

2. The subnet CIDRs within OpenStack and Kubernetes cannot overlap with each other in auto-interconnect mode.
   If there is overlap, you need to refer to the subsequent manual interconnection process, which can only connect non-overlapping Subnets.
3. A set of machines needs to exist that can be accessed by each cluster over the network and used to deploy controllers that interconnect across clusters.
4. Each cluster needs to have a set of machines that can access each other across clusters via IP as the gateway nodes.
5. This solution only connects to the Kubernetes default VPCs.

## Deploy a single-node OVN-IC DB

### Single node deployment solution 1

Solution 1 is recommended first, supported after Kube-OVN v1.11.16.

This method does not distinguish between "single node" or "multi-node high availability" deployment. The controller will be deployed on the master node in the form of Deployment. The cluster master node is 1, which is a single node deployment, and the number of master nodes is multiple, that is, multi-node. Highly available deployment.

First get the script `install-ovn-ic.sh` and use the following command:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install-ic-server.sh
```

Execute the command installation, where `TS_NUM` represents the number of ECMP Paths connected to the cluster:

```bash
sed 's/VERSION=.*/VERSION={{ variables.version }}/' dist/images/install-ic-server.sh | TS_NUM=3 bash
```

The output of successful execution is as follows:

```bash
deployment.apps/ovn-ic-server created
Waiting for deployment spec update to be observed...
Waiting for deployment "ovn-ic-server" rollout to finish: 0 out of 3 new replicas have been updated...
Waiting for deployment "ovn-ic-server" rollout to finish: 0 of 3 updated replicas are available...
Waiting for deployment "ovn-ic-server" rollout to finish: 1 of 3 updated replicas are available...
Waiting for deployment "ovn-ic-server" rollout to finish: 2 of 3 updated replicas are available...
deployment "ovn-ic-server" successfully rolled out
OVN IC Server installed Successfully
```

You can view the status of the current interconnected controller through the `kubectl ko icsbctl show` command. The command is as follows:

```bash
kubectl ko icsbctl show
availability-zone az0
    gateway 059b5c54-c540-4d77-b009-02d65f181a02
        hostname: kube-ovn-worker
        type: geneve
            ip: 172.18.0.3
        port ts-az0
            transit switch: ts
            address: ["00:00:00:B4:8E:BE 169.254.100.97/24"]
    gateway 74ee4b9a-ba48-4a07-861e-1a8e4b9f905f
        hostname: kube-ovn-worker2
        type: geneve
            ip: 172.18.0.2
        port ts1-az0
            transit switch: ts1
            address: ["00:00:00:19:2E:F7 169.254.101.90/24"]
    gateway 7e2428b6-344c-4dd5-a0d5-972c1ccec581
        hostname: kube-ovn-control-plane
        type: geneve
            ip: 172.18.0.4
        port ts2-az0
            transit switch: ts2
            address: ["00:00:00:EA:32:BA 169.254.102.103/24"]
availability-zone az1
    gateway 034da7cb-3826-4318-81ce-6a877a9bf285
        hostname: kube-ovn1-worker
        type: geneve
            ip: 172.18.0.6
        port ts-az1
            transit switch: ts
            address: ["00:00:00:25:3A:B9 169.254.100.51/24"]
    gateway 2531a683-283e-4fb8-a619-bdbcb33539b8
        hostname: kube-ovn1-worker2
        type: geneve
            ip: 172.18.0.5
        port ts1-az1
            transit switch: ts1
            address: ["00:00:00:52:87:F4 169.254.101.118/24"]
    gateway b0efb0be-e5a7-4323-ad4b-317637a757c4
        hostname: kube-ovn1-control-plane
        type: geneve
            ip: 172.18.0.8
        port ts2-az1
            transit switch: ts2
            address: ["00:00:00:F6:93:1A 169.254.102.17/24"]
```

### Single node deployment solution 2

Deploy the `OVN-IC` DB on a machine accessible by `kube-ovn-controller`, This DB will hold the network configuration information synchronized up from each cluster.

An environment deploying `docker` can start the `OVN-IC` DB with the following command.

```bash
docker run --name=ovn-ic-db -d --env "ENABLE_OVN_LEADER_CHECK="false"" --network=host --privileged  -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

For deploying a `containerd` environment instead of `docker` you can use the following command:

```bash
ctr -n k8s.io run -d --env "ENABLE_OVN_LEADER_CHECK="false"" --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
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

Check if the interconnected logical switch `ts` has been established in the `ovn-ic` container with the following command:

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

### High availability deployment solution 1

Solution 1 is recommended first, supported after Kube-OVN v1.11.16.

The method is the same as [Single node deployment solution 1](#single-node-deployment-solution-1)

### High availability deployment solution 2

A highly available cluster can be formed between `OVN-IC` DB via the Raft protocol, which requires a minimum of 3 nodes for this deployment model.

First start the leader of the `OVN-IC` DB on the first node.

Users deploying a `docker` environment can use the following command:

```bash
docker run --name=ovn-ic-db -d --env "ENABLE_OVN_LEADER_CHECK="false"" --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn -e LOCAL_IP="192.168.65.3"  -e NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"   kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

If you are  using `containerd` you can use the following command:

```bash
ctr -n k8s.io run -d --env "ENABLE_OVN_LEADER_CHECK="false"" --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw"  --env="NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"" --env="LOCAL_IP="192.168.65.3"" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

- `LOCAL_IP`: The IP address of the node where the current container is located.
- `NODE_IPS`: The IP addresses of the three nodes running the `OVN-IC` database, separated by commas.

Next, deploy the follower of the `OVN-IC` DB on the other two nodes.

`docker` environment can use the following command.

```bash
docker run --name=ovn-ic-db -d --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn -e LOCAL_IP="192.168.65.2"  -e NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1" -e LEADER_IP="192.168.65.3"  kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

If using `containerd` you can use the following command:

```bash
ctr -n k8s.io run -d --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw"  --env="NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"" --env="LOCAL_IP="192.168.65.2"" --env="LEADER_IP="192.168.65.3"" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

- `LOCAL_IP`: The IP address of the node where the current container is located.
- `NODE_IPS`: The IP addresses of the three nodes running the `OVN-IC` database, separated by commas.
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

## Support cluster interconnection ECMP

The premise controller is deployed according to [Single Node Deployment Solution 1](#single-node-deployment-solution-1)

This solution supports cluster interconnection ECMP by default. The default ECMP path is 3. It also supports modifying the number of ECMP paths. Use the command:

```bash
kubectl edit deployment ovn-ic-server -n kube-system
```

Just modify the value of the environment variable 'TS_NUM'. `TS_NUM` represents the number of ECMP Paths accessed between the two clusters.

## Manual Reset

In some cases, the entire interconnection configuration needs to be cleaned up due to configuration errors,
you can refer to the following steps to clean up your environment.

Delete the current `ovn-ic-config` Configmap:

```bash
kubectl -n kube-system delete cm ovn-ic-config
```

Delete `ts` logical switch:

```bash
kubectl ko nbctl ls-del ts
```

Repeat the same steps at the peer cluster.

## Clean OVN-IC

Delete the `ovn-ic-config` Configmap for all clusters:

```bash
kubectl -n kube-system delete cm ovn-ic-config
```

Delete all clusters' `ts` logical switches:

```bash
kubectl ko nbctl ls-del ts
```

Delete the cluster interconnect controller. If it is a high-availability OVN-IC database deployment, all need to be cleaned up.

If the controller is `docker` deploy execute command:

```bash
docker stop ovn-ic-db 
docker rm ovn-ic-db
```

If the controller is `containerd` deploy the command:

```bash
ctr -n k8s.io task kill ovn-ic-db
ctr -n k8s.io containers rm ovn-ic-db
```

If the controller is deployed using deployment `ovn-ic-server`:

```bash
kubectl delete deployment ovn-ic-server -n kube-system
```

Then clean up the interconnection-related DB on each master node. The command is as follows:

```bash
rm -f /etc/origin/ovn/ovn_ic_nb_db.db
rm -f /etc/origin/ovn/ovn_ic_sb_db.db
```
