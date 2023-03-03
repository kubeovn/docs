# ovn eip fip snat

``` mermaid
graph LR


pod-->vpc1-subnet-->vpc1-->snat-->lrp-->external-subnet-->gw-node-external-nic
```

pod基于snat出公网的大致流程，最后是经过网关节点的公网网卡。

``` mermaid
graph LR


pod-->vpc1-subnet-->vpc1-->fip-->lrp-->external-subnet-->local-node-external-nic
```

pod基于fip出公网的大致流程，最后可以基于本地节点的公网网卡出公网。

## 1. 部署

目前允许所有（默认以及自定义）vpc使用同一个provider vlan subnet 资源，类似neutron ovn模式，同时兼容之前**默认vpc可以使用enable_eip_snat**的场景。

执行install.sh 需要指定默认公网逻辑交换机。
该配置项的设计和使用主要考虑了如下因素：

- 基于该配置项可以对接到provider network，vlan，subnet的资源。
- 基于该配置项可以将默认vpc enable_eip_snat 功能对接到已有的vlan，subnet资源，同时支持公网ip的ipam。
- 如果仅使用默认vpc的enable_eip_snat模式, 且仅使用旧的基于pod annotaion的 eip fip snat，那么这个配置无需配置。
- 基于该配置可以不使用默认vpc enable_eip_snat 流程，仅通过对应到vlan，subnet流程，可以兼容仅自定义vpc使用eip snat的使用场景。

neutron ovn 模式也有一定的静态文件配置指定设计，目前来说，大致一致。

```bash
# 部署的时候你需要参考以上场景，根据实际情况，按需指定如下参数
# 1. kube-ovn-controller 启动参数需要配置：
          - --external-gateway-vlanid=204
          - --external-gateway-switch=external204
          
# 2. kube-ovn-cni 启动参数需要配置:
          - --external-gateway-switch=external204 

### 以上配置都和下面的公网网络配置vlan id 和资源名保持一致，目前仅支持指定一个underlay公网作为默认外部公网。
```

### 1.1 准备underlay公网网络

``` bash
# 准备provider-network， vlan， subnet
# cat 01-provider-network.yaml
apiVersion: kubeovn.io/v1
kind: ProviderNetwork
metadata:
  name: external204
spec:
  defaultInterface: vlan
# cat 02-vlan.yaml
apiVersion: kubeovn.io/v1
kind: Vlan
metadata:
  name: vlan204
spec:
  id: 204
  provider: external204
# cat 03-vlan-subnet.yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: external204
spec:
  protocol: IPv4
  cidrBlock: 10.5.204.0/24
  gateway: 10.5.204.254
  vlan: vlan204
  excludeIps:
  - 10.5.204.1..10.5.204.100
```

### 1.2 默认vpc启用eip_snat

``` bash
# 启用默认vpc和上述underlay公网provider subnet互联
cat 00-centralized-external-gw-no-ip.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-external-gw-config
  namespace: kube-system
data:
  enable-external-gw: "true"
  external-gw-nodes: "pc-node-1,pc-node-2,pc-node-3"
  type: "centralized" 
  external-gw-nic: "vlan" # 用于接入ovs公网网桥的网卡
  external-gw-addr: "10.5.204.254/24" # underlay物理网关的ip
```

目前该功能已支持可以不指定lrp ip和mac，已支持自动获取，创建lrp 类型的ovn eip资源。

如果指定了，则相当于指定ip创建lrp类型的ovn-eip。
当然也可以提前手动创建lrp类型的ovn eip。

### 1.3 自定义vpc启用eip snat fip功能

``` bash
# cat 00-ns.yml
apiVersion: v1
kind: Namespace
metadata:
  name: vpc1
  
# cat 01-vpc-ecmp-enable-external-bfd.yml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc1
spec:
  namespaces:
  - vpc1
  enableExternal: true
# vpc 启用 enableExternal 会自动创建lrp关联到上述指定的公网

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
  enableEcmp: true
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

# 这里子网和之前使用子网一样，该功能在subnet上没有新增属性，没有任何变更
```

以上模板应用后，应该可以看到如下资源存在

```bash
# k ko nbctl show vpc1
router 87ad06fd-71d5-4ff8-a1f0-54fa3bba1a7f (vpc1)
    port vpc1-vpc1-subnet1
        mac: "00:00:00:ED:8E:C7"
        networks: ["192.168.0.1/24"]
    port vpc1-external204
        mac: "00:00:00:EF:05:C7"
        networks: ["10.5.204.105/24"]
        gateway chassis: [7cedd14f-265b-42e5-ac17-e03e7a1f2342 276baccb-fe9c-4476-b41d-05872a94976d fd9f140c-c45d-43db-a6c0-0d4f8ea298dd]
    nat 21d853b0-f7b4-40bd-9a53-31d2e2745739
        external ip: "10.5.204.115"
        logical ip: "192.168.0.0/24"
        type: "snat"
```

``` bash
# k ko nbctl lr-route-list vpc1
IPv4 Routes
Route Table <main>:
                0.0.0.0/0              10.5.204.254 dst-ip
# 目前该路由已自动维护
```

## 2. ovn-eip

该功能和iptables-eip设计和使用方式基本一致，ovn-eip目前有四种type

- lrp: 用于vpc和公网相连的资源
- fip: 用于ovn nat dnat_and_snat 资源
- snat: 用于snat，支持一对一到pod ip，以及对应到subnet cidr
- node-ext-gw: 用于ovn 基于bfd的ecmp路由场景

``` bash
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  externalSubnet: external204
  type: fip
  
# 动态分配一个eip资源，该资源预留用于fip场景
```

### 3.1 ovn-fip 为pod绑定一个fip

``` bash
# k get po -o wide -n vpc1 vpc-1-busybox01
NAME              READY   STATUS    RESTARTS   AGE     IP            NODE
vpc-1-busybox01   1/1     Running   0          3d15h   192.168.0.2   pc-node-2

# k get ip vpc-1-busybox01.vpc1
NAME                   V4IP          V6IP   MAC                 NODE        SUBNET
vpc-1-busybox01.vpc1   192.168.0.2          00:00:00:0A:DD:27   pc-node-2   vpc1-subnet1

---

kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  externalSubnet: external204
  type: fip

---
kind: OvnFip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  ovnEip: eip-static
  ipName: vpc-1-busybox01.vpc1  # 注意这里是ip crd的名字，具有唯一性
```

``` bash
# k get ofip
NAME          VPC    V4EIP          V4IP          READY   IPTYPE   IPNAME
eip-for-vip   vpc1   10.5.204.106   192.168.0.3   true    vip      test-fip-vip
eip-static    vpc1   10.5.204.101   192.168.0.2   true             vpc-1-busybox01.vpc1
# k get ofip eip-static
NAME         VPC    V4EIP          V4IP          READY   IPTYPE   IPNAME
eip-static   vpc1   10.5.204.101   192.168.0.2   true             vpc-1-busybox01.vpc1

[root@pc-node-1 03-cust-vpc]# ping 10.5.204.101
PING 10.5.204.101 (10.5.204.101) 56(84) bytes of data.
64 bytes from 10.5.204.101: icmp_seq=2 ttl=62 time=1.21 ms
64 bytes from 10.5.204.101: icmp_seq=3 ttl=62 time=0.624 ms
64 bytes from 10.5.204.101: icmp_seq=4 ttl=62 time=0.368 ms
^C
--- 10.5.204.101 ping statistics ---
4 packets transmitted, 3 received, 25% packet loss, time 3049ms
rtt min/avg/max/mdev = 0.368/0.734/1.210/0.352 ms
[root@pc-node-1 03-cust-vpc]#

# 可以看到在node ping 默认vpc下的pod的公网ip 是能通的
```

``` bash
# 该公网ip能通的关键资源主要包括以下部分
# k ko nbctl show vpc1
router 87ad06fd-71d5-4ff8-a1f0-54fa3bba1a7f (vpc1)
    port vpc1-vpc1-subnet1
        mac: "00:00:00:ED:8E:C7"
        networks: ["192.168.0.1/24"]
    port vpc1-external204
        mac: "00:00:00:EF:05:C7"
        networks: ["10.5.204.105/24"]
        gateway chassis: [7cedd14f-265b-42e5-ac17-e03e7a1f2342 276baccb-fe9c-4476-b41d-05872a94976d fd9f140c-c45d-43db-a6c0-0d4f8ea298dd]
    nat 813523e7-c68c-408f-bd8c-cba30cb2e4f4
        external ip: "10.5.204.101"
        logical ip: "192.168.0.2"
        type: "dnat_and_snat"
```

### 3.2 ovn-fip 为vip绑定一个fip

为了便于一些vip场景的使用，比如kubevirt虚拟机内部我可能会使用一些vip提供给keepalived，kube-vip等场景来使用，同时支持公网访问。

那么可以基于fip绑定vpc内部的vip的方式来提供vip的公网能力。

``` bash
# 先创建vip，eip，再将eip绑定到vip
# cat vip.yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: test-fip-vip
spec:
  subnet: vpc1-subnet1

# cat 04-fip.yaml
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-for-vip
spec:
  externalSubnet: external204
  type: fip

---
kind: OvnFip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-for-vip
spec:
  ovnEip: eip-for-vip
  ipType: vip         # 默认情况下fip是面向pod ip的，这里需要标注指定对接到vip资源
  ipName: test-fip-vip
```

``` bash
# k get ofip
NAME          VPC    V4EIP          V4IP          READY   IPTYPE   IPNAME
eip-for-vip   vpc1   10.5.204.106   192.168.0.3   true    vip      test-fip-vip


[root@pc-node-1 fip-vip]# ping  10.5.204.106
PING 10.5.204.106 (10.5.204.106) 56(84) bytes of data.
64 bytes from 10.5.204.106: icmp_seq=1 ttl=62 time=0.694 ms
64 bytes from 10.5.204.106: icmp_seq=2 ttl=62 time=0.436 ms

# 在node上是ping得通的


# pod内部的ip使用方式大致就是如下这种情况

[root@pc-node-1 fip-vip]# k -n vpc1 exec -it vpc-1-busybox03 -- bash
[root@vpc-1-busybox03 /]#
[root@vpc-1-busybox03 /]#
[root@vpc-1-busybox03 /]# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
1568: eth0@if1569: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 00:00:00:56:40:e5 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 192.168.0.5/24 brd 192.168.0.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet 192.168.0.3/24 scope global secondary eth0  # 可以看到vip的配置
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe56:40e5/64 scope link
       valid_lft forever preferred_lft forever

[root@vpc-1-busybox03 /]# tcpdump -i eth0 host  192.168.0.3 -netvv
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
00:00:00:ed:8e:c7 > 00:00:00:56:40:e5, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 62, id 44830, offset 0, flags [DF], proto ICMP (1), length 84)
    10.5.32.51 > 192.168.0.3: ICMP echo request, id 177, seq 1, length 64
00:00:00:56:40:e5 > 00:00:00:ed:8e:c7, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 64, id 43962, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.0.3 > 10.5.32.51: ICMP echo reply, id 177, seq 1, length 64

# pod内部可以抓到fip相关的icmp包
```

## 4. ovn-snat

### 4.1 ovn-snat 对应一个subnet的cidr

该功能和iptables-snat设计和使用方式基本一致

```bash
# cat 03-subnet-snat.yaml
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-subnet-in-vpc
spec:
  externalSubnet: external204
  type: snat

---
kind: OvnSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-subnet-in-vpc
spec:
  ovnEip: snat-for-subnet-in-vpc
  vpcSubnet: vpc1-subnet1 # eip 对应整个网段
```

### 4.2 ovn-fip 对应到一个pod ip

该功能和iptables-fip 设计和使用方式基本一致

```bash
# cat 03-pod-snat.yaml
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-pod-vpc-ip
spec:
  externalSubnet: external204
  type: snat

---
kind: OvnSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat01
spec:
  ovnEip: snat-for-pod-vpc-ip
  ipName: vpc-1-busybox02.vpc1 # eip 对应单个pod ip

```

以上资源创建后，可以看到snat公网功能依赖的如下资源。

``` bash
# kubectl ko nbctl show vpc1
router 87ad06fd-71d5-4ff8-a1f0-54fa3bba1a7f (vpc1)
    port vpc1-vpc1-subnet1
        mac: "00:00:00:ED:8E:C7"
        networks: ["192.168.0.1/24"]
    port vpc1-external204
        mac: "00:00:00:EF:05:C7"
        networks: ["10.5.204.105/24"]
        gateway chassis: [7cedd14f-265b-42e5-ac17-e03e7a1f2342 276baccb-fe9c-4476-b41d-05872a94976d fd9f140c-c45d-43db-a6c0-0d4f8ea298dd]
    nat 21d853b0-f7b4-40bd-9a53-31d2e2745739
        external ip: "10.5.204.115"
        logical ip: "192.168.0.0/24"
        type: "snat"
    nat da77a11f-c523-439c-b1d1-72c664196a0f
        external ip: "10.5.204.116"
        logical ip: "192.168.0.4"
        type: "snat"
```

``` bash
[root@pc-node-1 03-cust-vpc]# k get po -A -o wide  | grep busy
vpc1            vpc-1-busybox01                                 1/1     Running   0                3d15h   192.168.0.2   pc-node-2   <none>           <none>
vpc1            vpc-1-busybox02                                 1/1     Running   0                17h     192.168.0.4   pc-node-1   <none>           <none>
vpc1            vpc-1-busybox03                                 1/1     Running   0                17h     192.168.0.5   pc-node-1   <none>           <none>
vpc1            vpc-1-busybox04                                 1/1     Running   0                17h     192.168.0.6   pc-node-3   <none>           <none>
vpc1            vpc-1-busybox05                                 1/1     Running   0                17h     192.168.0.7   pc-node-1   <none>           <none>

# k exec -it -n vpc1            vpc-1-busybox04   bash
kubectl exec [POD] [COMMAND] is DEPRECATED and will be removed in a future version. Use kubectl exec [POD] -- [COMMAND] instead.
[root@vpc-1-busybox04 /]#
[root@vpc-1-busybox04 /]#
[root@vpc-1-busybox04 /]# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
17095: eth0@if17096: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 00:00:00:76:94:55 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 192.168.0.6/24 brd 192.168.0.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe76:9455/64 scope link
       valid_lft forever preferred_lft forever
[root@vpc-1-busybox04 /]# ping 223.5.5.5
PING 223.5.5.5 (223.5.5.5) 56(84) bytes of data.
64 bytes from 223.5.5.5: icmp_seq=1 ttl=114 time=22.2 ms
64 bytes from 223.5.5.5: icmp_seq=2 ttl=114 time=21.8 ms

[root@pc-node-1 03-cust-vpc]# k exec -it -n vpc1            vpc-1-busybox02   bash
kubectl exec [POD] [COMMAND] is DEPRECATED and will be removed in a future version. Use kubectl exec [POD] -- [COMMAND] instead.
[root@vpc-1-busybox02 /]#
[root@vpc-1-busybox02 /]#
[root@vpc-1-busybox02 /]#
[root@vpc-1-busybox02 /]# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
1566: eth0@if1567: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 00:00:00:0b:e9:d0 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 192.168.0.4/24 brd 192.168.0.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe0b:e9d0/64 scope link
       valid_lft forever preferred_lft forever
[root@vpc-1-busybox02 /]# ping 223.5.5.5
PING 223.5.5.5 (223.5.5.5) 56(84) bytes of data.
64 bytes from 223.5.5.5: icmp_seq=2 ttl=114 time=22.7 ms
64 bytes from 223.5.5.5: icmp_seq=3 ttl=114 time=22.6 ms
64 bytes from 223.5.5.5: icmp_seq=4 ttl=114 time=22.1 ms
^C
--- 223.5.5.5 ping statistics ---
4 packets transmitted, 3 received, 25% packet loss, time 3064ms
rtt min/avg/max/mdev = 22.126/22.518/22.741/0.278 ms

# 可以看到两个pod可以分别基于这两种snat资源上外网
```
