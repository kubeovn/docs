# Integration with OpenStack

In some cases, users need to run virtual machines with OpenStack and containers with Kubernetes,
and need the network to interoperate between containers and virtual machines and be under a unified control plane.
If the OpenStack Neutron side also uses OVN as the underlying network, then Kube-OVN can use either cluster interconnection
or shared underlying OVN to connect the OpenStack and Kubernetes networks.

## Cluster Interconnection

This pattern is similar to [Cluster Inter-Connection with OVN-IC](./with-ovn-ic.md) to connect two Kubernetes cluster networks,
except that the two ends of the cluster are replaced with OpenStack and Kubernetes.

### Prerequisites

1. The subnet CIDRs within OpenStack and Kubernetes cannot overlap with each other in auto-route mode.
2. A set of machines needs to exist that can be accessed by each cluster over the network and used to deploy controllers that interconnect across clusters.
3. Each cluster needs to have a set of machines that can access each other across clusters via IP as the gateway nodes.
4. This solution only connects to the Kubernetes default subnet with selected VPC in OpenStack.

### Deploy OVN-IC DB

Start the `OVN-IC` DB with the following command:

```bash
docker run --name=ovn-ic-db -d --network=host -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

### Kubernetes Side Operations

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

### OpenStack Side Operations

Create logical routers that interconnect with Kubernetes:

```bash
# openstack router create router0
# openstack router list
+--------------------------------------+---------+--------+-------+----------------------------------+
| ID                                   | Name    | Status | State | Project                          |
+--------------------------------------+---------+--------+-------+----------------------------------+
| d5b38655-249a-4192-8046-71aa4d2b4af1 | router0 | ACTIVE | UP    | 98a29ab7388347e7b5ff8bdd181ba4f9 |
+--------------------------------------+---------+--------+-------+----------------------------------+
```

Set the availability zone name in the OVN northbound database within OpenStack, which needs to be different from the other interconnected clusters:

```bash
ovn-nbctl set NB_Global . name=op-az
```

Start the `OVN-IC` controller at a node that has access to the `OVN-IC` DB:

```bash
/usr/share/ovn/scripts/ovn-ctl --ovn-ic-nb-db=tcp:192.168.65.3:6645 \
  --ovn-ic-sb-db=tcp:192.168.65.3:6646 \
  --ovn-northd-nb-db=unix:/run/ovn/ovnnb_db.sock \
  --ovn-northd-sb-db=unix:/run/ovn/ovnsb_db.sock \
  start_ic
```

- `ovn-ic-nb-db`, `ovn-ic-sb-db`: OVN-IC Northbound database and southbound database addresses.
- `ovn-northd-nb-db`, `ovn-northd-sb-db`: Current cluster OVN northbound database and southbound data address.

Configuration gateway nodes:

```bash
ovs-vsctl set open_vswitch . external_ids:ovn-is-interconn=true
```

The next step is to create a logical topology by operating the OVN in OpenStack.

Connect the `ts` interconnect switch and the `router0` logical router, and set the relevant rules:

```bash
ovn-nbctl lrp-add router0 lrp-router0-ts 00:02:ef:11:39:4f 169.254.100.73/24
ovn-nbctl lsp-add ts lsp-ts-router0 -- lsp-set-addresses lsp-ts-router0 router \
  -- lsp-set-type lsp-ts-router0 router \
  -- lsp-set-options lsp-ts-router0  router-port=lrp-router0-ts
ovn-nbctl lrp-set-gateway-chassis lrp-router0-ts {gateway chassis} 1000
ovn-nbctl set NB_Global . options:ic-route-adv=true options:ic-route-learn=true
```

Verify that OpenStack has learned the Kubernetes routing rules:

```bash
# ovn-nbctl lr-route-list router0
IPv4 Routes
                10.0.0.22            169.254.100.34 dst-ip (learned)
             10.16.0.0/16            169.254.100.34 dst-ip (learned)
```

Next, you can create a virtual machine under the `router0` network to verify that it can interconnect with Pods under Kubernetes.

## Shared Underlay OVN

In this scenario, OpenStack and Kubernetes share the same OVN, so concepts such as VPC and Subnet can be pulled together for better control and interconnection.

In this mode we deploy the OVN normally using Kube-OVN, and OpenStack modifies the Neutron configuration to connect to the same OVN DB.
OpenStack requires networking-ovn as a Neutron backend implementation.

### Neutron Modification

Modify the Neutron configuration file `/etc/neutron/plugins/ml2/ml2_conf.ini`:

```bash
[ovn]
...
ovn_nb_connection = tcp:[192.168.137.176]:6641,tcp:[192.168.137.177]:6641,tcp:[192.168.137.178]:6641
ovn_sb_connection = tcp:[192.168.137.176]:6642,tcp:[192.168.137.177]:6642,tcp:[192.168.137.178]:6642
ovn_l3_scheduler = OVN_L3_SCHEDULER
```

- `ovn_nb_connection`, `ovn_sb_connection`: The address needs to be changed to the address of the `ovn-central` nodes deployed by Kube-OVN.

Modify the OVS configuration for each node:

```bash
ovs-vsctl set open . external-ids:ovn-remote=tcp:[192.168.137.176]:6642,tcp:[192.168.137.177]:6642,tcp:[192.168.137.178]:6642
ovs-vsctl set open . external-ids:ovn-encap-type=geneve
ovs-vsctl set open . external-ids:ovn-encap-ip=192.168.137.200
```

- `external-ids:ovn-remote`: The address needs to be changed to the address of the `ovn-central` nodes deployed by Kube-OVN.
- `ovn-encap-ip`: Change to the IP address of the current node.

### Using OpenStack Internal Resources in Kubernetes

The next section describes how to query OpenStack's network resources in Kubernetes and create Pods in the subnet from OpenStack.

!!! note

    To use this feature, you need to enable resource synchronization in the `kube-ovn-controller` args by setting `--enable-external-vpc=true`.

Query the existing network resources in OpenStack for the following resources that have been pre-created.

```bash
# openstack router list
+--------------------------------------+---------+--------+-------+----------------------------------+
| ID                                   | Name    | Status | State | Project                          |
+--------------------------------------+---------+--------+-------+----------------------------------+
| 22040ed5-0598-4f77-bffd-e7fd4db47e93 | router0 | ACTIVE | UP    | 62381a21d569404aa236a5dd8712449c |
+--------------------------------------+---------+--------+-------+----------------------------------+
# openstack network list
+--------------------------------------+----------+--------------------------------------+
| ID                                   | Name     | Subnets                              |
+--------------------------------------+----------+--------------------------------------+
| cd59e36a-37db-4c27-b709-d35379a7920f | provider | 01d73d9f-fdaa-426c-9b60-aa34abbfacae |
+--------------------------------------+----------+--------------------------------------+
# openstack subnet list
+--------------------------------------+-------------+--------------------------------------+----------------+
| ID                                   | Name        | Network                              | Subnet         |
+--------------------------------------+-------------+--------------------------------------+----------------+
| 01d73d9f-fdaa-426c-9b60-aa34abbfacae | provider-v4 | cd59e36a-37db-4c27-b709-d35379a7920f | 192.168.1.0/24 |
+--------------------------------------+-------------+--------------------------------------+----------------+
# openstack server list
+--------------------------------------+-------------------+--------+-----------------------+--------+--------+
| ID                                   | Name              | Status | Networks              | Image  | Flavor |
+--------------------------------------+-------------------+--------+-----------------------+--------+--------+
| 8433d622-a8d6-41a7-8b31-49abfd64f639 | provider-instance | ACTIVE | provider=192.168.1.61 | ubuntu | m1     |
+--------------------------------------+-------------------+--------+-----------------------+--------+--------+
```

On the Kubernetes side, query the VPC resources from OpenStack:

```bash
# kubectl get vpc
NAME                                           STANDBY   SUBNETS
neutron-22040ed5-0598-4f77-bffd-e7fd4db47e93   true      ["neutron-cd59e36a-37db-4c27-b709-d35379a7920f"]
ovn-cluster                                    true      ["join","ovn-default"]
```

`neutron-22040ed5-0598-4f77-bffd-e7fd4db47e93` is the VPC resources synchronized from OpenStack.

Next, you can create Pods and run them according to Kube-OVN's native VPC and Subnet operations.

Bind VPC, Subnet to Namespace `net2` and create Pod:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: net2
---
apiVersion: kubeovn.io/v1
kind: Vpc
metadata:
  creationTimestamp: "2021-06-20T13:34:11Z"
  generation: 2
  labels:
    ovn.kubernetes.io/vpc_external: "true"
  name: neutron-22040ed5-0598-4f77-bffd-e7fd4db47e93
  resourceVersion: "583728"
  uid: 18d4c654-f511-4def-a3a0-a6434d237c1e
spec:
  namespaces:
  - net2
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net2
spec:
  vpc: neutron-22040ed5-0598-4f77-bffd-e7fd4db47e93
  namespaces:
    - net2
  cidrBlock: 12.0.1.0/24
  natOutgoing: false
---
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu
  namespace: net2
spec:
  containers:
    - image: docker.io/kubeovn/kube-ovn:v1.8.0
      command:
        - "sleep"
        - "604800"
      imagePullPolicy: IfNotPresent
      name: ubuntu
  restartPolicy: Always
```
