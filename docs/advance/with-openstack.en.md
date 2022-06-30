# Integration with OpenStack

在一些情况下，用户需要使用 OpenStack 运行虚拟机，使用 Kubernetes 运行容器，并需要容器和虚机之间网络互通并处于统一控制平面下。如果 OpenStack 
Neutron 侧同样使用 OVN 作为底层网络控制，那么 Kube-OVN 可以使用集群互联和共享底层 OVN 两种方式打通 OpenStack 和 Kubernetes 的网络。

## 集群互联

该模式和[使用 OVN-IC 进行多集群互联](./with-ovn-ic.md)打通两个 Kubernetes 集群网络方式类似，只不过将集群两端换成 OpenStack 和 Kubernetes,
底层通用利用 OVN-IC 的能力进行互联。

### 前提条件

1. 自动互联模式下 OpenStack 和 Kubernetes 内的子网 CIDR 不能相互重叠。若存在重叠需参考后续手动互联过程，只能将不重叠网段打通。
2. 需要存在一组机器可以被每个集群通过网络访问，用来部署跨集群互联的控制器。
3. 每个集群需要有一组可以通过 IP 进行跨集群互访的机器作为之后的网关节点。
4. 该方案只打通 Kubernetes 默认子网和 OpenStack 的选定 VPC。

###  部署 OVN-IC 数据库

使用下面的命令启动 `OVN-IC` 数据库：

```bash
docker run --name=ovn-ic-db -d --network=host -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn kubeovn/kube-ovn:v1.10.2 bash start-ic-db.sh
```

### Kubernetes 侧操作

在 `kube-system` Namespace 下创建 `ovn-ic-config` ConfigMap：

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

- `enable-ic`: 是否开启集群互联。
- `az-name`: 区分不同集群的集群名称，每个互联集群需不同。
- `ic-db-host`: 部署 `OVN-IC` 数据库的节点地址。
- `ic-nb-port`: `OVN-IC` 北向数据库，默认为 6645。
- `ic-sb-port`: `OVN-IC` 南向数据库，默认为 6646。
- `gw-nodes`: 集群互联中承担网关工作的节点名，逗号分隔。
- `auto-route`: 是否自动对外发布和学习路由。

### OpenStack 侧操作

创建和 Kubernetes 互联的逻辑路由器：

```bash
# openstack router create router0
# openstack router list
+--------------------------------------+---------+--------+-------+----------------------------------+
| ID                                   | Name    | Status | State | Project                          |
+--------------------------------------+---------+--------+-------+----------------------------------+
| d5b38655-249a-4192-8046-71aa4d2b4af1 | router0 | ACTIVE | UP    | 98a29ab7388347e7b5ff8bdd181ba4f9 |
+--------------------------------------+---------+--------+-------+----------------------------------+
```

在 OpenStack 内的 OVN 北向数据库中设置可用区名字，该名称需和其他互联集群不同：

```bash
ovn-nbctl set NB_Global . name=op-az
```

在可访问 `OVN-IC` 数据库的节点启动 `OVN-IC` 控制器：

```bash
/usr/share/ovn/scripts/ovn-ctl --ovn-ic-nb-db=tcp:192.168.65.3:6645 \
  --ovn-ic-sb-db=tcp:192.168.65.3:6646 \
  --ovn-northd-nb-db=unix:/run/ovn/ovnnb_db.sock \
  --ovn-northd-sb-db=unix:/run/ovn/ovnsb_db.sock \
  start_ic
```
- `ovn-ic-nb-db`，`ovn-ic-sb-db`: OVN-IC 数据库北向数据库和南向数据库地址。
- `ovn-northd-nb-db`， `ovn-northd-sb-db`: 当前集群 OVN 北向数据库和南向数据地址。

配置互联网关节点：

```bash
ovs-vsctl set open_vswitch . external_ids:ovn-is-interconn=true
```

接下来需要在 OpenStack 的 OVN 内进行操作创建逻辑拓扑。

连接 `ts` 互联交换机和 `router0` 逻辑路由器，并设置相关规则：

```bash
ovn-nbctl lrp-add router0 lrp-router0-ts 00:02:ef:11:39:4f 169.254.100.73/24
ovn-nbctl lsp-add ts lsp-ts-router0 -- lsp-set-addresses lsp-ts-router0 router \
  -- lsp-set-type lsp-ts-router0 router \
  -- lsp-set-options lsp-ts-router0  router-port=lrp-router0-ts
ovn-nbctl lrp-set-gateway-chassis lrp-router0-ts {gateway chassis} 1000
ovn-nbctl set NB_Global . options:ic-route-adv=true options:ic-route-learn=true
```

验证已学习到 Kubernetes 路由规则：

```bash
# ovn-nbctl lr-route-list router0
IPv4 Routes
                10.0.0.22            169.254.100.34 dst-ip (learned)
             10.16.0.0/16            169.254.100.34 dst-ip (learned)
```

接下来可以在 `router0` 网络下创建虚机验证是否可以和 Kubernetes 下 Pod 互通。



## 共享底层 OVN

在该方案下，OpenStack 和 Kubernetes 共享使用同一个 OVN，因此可以将两者的 VPC 和 Subnet 等概念拉齐，实现更好的控制和互联。

在该模式下我们正常使用 Kube-OVN 部署 OVN，OpenStack 修改 Neutron 配置实现连接同一个 OVN 数据库。OpenStack 需使用 networking-ovn 作为 
Neutron 后端实现。

### Neutron 配置修改

修改 Neutron 配置文件 `/etc/neutron/plugins/ml2/ml2_conf.ini`：

```bash
[ovn]
...
ovn_nb_connection = tcp:[192.168.137.176]:6641,tcp:[192.168.137.177]:6641,tcp:[192.168.137.178]:6641
ovn_sb_connection = tcp:[192.168.137.176]:6642,tcp:[192.168.137.177]:6642,tcp:[192.168.137.178]:6642
ovn_l3_scheduler = OVN_L3_SCHEDULER
```

- `ovn_nb_connection`， `ovn_sb_connection`: 地址需修改为 Kube-OVN 部署 `ovn-central` 节点的地址。

修改每个节点的 OVS 配置：

```bash
ovs-vsctl set open . external-ids:ovn-remote=tcp:[192.168.137.176]:6642,tcp:[192.168.137.177]:6642,tcp:[192.168.137.178]:6642
ovs-vsctl set open . external-ids:ovn-encap-type=geneve
ovs-vsctl set open . external-ids:ovn-encap-ip=192.168.137.200
```

- `external-ids:ovn-remote`: 地址需修改为 Kube-OVN 部署 `ovn-central` 节点的地址。
- `ovn-encap-ip`: 修改为当前节点的 IP 地址。

### 在 Kubernetes 中使用 OpenStack 内资源

接下来介绍如何在 Kubernetes 中查询 OpenStack 的网络资源并在 OpenStack 的子网中创建 Pod。

查询 OpenStack 中已有的网络资源，如下资源已经预先创建完成：

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

在 Kubernetes 侧，查询 VPC 资源：
```bash
# kubectl get vpc
NAME                                           STANDBY   SUBNETS
neutron-22040ed5-0598-4f77-bffd-e7fd4db47e93   true      ["neutron-cd59e36a-37db-4c27-b709-d35379a7920f"]
ovn-cluster                                    true      ["join","ovn-default"]
```

`neutron-22040ed5-0598-4f77-bffd-e7fd4db47e93` 为从 OpenStack 同步过来的 VPC 资源。

接下来可以按照 Kube-OVN 原生的 VPC 和 Subnet 操作创建 Pod 并运行。

VPC, Subnet 绑定 Namespace `net2`，并创建 Pod:

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
    - image: kubeovn/kube-ovn:v1.8.0
      command:
        - "sleep"
        - "604800"
      imagePullPolicy: IfNotPresent
      name: ubuntu
  restartPolicy: Always
```
