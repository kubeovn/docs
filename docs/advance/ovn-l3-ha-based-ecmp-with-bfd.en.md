# L3 snat gw HA based Ecmp static route with BFD

Custom vpc based on ovn snat after ecmp based static route hash to multiple gw node ovnext0 NICs out of the public network

- Supports bfd-based high availability
- Only supports hash load balancing

``` mermaid
graph LR

pod-->vpc-subnet-->vpc-->snat-->ecmp-->external-subnet-->gw-node1-ovnext0--> node1-external-switch
external-subnet-->gw-node2-ovnext0--> node2-external-switch
external-subnet-->gw-node3-ovnext0--> node3-external-switch
```

This functionis basically the same as [ovn-eip-fip-snat.md](./ovn-eip-fip-snat.md) .

As for the different parts, which will be specified in the following sections, mainly including the creation of ovn-eip of node-ext-gw type and the automatic maintenance of bfd as well as ecmp static routes based on vpc enable_bfd.

## 1. Deployment

### 1.1 Create the underlay public network

### 1.2 Default vpc enable eip_snat

### 1.3 Custom vpc enable eip snat fip function

The above section is exactly the same with [ovn-eip-fip-snat.md](./ovn-eip-fip-snat.md).

After these functions are verified, the vpc can be switched directly to the ecmp-based bfd static route based on the following way, or of course, switched directly back.

Before customizing vpc to use this feature, you need to provide some gateway nodes, at least 2.

``` yaml
# cat gw-node-eip.yaml
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: pc-node-1
spec:
  externalSubnet: external204
  type: node-ext-gw

---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: pc-node-2
spec:
  externalSubnet: external204
  type: node-ext-gw

---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: pc-node-3
spec:
  externalSubnet: external204
  type: node-ext-gw
```

Since this scenario is currently designed for vpc ecmp out of the public network, the gateway node above will not trigger the creation of a gateway NIC when there is no vpc enabled bfd, i.e. when there is no ovn eip (lrp) with enable bfd labeled, and will not be able to successfully start listening to the bfd session on the other side.

## 2. Custom vpc enable ecmp bfd L3 HA public network function

``` bash
# cat 01-vpc-ecmp-enable-external-bfd.yml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc1
spec:
  namespaces:
  - vpc1
  enableExternal: true
  enableBfd: true # bfd switch can be switched at will
  #enableBfd: false 


# cat 02-subnet.yml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: vpc1-subnet1
spec:
  cidrBlock: 192.168.0.0/24
  default: false
  disableGatewayCheck: false
  disableInterConnection: true
  enableEcmp: true  # enable ecmp
  gatewayNode: ""
  gatewayType: distributed
  #gatewayType: centralized
  natOutgoing: false
  private: false
  protocol: IPv4
  provider: ovn
  vpc: vpc1
  namespaces:
  - vpc1
```

**note:**

1. Customize ecmp under vpc to use only static ecmp bfd routes. vpc enableBfd and subnet enableEcmp will only take effect if they are enabled at the same time, before static ecmp bfd routes are automatically managed.
2. If the above configuration is turned off, it will automatically switch back to the regular default static route.
3. This feature is not available for the default vpc, only custom vpc is supported, the default vpc has more complex policy routing.
4. The enableEcmp of the subnet of the custom vpc uses only static routes, the gateway type gatewayType has no effect.
5. When EnableExternal is turned off in vpc, the external network cannot be passed inside vpc.
6. When EnableExternal is enabled on vpc, when EnableBfd is turned off, it will be based on the normal default route to the external network and will not have high availability.

``` bash
# After the above template is applied the ovn logic layer should see the following resources
# k get vpc
NAME          ENABLEEXTERNAL   ENABLEBFD   STANDBY   SUBNETS                                NAMESPACES
ovn-cluster   true                         true      ["external204","join","ovn-default"]
vpc1          true             true        true      ["vpc1-subnet1"]                       ["vpc1"]

# Default vpc does not support ENABLEBFD
# Custom vpc is supported and enabled

# 1. bfd table created
# k ko nbctl list bfd
_uuid               : be7df545-2c4c-4751-878f-b3507987f050
detect_mult         : 3
dst_ip              : "10.5.204.121"
external_ids        : {}
logical_port        : vpc1-external204
min_rx              : 100
min_tx              : 100
options             : {}
status              : up

_uuid               : 684c4489-5b59-4693-8d8c-3beab93f8093
detect_mult         : 3
dst_ip              : "10.5.204.109"
external_ids        : {}
logical_port        : vpc1-external204
min_rx              : 100
min_tx              : 100
options             : {}
status              : up

_uuid               : f0f62077-2ae9-4e79-b4f8-a446ec6e784c
detect_mult         : 3
dst_ip              : "10.5.204.108"
external_ids        : {}
logical_port        : vpc1-external204
min_rx              : 100
min_tx              : 100
options             : {}
status              : up

### Note that all statuses should normally be up

# 2. bfd ecmp static routes table created
# k ko nbctl lr-route-list vpc1
IPv4 Routes
Route Table <main>:
           192.168.0.0/24              10.5.204.108 src-ip ecmp ecmp-symmetric-reply bfd
           192.168.0.0/24              10.5.204.109 src-ip ecmp ecmp-symmetric-reply bfd
           192.168.0.0/24              10.5.204.121 src-ip ecmp ecmp-symmetric-reply bfd

# 3. Static Route Details
# k ko nbctl find Logical_Router_Static_Route  policy=src-ip options=ecmp_symmetric_reply="true"
_uuid               : 3aacb384-d5ee-4b14-aebf-59e8c11717ba
bfd                 : 684c4489-5b59-4693-8d8c-3beab93f8093
external_ids        : {}
ip_prefix           : "192.168.0.0/24"
nexthop             : "10.5.204.109"
options             : {ecmp_symmetric_reply="true"}
output_port         : []
policy              : src-ip
route_table         : ""

_uuid               : 18bcc585-bc05-430b-925b-ef673c8e1aef
bfd                 : f0f62077-2ae9-4e79-b4f8-a446ec6e784c
external_ids        : {}
ip_prefix           : "192.168.0.0/24"
nexthop             : "10.5.204.108"
options             : {ecmp_symmetric_reply="true"}
output_port         : []
policy              : src-ip
route_table         : ""

_uuid               : 7d0a4e6b-cde0-4110-8176-fbaf19738498
bfd                 : be7df545-2c4c-4751-878f-b3507987f050
external_ids        : {}
ip_prefix           : "192.168.0.0/24"
nexthop             : "10.5.204.121"
options             : {ecmp_symmetric_reply="true"}
output_port         : []
policy              : src-ip
route_table         : ""

```

``` bash
# Also, the following resources should be available at all gateway nodes

[root@pc-node-1 ~]# ip netns exec ovnext bash ip a
/usr/sbin/ip: /usr/sbin/ip: cannot execute binary file
[root@pc-node-1 ~]#
[root@pc-node-1 ~]# ip netns exec ovnext ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
1541: ovnext0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1400 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ether 00:00:00:ab:bd:87 brd ff:ff:ff:ff:ff:ff
    inet 10.5.204.108/24 brd 10.5.204.255 scope global ovnext0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:feab:bd87/64 scope link
       valid_lft forever preferred_lft forever
[root@pc-node-1 ~]#
[root@pc-node-1 ~]# ip netns exec ovnext route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.5.204.254    0.0.0.0         UG    0      0        0 ovnext0
10.5.204.0      0.0.0.0         255.255.255.0   U     0      0        0 ovnext0


[root@pc-node-1 ~]# ip netns exec ovnext bfdd-control status
There are 1 sessions:
Session 1
 id=1 local=10.5.204.108 (p) remote=10.5.204.122 state=Up

## This is the other end of the lrp bfd session and one of the next hops of the lrp ecmp


[root@pc-node-1 ~]# ip netns exec ovnext ping -c1 223.5.5.5
PING 223.5.5.5 (223.5.5.5) 56(84) bytes of data.
64 bytes from 223.5.5.5: icmp_seq=1 ttl=115 time=21.6 ms

# No problem to the public network
```

catch outgoing packets within the ovnext ns of a gateway node

```bash
# tcpdump -i ovnext0 host 223.5.5.5 -netvv
dropped privs to tcpdump
tcpdump: listening on ovnext0, link-type EN10MB (Ethernet), capture size 262144 bytes
^C
0 packets captured
0 packets received by filter
0 packets dropped by kernel
[root@pc-node-1 ~]# exit
[root@pc-node-1 ~]# ssh pc-node-2
Last login: Thu Feb 23 09:21:08 2023 from 10.5.32.51
[root@pc-node-2 ~]# ip netns exec ovnext bash
[root@pc-node-2 ~]# tcpdump -i ovnext0 host 223.5.5.5 -netvv
dropped privs to tcpdump
tcpdump: listening on ovnext0, link-type EN10MB (Ethernet), capture size 262144 bytes
^C
0 packets captured
0 packets received by filter
0 packets dropped by kernel
[root@pc-node-2 ~]# exit
[root@pc-node-2 ~]# logout
Connection to pc-node-2 closed.
[root@pc-node-1 ~]# ssh pc-node-3
Last login: Thu Feb 23 08:32:41 2023 from 10.5.32.51
[root@pc-node-3 ~]#  ip netns exec ovnext bash
[root@pc-node-3 ~]# tcpdump -i ovnext0 host 223.5.5.5 -netvv
dropped privs to tcpdump
tcpdump: listening on ovnext0, link-type EN10MB (Ethernet), capture size 262144 bytes
00:00:00:2d:f8:ce > 00:00:00:fd:b2:a4, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 63, id 57978, offset 0, flags [DF], proto ICMP (1), length 84)
    10.5.204.102 > 223.5.5.5: ICMP echo request, id 22, seq 71, length 64
00:00:00:fd:b2:a4 > dc:ef:80:5a:44:1a, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 62, id 57978, offset 0, flags [DF], proto ICMP (1), length 84)
    10.5.204.102 > 223.5.5.5: ICMP echo request, id 22, seq 71, length 64
^C
2 packets captured
2 packets received by filter
0 packets dropped by kernel
[root@pc-node-3 ~]#


```

## 3. Turn off bfd mode

In some scenarios, you may want to use a (centralized) single gateway directly out of the public network, which is the same as the default vpc enable_eip_snat usage pattern

``` bash
# cat 01-vpc-ecmp-enable-external-bfd.yml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc2
spec:
  namespaces:
  - vpc2
  enableExternal: true
  #enableBfd: true
  enableBfd: false

## set it false add apply

# k ko nbctl lr-route-list vpc2
IPv4 Routes
Route Table <main>:
                0.0.0.0/0              10.5.204.254 dst-ip

# After application the route will switch back to the normal default static route
# nbctl list bfd, the bfd session associated with lrp has been removed
# And the opposite side of the bfd session in ovnext ns is automatically removed
```
