# OVN 数据库备份和恢复

## OVN 数据库启动校验与单成员恢复

在 Raft 模式的 `ovn-central` 和 OVN-IC 数据库启动时，系统会先校验数据库身份、存储格式和集群日志。无法验证时会保留原数据库文件和 Raft header，并以非零状态退出。

| 数据库状态 | 启动行为 |
| --- | --- |
| 有效的集群数据库 | 正常启动，由 Raft 同步成员。 |
| 有效的 standalone 数据库 | 保留原有 standalone 启动流程。 |
| 数据库不存在 | 保留原有初始化和 header 恢复流程。 |
| 等待加入集群 | 继续加入流程；central 数据库保留原有过期 pending-join 清理。 |
| 身份未知、数据库名错误、存储格式未知或集群日志无效 | 保留原文件和 header；只有在 header 匹配可访问 quorum 时，才从 header 创建干净成员，否则阻塞并等待后续重试。 |

不要在已有无效成员上直接执行 `ovsdb-tool fix-cluster` 后再执行 `join-cluster`。本地修复可能丢弃已提交但本地缺失的日志。系统会要求有效且匹配的 Raft header，查询可访问的多数派，然后使用原 server ID 和 peer 地址创建 `rejoin-cluster` 数据库；新文件创建成功后才会把原数据库移动为带时间戳的备份。新成员启动后由健康多数派通过 Raft 日志或 snapshot 重新填充。

磁盘仍满、header 无效、quorum 不可访问或替换失败时，进程会以非零状态退出，原文件保持不变，成员保持不可用以便后续重试。集群数据库的 readiness/liveness 检查也会执行 `ovsdb-tool check-cluster`，因此语义持久化缺口会使成员退出服务并由 kubelet 重启；进程或 Pod 显示 Ready 不能单独证明数据库历史安全。

自动恢复一次只处理一个损坏成员，不能自动修复多个分叉成员。显式恢复前，请保存每个成员的数据库、header、备份和日志，比较 cluster/server identity、snapshot/log history、term、commit entry 和应用数据，并在历史冲突时先完成明确的人工取舍。文件大小和 commit index 单独不能证明哪份数据是权威副本。

该启动保护不会修复已经分叉的历史，也不会修复底层 I/O 故障；它只把可验证的单成员恢复限制在能够从一致多数派同步的路径上。详见 [Issue #7870](https://github.com/kubeovn/kube-ovn/issues/7870)。

本文档介绍如何进行数据库备份，以及在不同情况下如何通过已有的数据库文件进行集群恢复。

## 数据库备份

利用 kubectl 插件的 backup 命令可以对数据库文件进行备份，以用于故障时恢复：

```bash
# kubectl ko nb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnnb_db.060223191654183154.backup

# kubectl ko sb backup
tar: Removing leading `/' from member names
backup ovn-sb db to /root/ovnsb_db.060223191654183154.backup
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

### 无效 Raft 成员的启动检查和恢复

对于 OVN central 的 NB/SB 数据库，以及 OVN-IC 的 NB/SB 数据库，启动时会先检查持久化数据库。可以在对应的节点或 OVN 容器中执行 `ovsdb-tool check-cluster` 查看检查结果：

```bash
ovsdb-tool check-cluster /etc/origin/ovn/ovnnb_db.db
ovsdb-tool check-cluster /etc/origin/ovn/ovnsb_db.db

# OVN-IC 数据库
ovsdb-tool check-cluster /etc/origin/ovn/ovn_ic_nb_db.db
ovsdb-tool check-cluster /etc/origin/ovn/ovn_ic_sb_db.db
```

如果检查发现持久化日志存在语义缺口，启动流程会将该成员判定为无效成员。数据库存活和就绪检查也会执行 `check-cluster`，因此该成员会从服务中移除并由 kubelet 重启；进程或 Pod 显示为运行中不能代替数据库检查结果。自动恢复一次只处理一个无效成员，不能在多个成员同时损坏时自动重建多数派。

恢复无效成员时，请先保留对应的数据库文件、Raft header（例如 `ovnnb_db.hdr`）和日志。Raft header 必须包含有效的 cluster ID 和 server ID，且 cluster ID 必须与可达多数派查询到的 live cluster ID 一致。无法读取有效 header、无法达到多数派、发现 peer 的 cluster ID 不一致，或磁盘仍然没有可用空间时，不会替换原文件，成员会保持不可用以便后续重试和人工处理。

启动流程不会直接在原数据库上执行修复。它会根据 Raft header 和 peer 地址在临时文件中执行 `ovsdb-tool rejoin-cluster`，使用原 server ID 创建干净成员；只有临时文件成功生成且非空后，才会将原数据库移动为带时间戳的 `.backup-*` 文件，并把临时文件移到原路径。随后由健康多数派通过正常的 Raft 日志或快照同步补齐该成员。数据库文件缺失但仍保留可用 header 时，流程也会先生成临时 `join-cluster` 文件，再安装到原路径。任何本地检查或诊断都应针对副本执行，不能覆盖原数据库。

如果创建临时文件、保存原文件或安装新文件失败，启动会以非零状态退出并保持成员不可用；失败的恢复文件和原文件会按情况保留，供诊断使用。恢复前应同时核对 cluster/server identity、Raft header、任期、已提交条目、快照和应用数据，不能仅凭文件大小或 commit index 选择权威副本。

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

如果节点上仍可以使用 `docker`：

```bash
docker run -it -v /etc/origin/ovn:/etc/ovn kubeovn/kube-ovn:{{ variables.version }} bash
cd /etc/ovn/
ovsdb-tool cluster-to-standalone ovnnb_db_standalone.db ovnnb_db.db
ovsdb-tool cluster-to-standalone ovnsb_db_standalone.db ovnsb_db.db
```

若节点使用 containerd（无 docker），可以借助 `ctr` 直接拉取并运行：

```bash
ctr -n k8s.io image pull docker.io/kubeovn/kube-ovn:{{ variables.version }}
ctr -n k8s.io run --rm -t \
  --mount type=bind,src=/etc/origin/ovn,dst=/etc/ovn,options=rbind:rw \
  docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-recover bash
cd /etc/ovn/
ovsdb-tool cluster-to-standalone ovnnb_db_standalone.db ovnnb_db.db
ovsdb-tool cluster-to-standalone ovnsb_db_standalone.db ovnsb_db.db
exit
```

或直接在 `ovn-central` Pod 内执行 `ovsdb-tool cluster-to-standalone`，再 `kubectl cp` 拷出备份文件。

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
