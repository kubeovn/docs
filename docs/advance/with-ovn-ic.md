# 使用 OVN-IC 进行多集群互联

Kube-OVN 支持通过 [OVN-IC](https://docs.ovn.org/en/latest/tutorials/ovn-interconnection.html)
将两个 Kubernetes 集群 Pod 网络打通，打通后的两个集群内的 Pod 可以通过 Pod IP 进行直接通信。
Kube-OVN 使用隧道对跨集群流量进行封装，两个集群之间只要存在一组 IP 可达的机器即可完成容器网络的互通。

> 该模式的多集群互联为 Overlay 网络功能，Underlay 网络如果想要实现集群互联需要底层基础设施做网络打通。

![](../static/inter-connection.png)

## 前提条件

1. 1.11.16 之后版本部署的集群默认关闭了集群互联的开关，需要在部署脚本 `install.sh` 里修改下列变量：

    ```bash
    ENABLE_IC=true
    ```

    打开开关后部署集群，会出现组件 deployment ovn-ic-controller。

2. 自动互联模式下不同集群的子网 CIDR 不能相互重叠，默认子网需在安装时配置为不重叠的网段。若存在重叠需参考后续手动互联过程，只能将不重叠网段打通。
3. 需要存在一组机器可以被每个集群的 `kube-ovn-controller` 通过 IP 访问，用来部署跨集群互联的控制器。
4. 每个集群需要有一组可以通过 IP 进行跨集群互访的机器作为之后的网关节点。
5. 该功能只对默认 VPC 生效，用户自定义 VPC 无法使用互联功能。

## 部署单节点 OVN-IC 数据库

### 单节点部署方案 1

优先推荐方案 1，Kube-OVN v1.11.16 之后支持。

该方法不区别 "单节点" 或者 "多节点高可用" 部署，控制器会以 Deployment 的形式部署在 master 节点上，集群 master 节点为 1，即单节点部署，master 节点为多个，即多节点高可用部署。

先获取脚本 `install-ovn-ic.sh`，使用下面命令：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install-ic-server.sh
```

执行命令安装，其中 `TS_NUM` 表示集群互联的 ECMP Path 数量：

```bash
sed 's/VERSION=.*/VERSION={{ variables.version }}/' dist/images/install-ic-server.sh | TS_NUM=3 bash
```

执行成功输出如下：

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

通过 `kubectl ko icsbctl show` 命令可以查看当前互联控制器的状态，命令如下：

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

### 单节点部署方案 2

在每个集群 `kube-ovn-controller` 可通过 IP 访问的机器上部署 `OVN-IC` 数据库，该节点将保存各个集群同步上来的网络配置信息。

部署 `docker` 的环境可以使用下面的命令启动 `OVN-IC` 数据库：

```bash
docker run --name=ovn-ic-db -d --env "ENABLE_OVN_LEADER_CHECK="false"" --network=host --privileged  -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

对于部署 `containerd` 取代 `docker` 的环境可以使用下面的命令：

```bash
ctr -n k8s.io run -d --env "ENABLE_OVN_LEADER_CHECK="false"" --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

## 自动路由设置

在自动路由设置下，每个集群会将自己默认 VPC 下 Subnet 的 CIDR 信息同步给 `OVN-IC`，因此要确保两个集群的 Subnet CIDR 不存在重叠。

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
- `ic-nb-port`: `OVN-IC` 北向数据库端口，默认为 6645。
- `ic-sb-port`: `OVN-IC` 南向数据库端口，默认为 6646。
- `gw-nodes`: 集群互联中承担网关工作的节点名，逗号分隔。
- `auto-route`: 是否自动对外发布和学习路由。

**注意：** 为了保证操作的正确性，`ovn-ic-config` 这个 ConfigMap 不允许修改。如有参数需要变更，请删除该 ConfigMap，修改后再应用此 ConfigMap。

在 `ovn-ic` 容器内通过下面的命令查看是否已建立互联逻辑交换机 `ts`：

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

在每个集群观察逻辑路由是否有学习到的对端路由：

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

接下来可以尝试在集群 1 内的一个 Pod 内直接 `ping` 集群 2 内的一个 Pod IP 观察是否可以联通。

对于某个不想对外自动发布路由的子网可以通过修改 Subnet 里的 `disableInterConnection` 来禁止路由广播：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: no-advertise
spec:
  cidrBlock: 10.199.0.0/16
  disableInterConnection: true
```

## 手动路由设置

对于集群间存在重叠 CIDR 只希望做部分子网打通的情况，可以通过下面的步骤手动发布子网路由。

在 `kube-system` Namespace 下创建 `ovn-ic-config` ConfigMap，并将 `auto-route` 设置为 `false`：

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

在每个集群分别查看远端逻辑端口的地址，用于之后手动配置路由：

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

由上输出可知，集群 `az1` 到 集群 `az2` 的远端地址为 `169.254.100.31`，`az2` 到 `az1` 的远端地址为 `169.254.100.79`。

下面手动设置路由，在该例子中，集群 `az1` 内的子网 CIDR 为 `10.16.0.0/24`，集群 `az2` 内的子网 CIDR 为 `10.17.0.0/24`。

在集群 `az1` 设置到集群 `az2` 的路由:

```bash
kubectl ko nbctl lr-route-add ovn-cluster 10.17.0.0/24 169.254.100.31
```

在集群 `az2` 设置到集群 `az1` 的路由:

```bash
kubectl ko nbctl lr-route-add ovn-cluster 10.16.0.0/24 169.254.100.79
```

## 高可用 OVN-IC 数据库部署

### 高可用部署方案 1

优先推荐方案 1，Kube-OVN v1.11.16 之后支持。

方法同[单节点部署方案 1](#单节点部署方案-1)

### 高可用部署方案 2

`OVN-IC` 数据库之间可以通过 Raft 协议组成一个高可用集群，该部署模式需要至少 3 个节点。

首先在第一个节点上启动 `OVN-IC` 数据库的 leader。

部署 `docker` 环境的用户可以使用下面的命令：

```bash
docker run --name=ovn-ic-db -d --env "ENABLE_OVN_LEADER_CHECK="false"" --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn -e LOCAL_IP="192.168.65.3"  -e NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"   kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

如果是部署 `containerd` 的用户可以使用下面的命令：

```bash
ctr -n k8s.io run -d --env "ENABLE_OVN_LEADER_CHECK="false"" --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw"  --env="NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"" --env="LOCAL_IP="192.168.65.3"" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

- `LOCAL_IP`： 当前容器所在节点 IP 地址。
- `NODE_IPS`： 运行 `OVN-IC` 数据库的三个节点 IP 地址，使用逗号进行分隔。

接下来，在另外两个节点部署 `OVN-IC` 数据库的 follower。

部署 `docker` 环境的用户可以使用下面的命令：

```bash
docker run --name=ovn-ic-db -d --network=host --privileged -v /etc/ovn/:/etc/ovn -v /var/run/ovn:/var/run/ovn -v /var/log/ovn:/var/log/ovn -e LOCAL_IP="192.168.65.2"  -e NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1" -e LEADER_IP="192.168.65.3"  kubeovn/kube-ovn:{{ variables.version }} bash start-ic-db.sh
```

如果是部署 `containerd` 的用户可以使用下面的命令：

```bash
ctr -n k8s.io run -d --net-host --privileged --mount="type=bind,src=/etc/ovn/,dst=/etc/ovn,options=rbind:rw" --mount="type=bind,src=/var/run/ovn,dst=/var/run/ovn,options=rbind:rw" --mount="type=bind,src=/var/log/ovn,dst=/var/log/ovn,options=rbind:rw"  --env="NODE_IPS="192.168.65.3,192.168.65.2,192.168.65.1"" --env="LOCAL_IP="192.168.65.2"" --env="LEADER_IP="192.168.65.3"" docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-ic-db bash start-ic-db.sh
```

- `LOCAL_IP`： 当前容器所在节点 IP 地址。
- `NODE_IPS`： 运行 `OVN-IC` 数据库的三个节点 IP 地址，使用逗号进行分隔。
- `LEADER_IP`: 运行 `OVN-IC` 数据库 leader 节点的 IP 地址。

在每个集群创建 `ovn-ic-config` 时指定多个 `OVN-IC` 数据库节点地址：

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

## 支持集群互联 ECMP

前提控制器是按照[单节点部署方案 1](#单节点部署方案-1)部署

该方案默认支持集群互联 ECMP，ECMP path 默认为 3，同时也支持修改 ECMP path 条数，使用命令:

```bash
kubectl edit deployment ovn-ic-server -n kube-system
```

修改环境变量 'TS_NUM' 数值即可，`TS_NUM` 表示两个集群之间访问的 ECMP Path 条数。

## 手动重置

在一些情况下，由于配置错误需要对整个互联配置进行清理，可以参考下面的步骤清理环境。

删除当前的 `ovn-ic-config` Configmap：

```bash
kubectl -n kube-system delete cm ovn-ic-config
```

删除 `ts` 逻辑交换机：

```bash
kubectl ko nbctl ls-del ts
```

在对端集群重复同样的步骤。

## 修改 az-name

可以直接通过 `kubectl edit` 的方式对 `ovn-ic-config` 这个 configmap 中的 `az-name` 字段进行修改。
但是需要在每个 ovn-cni pod 上执行以下命令，否则可能出现最长 10 分钟的跨集群网络中断。

```bash
ovn-appctl -t ovn-controller inc-engine/recompute
```

## 清理集群互联

删除所有集群的 `ovn-ic-config` Configmap：

```bash
kubectl -n kube-system delete cm ovn-ic-config
```

删除所有集群的 `ts` 逻辑交换机：

```bash
kubectl ko nbctl ls-del ts
```

删除集群互联控制器，如果是高可用 OVN-IC 数据库部署，需要都清理掉。

如果控制器是 `docker` 部署执行命令：

```bash
docker stop ovn-ic-db 
docker rm ovn-ic-db
```

如果控制器是 `containerd` 部署执行命令：

```bash
ctr -n k8s.io task kill ovn-ic-db
ctr -n k8s.io containers rm ovn-ic-db
```

如果控制器是使用 deployment `ovn-ic-server` 部署：

```bash
kubectl delete deployment ovn-ic-server -n kube-system
```

然后在每个 master 节点上清理互联相关的 DB，命令如下：

```bash
rm -f /etc/origin/ovn/ovn_ic_nb_db.db
rm -f /etc/origin/ovn/ovn_ic_sb_db.db
```
