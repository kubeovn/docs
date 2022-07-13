# OVN 数据库备份和恢复

本文档介绍如何进行数据库备份，以及在不同情况下如何通过已有的数据库文件进行集群恢复。

## 数据库备份

利用 kubectl 插件的 backup 命令可以对数据库文件进行备份，以用于故障时恢复：

```bash
# kubectl ko nb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnnb_db.060223191654183154.backup

# kubectl ko sb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnsb_db.060223191654183154.backup
```

## 集群部分故障恢复

若集群中存在部分节点因为断电，文件系统故障或磁盘空间不足导致工作异常，
但是集群仍可正常工作可以通过如下步骤进行恢复。

### 查看日志确认状态异常

查看对应节点 `/var/log/ovn/ovn-northd.log`，若提示类似错误则可判断数据库存在异常

```bash
 * ovn-northd is not running
ovsdb-server: ovsdb error: error reading record 2739 from OVN_Northbound log: record 2739 advances commit index to 6308 but last log index is 6307
 * Starting ovsdb-nb
```

### 从集群中踢出对应节点

根据日志提示是 `OVN_Northbound` 还是 `OVN_Southbound` 选择对应的数据库进行操作。
上述日志提示为 `OVN_Northbound` 则对 ovn-nb 进行操作：

```bash
# kubectl ko nb status
9182
Name: OVN_Northbound
Cluster ID: e75f (e75fa340-49ed-45ab-990e-26cb865ebc85)
Server ID: 9182 (9182e8dd-b5b0-4dd8-8518-598cc1e374f3)
Address: tcp:[10.0.128.61]:6643
Status: cluster member
Role: leader
Term: 1454
Leader: self
Vote: self

Last Election started 1732603 ms ago, reason: timeout
Last Election won: 1732587 ms ago
Election timer: 1000
Log: [7332, 12512]
Entries not yet committed: 1
Entries not yet applied: 1
Connections: ->f080 <-f080 <-e631 ->e631
Disconnections: 1
Servers:
    f080 (f080 at tcp:[10.0.129.139]:6643) next_index=12512 match_index=12510 last msg 63 ms ago
    9182 (9182 at tcp:[10.0.128.61]:6643) (self) next_index=10394 match_index=12510
    e631 (e631 at tcp:[10.0.131.173]:6643) next_index=12512 match_index=0
```

从集群中踢出状态异常节点：

```bash
kubectl ko nb kick e631
```

登录异常节点，删除对应的数据库文件：

```bash
mv /etc/origin/ovn/ovnnb_db.db /tmp
```

删除对应节点的 `ovn-central` Pod，等待集群自动恢复：

```bash
kubectl delete pod -n kube-system ovn-central-xxxx
```

## 集群不能正常工作下的恢复

若集群多数节点受损无法选举出 leader，请参照下面的步骤进行恢复。

### 停止 ovn-central

记录当前 `ovn-central` 副本数量，并停止 `ovn-central` 避免新的数据库变更影响恢复：

```bash
kubectl scale deployment -n kube-system ovn-central --replicas=0
```

### 选择备份

由于多数节点受损，需要从某个数据库文件进行恢复重建集群。如果之前备份过数据库
可使用之前的备份文件进行恢复。如果没有进行过备份可以使用下面的步骤从已有的数据库文件
中生成一个备份。

> 由于默认文件夹下的数据库文件为集群格式数据库文件，包含当前集群的信息，无法直接
> 用该文件重建数据库，需要使用 `ovsdb-tool cluster-to-standalone` 进行格式转换。

选择 `ovn-central` 环境变量 `NODE_IPS` 中排第一的节点恢复数据库文件，
如果第一个节点数据库文件已损坏，从其他机器 `/etc/origin/ovn` 下复制文件到第一台机器 ，
执行下列命令生成数据库文件备份。

```bash
docker run -it -v /etc/origin/ovn:/etc/ovn kubeovn/kube-ovn:{{ variables.version }} bash
cd /etc/ovn/
ovsdb-tool cluster-to-standalone ovnnb_db_standalone.db ovnnb_db.db
ovsdb-tool cluster-to-standalone ovnsb_db_standalone.db ovnsb_db.db
```

### 删除每个 ovn-central 节点上的数据库文件

为了避免重建集群时使用到错误的数据，需要对已有数据库文件进行清理：

```bash
mv /etc/origin/ovn/ovnnb_db.db /tmp
mv /etc/origin/ovn/ovnsb_db.db /tmp
```

### 恢复数据库集群

将备份数据库分别重命名为 `ovnnb_db.db` 和 `ovnsb_db.db`，并复制到 `ovn-central`
 环境变量 `NODE_IPS` 中排第一机器的 `/etc/origin/ovn/` 目录下：

```bash
mv /etc/origin/ovn/ovnnb_db_standalone.db /etc/origin/ovn/ovnnb_db.db
mv /etc/origin/ovn/ovnsb_db_standalone.db /etc/origin/ovn/ovnsb_db.db
```

恢复 `ovn-central` 的副本数：

```bash
kubectl scale deployment -n kube-system ovn-central --replicas=3
kubectl rollout status deployment/ovn-central -n kube-system
```
