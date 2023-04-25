# Kubectl Plugin

To facilitate daily operations and maintenance, Kube-OVN provides the kubectl plug-in tool, which allows administrators to perform daily operations through this command.
For examples: Check OVN database information and status, OVN database backup and restore, OVS related information,
tcpdump specific containers, specific link logical topology, network problem diagnosis and performance optimization.

## Plugin Installation

Kube-OVN installation will deploy the plugin to each node by default.
If the machine that runs kubectl is not in the cluster,
or if you need to reinstall the plugin, please refer to the following steps:

Download `kubectl-ko` file:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/kubectl-ko
```

Move file to `$PATH`:

```bash
mv kubectl-ko /usr/local/bin/kubectl-ko
```

Add executable permissions:

```bash
chmod +x /usr/local/bin/kubectl-ko
```

Check if the plugin works properly:

```bash
# kubectl plugin list
The following compatible plugins are available:

/usr/local/bin/kubectl-ko
```

## Plugin Usage

Running `kubectl ko` will show all the available commands and usage descriptions, as follows:

```bash
# kubectl ko
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
  trace {namespace/podname} {target ip address} [target mac address] {icmp|tcp|udp} [target tcp/udp port]    trace ICMP/TCP/UDP
  trace {namespace/podname} {target ip address} [target mac address] arp {request|reply}                     trace ARP request/reply
  trace {node//nodename} {target ip address} [target mac address] {icmp|tcp|udp} [target tcp/udp port]       trace ICMP/TCP/UDP
  trace {node//nodename} {target ip address} [target mac address] arp {request|reply}                        trace ARP request/reply
  diagnose {all|node} [nodename]    diagnose connectivity of all nodes or a specific node
  tuning {install-fastpath|local-install-fastpath|remove-fastpath|install-stt|local-install-stt|remove-stt} {centos7|centos8}} [kernel-devel-version]  deploy  kernel optimisation components to the system
  reload    restart all kube-ovn components
```

The specific functions and usage of each command are described below.

### [nb | sb] [status | kick | backup | dbstatus | restore]

This subcommand mainly operates on OVN northbound or southbound databases,
including database cluster status check, database node offline, database backup,
database storage status check and database repair.

#### DB Cluster Status Check

This command executes `ovs-appctl cluster/status` on the leader node of the corresponding OVN database to show the cluster status:

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

If the `match_index` under `Server` has a large difference and the `last msg` time is long,
the corresponding Server may not respond for a long time and needs to be checked further.

#### DB Nodes Offline

This command removes a node from the OVN database and is required when a node is taken offline or replaced.
The following is an example of the cluster status from the previous command, to offline the `172.18.0.3` node:

```bash
# kubectl ko nb kick 8723
started removal
```

Check the database cluster status again to confirm that the node has been removed:

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

#### DB Backup

This subcommand backs up the current OVN database locally and can be used for disaster recovery:

```bash
# kubectl ko nb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnnb_db.060223191654183154.backup
```

#### Database Storage Status Check

This command is used to check if the database file is corrupt:

```bash
# kubectl ko nb dbstatus
status: ok
```

If error happens, `inconsistent data` is displayed and needs to be fixed with the following command.

#### Database Repair

If the database status goes to `inconsistent data`, this command can be used to repair:

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

This subcommand executes the `ovn-nbctl` and `ovn-sbctl` commands directly into the leader node of the OVN northbound or southbound database.
For more detailed usage of this command, please refer to the official documentation of the upstream OVN [ovn-nbctl(8)](https://man7.org/linux/man-pages/man8/ovn-nbctl.8.html){: target="_blank" } 和 [ovn-sbctl(8)](https://man7.org/linux/man-pages/man8/ovn-sbctl.8.html){: target="_blank" }。

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
    port alertmanager-main-0.monitoring
        addresses: ["00:00:00:6C:DF:A3 10.16.0.19"]
    port kube-state-metrics-5d6885d89-4nf8h.monitoring
        addresses: ["00:00:00:6F:02:1C 10.16.0.15"]
    port fake-kubelet-67c55dfd89-pv86k.kube-system
        addresses: ["00:00:00:5C:12:E8 10.16.19.177"]
    port ovn-default-ovn-cluster
        type: router
        router-port: ovn-cluster-ovn-default
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

This command will go to the `ovs-ovn` container on the corresponding `nodeName` and execute the corresponding `ovs-vsctl` command to query and configure `vswitchd`.
For more detailed usage of this command, please refer to the official documentation of the upstream OVS [ovs-vsctl(8)](https://man7.org/linux/man-pages/man8/ovs-vsctl.8.html){: target="_blank" }。

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
        Port mirror0
            Interface mirror0
                type: internal
        Port ovn-efa253-0
            Interface ovn-efa253-0
                type: stt
                options: {csum="true", key=flow, remote_ip="192.168.137.177"}
        Port br-int
            Interface br-int
                type: internal
    ovs_version: "2.17.2"
```

### ofctl {nodeName} [options ...]

This command will go to the `ovs-ovn` container on the corresponding `nodeName` and execute the corresponding `ovs-ofctl` command to query or manage OpenFlow.
For more detailed usage of this command, please refer to the official documentation of the upstream OVS [ovs-ofctl(8)](https://man7.org/linux/man-pages/man8/ovs-ofctl.8.html){: target="_blank" }。

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

This command will go to the `ovs-ovn` container on the corresponding `nodeName` and execute the corresponding `ovs-dpctl` command to query or manage the OVS datapath.
For more detailed usage of this command, please refer to the official documentation of the upstream OVS [ovs-dpctl(8)](https://man7.org/linux/man-pages/man8/ovs-dpctl.8.html){: target="_blank" }。

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
```

### appctl {nodeName} [options ...]

This command will enter the `ovs-ovn` container on the corresponding `nodeName` and execute the corresponding `ovs-appctl` command to operate the associated daemon process.
For more detailed usage of this command, please refer to the official documentation of the upstream OVS [ovs-appctl(8)](https://man7.org/linux/man-pages/man8/ovs-appctl.8.html){: target="_blank" }。

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

### tcpdump {namespace/podname} [tcpdump options ...]

This command will enter the `kube-ovn-cni` container on the machine where `namespace/podname` is located,
and run `tcpdump` to capture the traffic on the veth NIC of the corresponding container,
which can be used to troubleshoot network-related problems.

```bash
# kubectl ko tcpdump default/ds1-l6n7p icmp
+ kubectl exec -it kube-ovn-cni-wlg4s -n kube-ovn -- tcpdump -nn -i d7176fe7b4e0_h icmp
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on d7176fe7b4e0_h, link-type EN10MB (Ethernet), capture size 262144 bytes
06:52:36.619688 IP 100.64.0.3 > 10.16.0.4: ICMP echo request, id 2, seq 1, length 64
06:52:36.619746 IP 10.16.0.4 > 100.64.0.3: ICMP echo reply, id 2, seq 1, length 64
06:52:37.619588 IP 100.64.0.3 > 10.16.0.4: ICMP echo request, id 2, seq 2, length 64
06:52:37.619630 IP 10.16.0.4 > 100.64.0.3: ICMP echo reply, id 2, seq 2, length 64
06:52:38.619933 IP 100.64.0.3 > 10.16.0.4: ICMP echo request, id 2, seq 3, length 64
06:52:38.619973 IP 10.16.0.4 > 100.64.0.3: ICMP echo reply, id 2, seq 3, length 64
```

### trace [arguments ...]

This command will print the OVN logical flow table and the final Openflow flow table when the Pod/node accesses an address through a specific protocol,
so that it make locate flow table related problems during development or troubleshooting much easy.

Supported commands:

```bash
kubectl ko trace {namespace/podname} {target ip address} [target mac address] {icmp|tcp|udp} [target tcp/udp port]
kubectl ko trace {namespace/podname} {target ip address} [target mac address] arp {request|reply}
kubectl ko trace {node//nodename} {target ip address} [target mac address] {icmp|tcp|udp} [target tcp/udp port]
kubectl ko trace {node//nodename} {target ip address} [target mac address] arp {request|reply}
```

Example:

```bash
# kubectl ko trace default/ds1-l6n7p 8.8.8.8 icmp
+ kubectl exec ovn-central-5bc494cb5-np9hm -n kube-ovn -- ovn-trace --ct=new ovn-default 'inport == "ds1-l6n7p.default" && ip.ttl == 64 && icmp && eth.src == 0a:00:00:10:00:05 && ip4.src == 10.16.0.4 && eth.dst == 00:00:00:B8:CA:43 && ip4.dst == 8.8.8.8'
# icmp,reg14=0xf,vlan_tci=0x0000,dl_src=0a:00:00:10:00:05,dl_dst=00:00:00:b8:ca:43,nw_src=10.16.0.4,nw_dst=8.8.8.8,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=0,icmp_code=0

ingress(dp="ovn-default", inport="ds1-l6n7p.default")
-----------------------------------------------------
 0. ls_in_port_sec_l2 (ovn-northd.c:4143): inport == "ds1-l6n7p.default" && eth.src == {0a:00:00:10:00:05}, priority 50, uuid 39453393
    next;
 1. ls_in_port_sec_ip (ovn-northd.c:2898): inport == "ds1-l6n7p.default" && eth.src == 0a:00:00:10:00:05 && ip4.src == {10.16.0.4}, priority 90, uuid 81bcd485
    next;
 3. ls_in_pre_acl (ovn-northd.c:3269): ip, priority 100, uuid 7b4f4971
    reg0[0] = 1;
    next;
 5. ls_in_pre_stateful (ovn-northd.c:3396): reg0[0] == 1, priority 100, uuid 36cdd577
    ct_next;

ct_next(ct_state=new|trk)
-------------------------
 6. ls_in_acl (ovn-northd.c:3759): ip && (!ct.est || (ct.est && ct_label.blocked == 1)), priority 1, uuid 7608af5b
    reg0[1] = 1;
    next;
10. ls_in_stateful (ovn-northd.c:3995): reg0[1] == 1, priority 100, uuid 2aba1b90
    ct_commit(ct_label=0/0x1);
    next;
16. ls_in_l2_lkup (ovn-northd.c:4470): eth.dst == 00:00:00:b8:ca:43, priority 50, uuid 5c9c3c9f
    outport = "ovn-default-ovn-cluster";
    output;

...
```

If the trace object is a virtual machine running  in Underlay network, additional parameters is needed to specify the destination Mac address.

```bash
kubectl ko trace default/virt-handler-7lvml 8.8.8.8 82:7c:9f:83:8c:01 icmp
```

### diagnose {all|node} [nodename]

Diagnose the status of cluster network components and go to the corresponding node's `kube-ovn-pinger`
to detect connectivity and network latency from the current node to other nodes and critical services.

```bash
# kubectl ko diagnose all
switch c7cd17e8-ceee-4a91-9bb3-e5a313fe1ece (snat)
    port snat-ovn-cluster
        type: router
        router-port: ovn-cluster-snat
switch 20e0c6d0-023a-4756-aec5-200e0c60f95d (join)
    port node-liumengxin-ovn3-192.168.137.178
        addresses: ["00:00:00:64:FF:A8 100.64.0.4"]
    port node-liumengxin-ovn1-192.168.137.176
        addresses: ["00:00:00:AF:98:62 100.64.0.2"]
    port join-ovn-cluster
        type: router
        router-port: ovn-cluster-join
switch 0191705c-f827-427b-9de3-3c3b7d971ba5 (central)
    port central-ovn-cluster
        type: router
        router-port: ovn-cluster-central
switch 2a45ff05-388d-4f85-9daf-e6fccd5833dc (ovn-default)
    port ovn-default-ovn-cluster
        type: router
        router-port: ovn-cluster-ovn-default
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
Routing Policies
     31000                            ip4.dst == 10.16.0.0/16           allow
     31000                           ip4.dst == 100.64.0.0/16           allow
     30000                         ip4.dst == 192.168.137.177         reroute                100.64.0.3
     30000                         ip4.dst == 192.168.137.178         reroute                100.64.0.4
     29000                 ip4.src == $ovn.default.fake.6_ip4         reroute               100.64.0.22
     29000                 ip4.src == $ovn.default.fake.7_ip4         reroute               100.64.0.21
     29000                 ip4.src == $ovn.default.fake.8_ip4         reroute               100.64.0.23
     29000 ip4.src == $ovn.default.liumengxin.ovn3.192.168.137.178_ip4         reroute                100.64.0.4
     20000 ip4.src == $ovn.default.liumengxin.ovn1.192.168.137.176_ip4 && ip4.dst != $ovn.cluster.overlay.subnets.IPv4         reroute                100.64.0.2
     20000 ip4.src == $ovn.default.liumengxin.ovn2.192.168.137.177_ip4 && ip4.dst != $ovn.cluster.overlay.subnets.IPv4         reroute                100.64.0.3
     20000 ip4.src == $ovn.default.liumengxin.ovn3.192.168.137.178_ip4 && ip4.dst != $ovn.cluster.overlay.subnets.IPv4         reroute                100.64.0.4
IPv4 Routes
Route Table <main>:
                0.0.0.0/0                100.64.0.1 dst-ip
UUID                                    LB                  PROTO      VIP                     IPs
e9bcfd9d-793e-4431-9073-6dec96b75d71    cluster-tcp-load    tcp        10.100.209.132:10660    192.168.137.176:10660
                                                            tcp        10.101.239.192:6641     192.168.137.177:6641
                                                            tcp        10.101.240.101:3000     10.16.0.7:3000
                                                            tcp        10.103.184.186:6642     192.168.137.177:6642
35d2b7a5-e3a7-485a-a4b7-b4970eb0e63b    cluster-tcp-sess    tcp        10.100.158.128:8080     10.16.0.10:8080,10.16.0.5:8080,10.16.63.30:8080
                                                            tcp        10.107.26.215:8080      10.16.0.19:8080,10.16.0.20:8080,10.16.0.21:8080
                                                            tcp        10.107.26.215:9093      10.16.0.19:9093,10.16.0.20:9093,10.16.0.21:9093
                                                            tcp        10.98.187.99:8080       10.16.0.22:8080,10.16.0.23:8080
                                                            tcp        10.98.187.99:9090       10.16.0.22:9090,10.16.0.23:9090
f43303e4-89aa-4d3e-a3dc-278a552fe27b    cluster-udp-load    udp        10.96.0.10:53           10.16.0.4:53,10.16.0.9:53
_uuid               : 06776304-5a96-43ed-90c4-c4854c251699
addresses           : []
external_ids        : {vendor=kube-ovn}
name                : node_liumengxin_ovn2_192.168.137.177_underlay_v6

_uuid               : 62690625-87d5-491c-8675-9fd83b1f433c
addresses           : []
external_ids        : {vendor=kube-ovn}
name                : node_liumengxin_ovn1_192.168.137.176_underlay_v6

_uuid               : b03a9bae-94d5-4562-b34c-b5f6198e180b
addresses           : ["10.16.0.0/16", "100.64.0.0/16", "172.22.0.0/16", "192.101.0.0/16"]
external_ids        : {vendor=kube-ovn}
name                : ovn.cluster.overlay.subnets.IPv4

_uuid               : e1056f3a-24cc-4666-8a91-75ee6c3c2426
addresses           : []
external_ids        : {vendor=kube-ovn}
name                : ovn.cluster.overlay.subnets.IPv6

_uuid               : 3e5d5fff-e670-47b2-a2f5-a39f4698a8c5
addresses           : []
external_ids        : {vendor=kube-ovn}
name                : node_liumengxin_ovn3_192.168.137.178_underlay_v6
_uuid               : 2d85dbdc-d0db-4abe-b19e-cc806d32b492
action              : drop
direction           : from-lport
external_ids        : {}
label               : 0
log                 : false
match               : "inport==@ovn.sg.kubeovn_deny_all && ip"
meter               : []
name                : []
options             : {}
priority            : 2003
severity            : []

_uuid               : de790cc8-f155-405f-bb32-5a51f30c545f
action              : drop
direction           : to-lport
external_ids        : {}
label               : 0
log                 : false
match               : "outport==@ovn.sg.kubeovn_deny_all && ip"
meter               : []
name                : []
options             : {}
priority            : 2003
severity            : []
Chassis "e15ed4d4-1780-4d50-b09e-ea8372ed48b8"
    hostname: liumengxin-ovn1-192.168.137.176
    Encap stt
        ip: "192.168.137.176"
        options: {csum="true"}
    Port_Binding node-liumengxin-ovn1-192.168.137.176
    Port_Binding perf-6vxkn.default
    Port_Binding kube-state-metrics-5d6885d89-4nf8h.monitoring
    Port_Binding alertmanager-main-0.monitoring
    Port_Binding kube-ovn-pinger-6ftdf.kube-system
    Port_Binding fake-kubelet-67c55dfd89-pv86k.kube-system
    Port_Binding prometheus-k8s-0.monitoring
Chassis "eef07da1-f8ad-4775-b14d-bd6a3b4eb0d5"
    hostname: liumengxin-ovn3-192.168.137.178
    Encap stt
        ip: "192.168.137.178"
        options: {csum="true"}
    Port_Binding kube-ovn-pinger-7twb4.kube-system
    Port_Binding prometheus-adapter-86df476d87-rl88g.monitoring
    Port_Binding prometheus-k8s-1.monitoring
    Port_Binding node-liumengxin-ovn3-192.168.137.178
    Port_Binding perf-ff475.default
    Port_Binding alertmanager-main-1.monitoring
    Port_Binding blackbox-exporter-676d976865-tvsjd.monitoring
Chassis "efa253c9-494d-4719-83ae-b48ab0f11c03"
    hostname: liumengxin-ovn2-192.168.137.177
    Encap stt
        ip: "192.168.137.177"
        options: {csum="true"}
    Port_Binding grafana-6c4c6b8fb7-pzd2c.monitoring
    Port_Binding node-liumengxin-ovn2-192.168.137.177
    Port_Binding alertmanager-main-2.monitoring
    Port_Binding coredns-6789c94dd8-9jqsz.kube-system
    Port_Binding coredns-6789c94dd8-25d4r.kube-system
    Port_Binding prometheus-operator-7bbc99fc8b-wgjm4.monitoring
    Port_Binding prometheus-adapter-86df476d87-gdxmc.monitoring
    Port_Binding perf-fjnws.default
    Port_Binding kube-ovn-pinger-vh2xg.kube-system
ds kube-proxy ready
kube-proxy ready
deployment ovn-central ready
deployment kube-ovn-controller ready
ds kube-ovn-cni ready
ds ovs-ovn ready
deployment coredns ready
ovn-nb leader check ok
ovn-sb leader check ok
ovn-northd leader check ok
### kube-ovn-controller recent log

### start to diagnose node liumengxin-ovn1-192.168.137.176
#### ovn-controller log:
2022-06-03T00:56:44.897Z|16722|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T01:06:44.912Z|16723|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T01:16:44.925Z|16724|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T01:26:44.936Z|16725|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T01:36:44.959Z|16726|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T01:46:44.974Z|16727|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T01:56:44.988Z|16728|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T02:06:45.001Z|16729|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T02:16:45.025Z|16730|inc_proc_eng|INFO|User triggered force recompute.
2022-06-03T02:26:45.040Z|16731|inc_proc_eng|INFO|User triggered force recompute.

#### ovs-vswitchd log:
2022-06-02T23:03:00.137Z|00079|dpif(handler1)|WARN|system@ovs-system: execute ct(commit,zone=14,label=0/0x1,nat(src)),8 failed (Invalid argument) on packet icmp,vlan_tci=0x0000,dl_src=00:00:00:f8:07:c8,dl_dst=00:00:00:fa:1e:50,nw_src=10.16.0.5,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0 icmp_csum:f9d1
 with metadata skb_priority(0),tunnel(tun_id=0x160017000004,src=192.168.137.177,dst=192.168.137.176,ttl=64,tp_src=38881,tp_dst=7471,flags(csum|key)),skb_mark(0),ct_state(0x21),ct_zone(0xe),ct_tuple4(src=10.16.0.5,dst=10.16.0.10,proto=1,tp_src=8,tp_dst=0),in_port(4) mtu 0
2022-06-02T23:23:31.840Z|00080|dpif(handler1)|WARN|system@ovs-system: execute ct(commit,zone=14,label=0/0x1,nat(src)),8 failed (Invalid argument) on packet icmp,vlan_tci=0x0000,dl_src=00:00:00:f8:07:c8,dl_dst=00:00:00:fa:1e:50,nw_src=10.16.0.5,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0 icmp_csum:15b2
 with metadata skb_priority(0),tunnel(tun_id=0x160017000004,src=192.168.137.177,dst=192.168.137.176,ttl=64,tp_src=38881,tp_dst=7471,flags(csum|key)),skb_mark(0),ct_state(0x21),ct_zone(0xe),ct_tuple4(src=10.16.0.5,dst=10.16.0.10,proto=1,tp_src=8,tp_dst=0),in_port(4) mtu 0
2022-06-03T00:09:15.659Z|00081|dpif(handler1)|WARN|system@ovs-system: execute ct(commit,zone=14,label=0/0x1,nat(src)),8 failed (Invalid argument) on packet icmp,vlan_tci=0x0000,dl_src=00:00:00:dc:e3:63,dl_dst=00:00:00:fa:1e:50,nw_src=10.16.63.30,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0 icmp_csum:e5a5
 with metadata skb_priority(0),tunnel(tun_id=0x150017000004,src=192.168.137.178,dst=192.168.137.176,ttl=64,tp_src=9239,tp_dst=7471,flags(csum|key)),skb_mark(0),ct_state(0x21),ct_zone(0xe),ct_tuple4(src=10.16.63.30,dst=10.16.0.10,proto=1,tp_src=8,tp_dst=0),in_port(4) mtu 0
2022-06-03T00:30:13.409Z|00064|dpif(handler2)|WARN|system@ovs-system: execute ct(commit,zone=14,label=0/0x1,nat(src)),8 failed (Invalid argument) on packet icmp,vlan_tci=0x0000,dl_src=00:00:00:f8:07:c8,dl_dst=00:00:00:fa:1e:50,nw_src=10.16.0.5,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0 icmp_csum:6b4a
 with metadata skb_priority(0),tunnel(tun_id=0x160017000004,src=192.168.137.177,dst=192.168.137.176,ttl=64,tp_src=38881,tp_dst=7471,flags(csum|key)),skb_mark(0),ct_state(0x21),ct_zone(0xe),ct_tuple4(src=10.16.0.5,dst=10.16.0.10,proto=1,tp_src=8,tp_dst=0),in_port(4) mtu 0
2022-06-03T02:02:33.832Z|00082|dpif(handler1)|WARN|system@ovs-system: execute ct(commit,zone=14,label=0/0x1,nat(src)),8 failed (Invalid argument) on packet icmp,vlan_tci=0x0000,dl_src=00:00:00:f8:07:c8,dl_dst=00:00:00:fa:1e:50,nw_src=10.16.0.5,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0 icmp_csum:a819
 with metadata skb_priority(0),tunnel(tun_id=0x160017000004,src=192.168.137.177,dst=192.168.137.176,ttl=64,tp_src=38881,tp_dst=7471,flags(csum|key)),skb_mark(0),ct_state(0x21),ct_zone(0xe),ct_tuple4(src=10.16.0.5,dst=10.16.0.10,proto=1,tp_src=8,tp_dst=0),in_port(4) mtu 0

#### ovs-vsctl show results:
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

#### pinger diagnose results:
I0603 10:35:04.349404   17619 pinger.go:19]
-------------------------------------------------------------------------------
Kube-OVN:
  Version:       {{ variables.version }}
  Build:         2022-04-24_08:02:50
  Commit:        git-73f9d15
  Go Version:    go1.17.8
  Arch:          amd64
-------------------------------------------------------------------------------
I0603 10:35:04.376797   17619 config.go:166] pinger config is &{KubeConfigFile: KubeClient:0xc000493380 Port:8080 DaemonSetNamespace:kube-system DaemonSetName:kube-ovn-pinger Interval:5 Mode:job ExitCode:0 InternalDNS:kubernetes.default ExternalDNS: NodeName:liumengxin-ovn1-192.168.137.176 HostIP:192.168.137.176 PodName:kube-ovn-pinger-6ftdf PodIP:10.16.0.10 PodProtocols:[IPv4] ExternalAddress: NetworkMode:kube-ovn PollTimeout:2 PollInterval:15 SystemRunDir:/var/run/openvswitch DatabaseVswitchName:Open_vSwitch DatabaseVswitchSocketRemote:unix:/var/run/openvswitch/db.sock DatabaseVswitchFileDataPath:/etc/openvswitch/conf.db DatabaseVswitchFileLogPath:/var/log/openvswitch/ovsdb-server.log DatabaseVswitchFilePidPath:/var/run/openvswitch/ovsdb-server.pid DatabaseVswitchFileSystemIDPath:/etc/openvswitch/system-id.conf ServiceVswitchdFileLogPath:/var/log/openvswitch/ovs-vswitchd.log ServiceVswitchdFilePidPath:/var/run/openvswitch/ovs-vswitchd.pid ServiceOvnControllerFileLogPath:/var/log/ovn/ovn-controller.log ServiceOvnControllerFilePidPath:/var/run/ovn/ovn-controller.pid}
I0603 10:35:04.449166   17619 exporter.go:75] liumengxin-ovn1-192.168.137.176: exporter connect successfully
I0603 10:35:04.554011   17619 ovn.go:21] ovs-vswitchd and ovsdb are up
I0603 10:35:04.651293   17619 ovn.go:33] ovn_controller is up
I0603 10:35:04.651342   17619 ovn.go:39] start to check port binding
I0603 10:35:04.749613   17619 ovn.go:135] chassis id is 1d7f3d6c-eec5-4b3c-adca-2969d9cdfd80
I0603 10:35:04.763487   17619 ovn.go:49] port in sb is [node-liumengxin-ovn1-192.168.137.176 perf-6vxkn.default kube-state-metrics-5d6885d89-4nf8h.monitoring alertmanager-main-0.monitoring kube-ovn-pinger-6ftdf.kube-system fake-kubelet-67c55dfd89-pv86k.kube-system prometheus-k8s-0.monitoring]
I0603 10:35:04.763583   17619 ovn.go:61] ovs and ovn-sb binding check passed
I0603 10:35:05.049309   17619 ping.go:259] start to check apiserver connectivity
I0603 10:35:05.053666   17619 ping.go:268] connect to apiserver success in 4.27ms
I0603 10:35:05.053786   17619 ping.go:129] start to check pod connectivity
I0603 10:35:05.249590   17619 ping.go:159] ping pod: kube-ovn-pinger-6ftdf 10.16.0.10, count: 3, loss count 0, average rtt 16.30ms
I0603 10:35:05.354135   17619 ping.go:159] ping pod: kube-ovn-pinger-7twb4 10.16.63.30, count: 3, loss count 0, average rtt 1.81ms
I0603 10:35:05.458460   17619 ping.go:159] ping pod: kube-ovn-pinger-vh2xg 10.16.0.5, count: 3, loss count 0, average rtt 1.92ms
I0603 10:35:05.458523   17619 ping.go:83] start to check node connectivity
```

### tuning {install-fastpath|local-install-fastpath|remove-fastpath|install-stt|local-install-stt|remove-stt} {centos7|centos8}} [kernel-devel-version]

This command performs performance tuning related operations, please refer to [Performance Tunning](../advance/performance-tuning.en.md).

### reload

This command restarts all Kube-OVN related components:

```bash
# kubectl ko reload
pod "ovn-central-8684dd94bd-vzgcr" deleted
Waiting for deployment "ovn-central" rollout to finish: 0 of 1 updated replicas are available...
deployment "ovn-central" successfully rolled out
pod "ovs-ovn-bsnvz" deleted
pod "ovs-ovn-m9b98" deleted
pod "kube-ovn-controller-8459db5ff4-64c62" deleted
Waiting for deployment "kube-ovn-controller" rollout to finish: 0 of 1 updated replicas are available...
deployment "kube-ovn-controller" successfully rolled out
pod "kube-ovn-cni-2klnh" deleted
pod "kube-ovn-cni-t2jz4" deleted
Waiting for daemon set "kube-ovn-cni" rollout to finish: 0 of 2 updated pods are available...
Waiting for daemon set "kube-ovn-cni" rollout to finish: 1 of 2 updated pods are available...
daemon set "kube-ovn-cni" successfully rolled out
pod "kube-ovn-pinger-ln72z" deleted
pod "kube-ovn-pinger-w8lrk" deleted
Waiting for daemon set "kube-ovn-pinger" rollout to finish: 0 of 2 updated pods are available...
Waiting for daemon set "kube-ovn-pinger" rollout to finish: 1 of 2 updated pods are available...
daemon set "kube-ovn-pinger" successfully rolled out
pod "kube-ovn-monitor-7fb67d5488-7q6zb" deleted
Waiting for deployment "kube-ovn-monitor" rollout to finish: 0 of 1 updated replicas are available...
deployment "kube-ovn-monitor" successfully rolled out
```
