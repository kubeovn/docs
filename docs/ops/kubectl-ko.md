# kubectl 插件使用

为了方便日常的运维操作，Kube-OVN 提供了 kubectl 插件工具，网络管理员
可以通过该命令进行日常操作，例如：查看 OVN 数据库信息和状态，OVN 数据库
备份和恢复，OVS 相关信息查看，tcpdump 特定容器，特定链路逻辑拓扑展示，
网络问题诊断和性能优化。

## 插件安装

Kube-OVN 安装时默认会部署插件到每个节点，若执行 kubectl 的机器不在集群内，
或需要重装插件，可参考下面的步骤：

下载 `kubectl-ko` 文件：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/release-1.10/dist/images/kubectl-ko
```

将该文件移动至 `$PATH` 目录下：

```bash
mv kubectl-ko /usr/local/bin/kubectl-ko
```

增加可执行权限：

```bash
chmod +x /usr/local/bin/kubectl-ko
```

检查插件是否可以正常使用：

```bash
# kubectl plugin list
The following compatible plugins are available:

/usr/local/bin/kubectl-ko
```

## 插件使用

运行 `kubectl ko` 会展示该插件所有可用的命令和用法描述，如下所示：

```bash
kubectl ko {subcommand} [option...]
Available Subcommands:
  [nb|sb] [status|kick|backup|dbstatus|restore]     ovn-db operations show cluster status, kick stale server, backup database, get db consistency status or restore ovn nb db when met 'inconsistent data' error
  nbctl [ovn-nbctl options ...]    invoke ovn-nbctl
  sbctl [ovn-sbctl options ...]    invoke ovn-sbctl
  vsctl {nodeName} [ovs-vsctl options ...]   invoke ovs-vsctl on the specified node
  ofctl {nodeName} [ovs-ofctl options ...]   invoke ovs-ofctl on the specified node
  dpctl {nodeName} [ovs-dpctl options ...]   invoke ovs-dpctl on the specified node
  appctl {nodeName} [ovs-appctl options ...]   invoke ovs-appctl on the specified node
  tcpdump {namespace/podname} [tcpdump options ...]     capture pod traffic
  trace {namespace/podname} {target ip address} {icmp|tcp|udp} [target tcp or udp port]    trace ovn microflow of specific packet
  diagnose {all|node} [nodename]    diagnose connectivity of all nodes or a specific node
  tuning {install-fastpath|local-install-fastpath|remove-fastpath|install-stt|local-install-stt|remove-stt} {centos7|centos8}} [kernel-devel-version]  deploy  kernel optimisation components to the system
  reload restart all kube-ovn components
```

下面将介绍每个命令的具体功能和使用。

### nb|sb

该子命令主要对 OVN 北向或南向数据库进行操作，包括数据库集群状态查看，数据库节点下线，
数据库备份，数据库存储状态查看和数据库恢复。

#### 数据库集群状态查看

该命令会在对应 OVN 数据库的 leader 节点执行 `ovs-appctl cluster/status` 展示集群状态

```bash
# kubectl ko nb status
306b
Name: OVN_Northbound
Cluster ID: 9a87 (9a872522-3e7d-47ca-83a3-d74333e1a7ca)
Server ID: 306b (306b256b-b5e1-4eb0-be91-4ca96adf6bad)
Address: tcp:[172.18.0.2]:6643
Status: cluster member
Role: leader
Term: 1
Leader: self
Vote: self

Last Election started 280309 ms ago, reason: timeout
Last Election won: 280309 ms ago
Election timer: 5000
Log: [139, 139]
Entries not yet committed: 0
Entries not yet applied: 0
Connections: <-8723 ->8723 <-85d6 ->85d6
Disconnections: 0
Servers:
    85d6 (85d6 at tcp:[172.18.0.4]:6643) next_index=139 match_index=138 last msg 763 ms ago
    8723 (8723 at tcp:[172.18.0.3]:6643) next_index=139 match_index=138 last msg 763 ms ago
    306b (306b at tcp:[172.18.0.2]:6643) (self) next_index=2 match_index=138
status: ok
```

若 `Server` 下的 `match_index` 出现较大差别，且 `last msg` 时间较长则对应 Server 可能长时间没有响应，
需要进一步查看。

#### 数据库节点下线

该命令会将某个节点从 OVN 数据库中移除，在节点下线或更换节点时需要用到,
以上个命令所查看到的集群状态为例，下线 `172.18.0.3` 节点

```bash
# kubectl ko nb kick 8723
started removal
```

再次查看数据库集群状态确认节点已移除

```bash
# kubectl ko nb status
306b
Name: OVN_Northbound
Cluster ID: 9a87 (9a872522-3e7d-47ca-83a3-d74333e1a7ca)
Server ID: 306b (306b256b-b5e1-4eb0-be91-4ca96adf6bad)
Address: tcp:[172.18.0.2]:6643
Status: cluster member
Role: leader
Term: 1
Leader: self
Vote: self

Last Election started 324356 ms ago, reason: timeout
Last Election won: 324356 ms ago
Election timer: 5000
Log: [140, 140]
Entries not yet committed: 0
Entries not yet applied: 0
Connections: <-85d6 ->85d6
Disconnections: 2
Servers:
    85d6 (85d6 at tcp:[172.18.0.4]:6643) next_index=140 match_index=139 last msg 848 ms ago
    306b (306b at tcp:[172.18.0.2]:6643) (self) next_index=2 match_index=139
status: ok
```

#### 数据库备份

该命令会备份当前 OVN 数据库至本地，可用于灾备和恢复

```bash
# kubectl ko nb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnnb_db.060223191654183154.backup
```

#### 数据库存储状态查看

该命令用来查看数据库文件是否存在损坏



#### 数据库恢复
