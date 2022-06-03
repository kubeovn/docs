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

### [nb | sb] [status | kick | backup | dbstatus | restore]

该子命令主要对 OVN 北向或南向数据库进行操作，包括数据库集群状态查看，数据库节点下线，
数据库备份，数据库存储状态查看和数据库修复。

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

```bash
# kubectl ko nb dbstatus
status: ok
```

若异常则显示 `inconsistent data` 需要使用下面的命令进行修复

#### 数据库修复

若数据库状态进入 `inconsistent data` 可使用该命令进行修复

```bash
# kubectl ko nb restore
deployment.apps/ovn-central scaled
ovn-central original replicas is 3
first nodeIP is 172.18.0.5
ovs-ovn pod on node 172.18.0.5 is ovs-ovn-8jxv9
ovs-ovn pod on node 172.18.0.3 is ovs-ovn-sjzb6
ovs-ovn pod on node 172.18.0.4 is ovs-ovn-t87zk
backup nb db file
restore nb db file, operate in pod ovs-ovn-8jxv9
deployment.apps/ovn-central scaled
finish restore nb db file and ovn-central replicas
recreate ovs-ovn pods
pod "ovs-ovn-8jxv9" deleted
pod "ovs-ovn-sjzb6" deleted
pod "ovs-ovn-t87zk" deleted
```

### [nbctl | sbctl] [options ...]

该子命令会直接进入 OVN 北向数据库或南向数据库 的 leader 节点分别执行 `ovn-nbctl` 和 `ovn-sbctl` 命令。
更多该命令的详细用法请查询上游 OVN 的官方文档 [ovn-nbctl(8)](https://man7.org/linux/man-pages/man8/ovn-nbctl.8.html) 和 [ovn-sbctl(8)](https://man7.org/linux/man-pages/man8/ovn-sbctl.8.html)

```bash
# kubectl ko nbctl show
switch c7cd17e8-ceee-4a91-9bb3-e5a313fe1ece (snat)
    port snat-ovn-cluster
        type: router
        router-port: ovn-cluster-snat
switch 20e0c6d0-023a-4756-aec5-200e0c60f95d (join)
    port node-liumengxin-ovn3-192.168.137.178
        addresses: ["00:00:00:64:FF:A8 100.64.0.4"]
    port node-liumengxin-ovn1-192.168.137.176
        addresses: ["00:00:00:AF:98:62 100.64.0.2"]
    port node-liumengxin-ovn2-192.168.137.177
        addresses: ["00:00:00:D9:58:B8 100.64.0.3"]
    port join-ovn-cluster
        type: router
        router-port: ovn-cluster-join
switch 0191705c-f827-427b-9de3-3c3b7d971ba5 (central)
    port central-ovn-cluster
        type: router
        router-port: ovn-cluster-central
switch 2a45ff05-388d-4f85-9daf-e6fccd5833dc (ovn-default)
    port perf-6vxkn.default
        addresses: ["00:00:00:82:84:71 10.16.0.2"]
    port grafana-6c4c6b8fb7-pzd2c.monitoring
        addresses: ["00:00:00:82:5E:9B 10.16.0.7"]
    port kube-ovn-pinger-7twb4.kube-system
        addresses: ["00:00:00:DC:E3:63 10.16.63.30"]
    port prometheus-operator-7bbc99fc8b-wgjm4.monitoring
        addresses: ["00:00:00:8F:31:15 10.16.0.18"]
    port kube-ovn-pinger-6ftdf.kube-system
        addresses: ["00:00:00:FA:1E:50 10.16.0.10"]
    port lsp1
    port alertmanager-main-0.monitoring
        addresses: ["00:00:00:6C:DF:A3 10.16.0.19"]
    port kube-state-metrics-5d6885d89-4nf8h.monitoring
        addresses: ["00:00:00:6F:02:1C 10.16.0.15"]
    port fake-kubelet-67c55dfd89-pv86k.kube-system
        addresses: ["00:00:00:5C:12:E8 10.16.19.177"]
    port ovn-default-ovn-cluster
        type: router
        router-port: ovn-cluster-ovn-default
    port alertmanager-main-1.monitoring
        addresses: ["00:00:00:F9:74:F7 10.16.0.20"]
    port coredns-6789c94dd8-25d4r.kube-system
        addresses: ["00:00:00:23:65:24 10.16.0.9"]
    port kube-ovn-pinger-vh2xg.kube-system
        addresses: ["00:00:00:F8:07:C8 10.16.0.5"]
    port prometheus-k8s-0.monitoring
        addresses: ["00:00:00:76:15:F8 10.16.0.22"]
    port perf-fjnws.default
        addresses: ["00:00:00:2A:14:75 10.16.0.14"]
    port prometheus-adapter-86df476d87-rl88g.monitoring
        addresses: ["00:00:00:DA:B0:35 10.16.0.16"]
    port perf-ff475.default
        addresses: ["00:00:00:56:1B:67 10.16.0.8"]
    port alertmanager-main-2.monitoring
        addresses: ["00:00:00:CB:56:43 10.16.0.21"]
    port prometheus-adapter-86df476d87-gdxmc.monitoring
        addresses: ["00:00:00:94:31:DD 10.16.0.12"]
    port coredns-6789c94dd8-9jqsz.kube-system
        addresses: ["00:00:00:40:A1:95 10.16.0.4"]
    port blackbox-exporter-676d976865-tvsjd.monitoring
        addresses: ["00:00:00:BF:9C:FC 10.16.0.13"]
    port prometheus-k8s-1.monitoring
        addresses: ["00:00:00:AA:37:DF 10.16.0.23"]
router 212f73dd-d63d-4d72-864b-a537e9afbee1 (ovn-cluster)
    port ovn-cluster-snat
        mac: "00:00:00:7A:82:8F"
        networks: ["172.22.0.1/16"]
    port ovn-cluster-join
        mac: "00:00:00:F8:18:5A"
        networks: ["100.64.0.1/16"]
    port ovn-cluster-central
        mac: "00:00:00:4D:8C:F5"
        networks: ["192.101.0.1/16"]
    port ovn-cluster-ovn-default
        mac: "00:00:00:A3:F8:18"
        networks: ["10.16.0.1/16"]
```

### vsctl {nodeName} [options ...]

该命令会进入对应 `nodeName` 上的 `ovs-ovn` 容器，并执行相应的 `ovs-vsctl` 命令，查询并配置 `vswitchd`。
更多该命令的详细用法请查询上游 OVS 的官方文档 [ovs-vsctl(8)](https://man7.org/linux/man-pages/man8/ovs-vsctl.8.html)

```bash
# kubectl ko vsctl kube-ovn-01 show
0d4c4675-c9cc-440a-8c1a-878e17f81b88
    Bridge br-int
        fail_mode: secure
        datapath_type: system
        Port a2c1a8a8b83a_h
            Interface a2c1a8a8b83a_h
        Port "4fa5c4cbb1a5_h"
            Interface "4fa5c4cbb1a5_h"
        Port ovn-eef07d-0
            Interface ovn-eef07d-0
                type: stt
                options: {csum="true", key=flow, remote_ip="192.168.137.178"}
        Port ovn0
            Interface ovn0
                type: internal
        Port "04d03360e9a0_h"
            Interface "04d03360e9a0_h"
        Port eeb4d9e51b5d_h
            Interface eeb4d9e51b5d_h
        Port mirror0
            Interface mirror0
                type: internal
        Port "8e5d887ccd80_h"
            Interface "8e5d887ccd80_h"
        Port ovn-efa253-0
            Interface ovn-efa253-0
                type: stt
                options: {csum="true", key=flow, remote_ip="192.168.137.177"}
        Port "17512d5be1f1_h"
            Interface "17512d5be1f1_h"
        Port br-int
            Interface br-int
                type: internal
    ovs_version: "2.17.2"
```

### ofctl {nodeName} [options ...]

该命令会进入对应 `nodeName` 上的 `ovs-ovn` 容器，并执行相应的 `ovs-ofctl` 命令，查询或管理 OpenFlow
更多该命令的详细用法请查询上游 OVS 的官方文档 [ovs-ofctl(8)](https://man7.org/linux/man-pages/man8/ovs-ofctl.8.html)

```bash
# kubectl ko ofctl kube-ovn-01 dump-flows br-int
NXST_FLOW reply (xid=0x4): flags=[more]
 cookie=0xcf3429e6, duration=671791.432s, table=0, n_packets=0, n_bytes=0, idle_age=65534, hard_age=65534, priority=100,in_port=2 actions=load:0x4->NXM_NX_REG13[],load:0x9->NXM_NX_REG11[],load:0xb->NXM_NX_REG12[],load:0x4->OXM_OF_METADATA[],load:0x1->NXM_NX_REG14[],resubmit(,8)
 cookie=0xc91413c6, duration=671791.431s, table=0, n_packets=907489, n_bytes=99978275, idle_age=0, hard_age=65534, priority=100,in_port=7 actions=load:0x1->NXM_NX_REG13[],load:0x9->NXM_NX_REG11[],load:0xb->NXM_NX_REG12[],load:0x4->OXM_OF_METADATA[],load:0x4->NXM_NX_REG14[],resubmit(,8)
 cookie=0xf180459, duration=671791.431s, table=0, n_packets=17348582, n_bytes=2667811214, idle_age=0, hard_age=65534, priority=100,in_port=6317 actions=load:0xa->NXM_NX_REG13[],load:0x9->NXM_NX_REG11[],load:0xb->NXM_NX_REG12[],load:0x4->OXM_OF_METADATA[],load:0x9->NXM_NX_REG14[],resubmit(,8)
 cookie=0x7806dd90, duration=671791.431s, table=0, n_packets=3235428, n_bytes=833821312, idle_age=0, hard_age=65534, priority=100,in_port=1 actions=load:0xd->NXM_NX_REG13[],load:0x9->NXM_NX_REG11[],load:0xb->NXM_NX_REG12[],load:0x4->OXM_OF_METADATA[],load:0x3->NXM_NX_REG14[],resubmit(,8)
...
```

### dpctl {nodeName} [options ...]

该命令会进入对应 `nodeName` 上的 `ovs-ovn` 容器，并执行相应的 `ovs-dpctl` 命令，查询或管理 OVS datapath
更多该命令的详细用法请查询上游 OVS 的官方文档 [ovs-dpctl(8)](https://man7.org/linux/man-pages/man8/ovs-dpctl.8.html)

```bash
# kubectl ko dpctl kube-ovn-01 show
system@ovs-system:
  lookups: hit:350805055 missed:21983648 lost:73
  flows: 105
  masks: hit:1970748791 total:22 hit/pkt:5.29
  port 0: ovs-system (internal)
  port 1: ovn0 (internal)
  port 2: mirror0 (internal)
  port 3: br-int (internal)
  port 4: stt_sys_7471 (stt: packet_type=ptap)
  port 5: eeb4d9e51b5d_h
  port 6: a2c1a8a8b83a_h
  port 7: 4fa5c4cbb1a5_h
  port 8: 17512d5be1f1_h
  port 9: 04d03360e9a0_h
  port 10: 8e5d887ccd80_h
```

### appctl {nodeName} [options ...]

该命令会进入对应 `nodeName` 上的 `ovs-ovn` 容器，并执行相应的 `ovs-appctl` 命令，来操作相关 daemon 进程
更多该命令的详细用法请查询上游 OVS 的官方文档 [ovs-appctl(8)](https://man7.org/linux/man-pages/man8/ovs-appctl.8.html)

```bash
# kubectl ko appctl kube-ovn-01 vlog/list
                 console    syslog    file
                 -------    ------    ------
backtrace          OFF        ERR       INFO
bfd                OFF        ERR       INFO
bond               OFF        ERR       INFO
bridge             OFF        ERR       INFO
bundle             OFF        ERR       INFO
bundles            OFF        ERR       INFO
...
```
