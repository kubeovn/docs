# OVN EIP FIP SNAT DNAT 支持

支持任意 VPC OVN NAT 功能使用任意多个的 `provider-network vlan (external) subnet` 资源，该功能独立于[默认 VPC EIP/SNAT](../guide/eip-snat.md)功能。

## 两种互相独立的使用方式

- `默认外部网络`：如果只需要用一个外部网络，需要在 `kube-ovn-controller` 和 `kube-ovn-cni` 中指定启动参数， 然后通过 `ovn-external-gw-config` 或者 `VPC spec enableExternal` 属性使用这个默认外部子网。
- `CRD`：创建 `provider-network` `vlan` `subnet` 资源，然后通过 `VPC spec extraExternalSubnets` 使用任意外部子网，然后通过 `ovn-eip，ovn-dnat，ovn-fip，ovn-snat` 等 CRD 来使用。

``` mermaid

graph LR

pod-->subnet-->vpc-->lrp--bind-->gw-chassis-->snat-->lsp-->external-subnet
lrp-.-peer-.-lsp

```

Pod 基于 SNAT 出公网的大致流程，最后是经过网关节点的公网网卡。
Pod 基于 Fip 使用集中式网关，路径也类似。

``` mermaid

graph LR


pod-->subnet-->vpc-->lrp--bind-->local-chassis-->snat-->lsp-->external-subnet


lrp-.-peer-.-lsp

```

Pod 基于分布式网关 FIP (dnat_and_snat) 出公网的大致流程，最后可以基于本地节点的公网网卡出公网。

该功能所支持的 CRD 在使用上将和 iptables nat gw 公网方案保持基本一致。

- ovn eip: 用于公网 ip 占位，从 underlay provider network vlan subnet 中分配
- ovn fip： 一对一 dnat snat，为 VPC 内的 ip 或者 vip 提供公网直接访问能力
- ovn snat：整个子网或者单个 VPC 内 ip 可以基于 snat 访问公网
- ovn dnat：基于 router lb 实现, 基于公网 ip + 端口 直接访问 VPC 内的 一组 endpoints

## 1. 部署

如果用户选择 `默认外部网络` 方式使用：

类似 OpenStack Neutron ovn，服务启动配置中需要指定 provider network 相关的配置，下述的启动参数也是为了兼容 VPC EIP/SNAT 的实现。

如果实际使用中没有 vlan（使用 vlan 0），那么无需配置 vlan id。

```bash
# 部署的时候你需要参考以上场景，根据实际情况，按需指定如下参数
# 1. kube-ovn-controller 启动参数需要配置：
          - --external-gateway-vlanid=204
          - --external-gateway-switch=external204

# 2. kube-ovn-cni 启动参数需要配置:
          - --external-gateway-switch=external204

### 以上配置都和下面的公网网络配置 vlan id 和资源名保持一致，目前仅支持指定一个 underlay 公网作为默认外部公网。
```

该配置项的设计和使用主要考虑了如下因素：

- 基于该配置项可以对接到 provider network，vlan，subnet 的资源。
- 基于该配置项可以将默认 VPC enable_eip_snat 功能对接到已有的 vlan，subnet 资源，同时支持公网 ip 的 ipam。
- 如果仅使用默认 VPC 的 enable_eip_snat 模式, 且仅使用旧的基于 pod annotation 的 fip snat，那么这个配置无需配置。
- 基于该配置可以不使用默认 VPC enable_eip_snat 流程，仅通过对应到 vlan，subnet 流程，可以兼容仅自定义 VPC 使用 eip snat 的使用场景。

### 1.1 准备 underlay 公网网络

``` bash
# 准备 provider-network， vlan， subnet
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

### 1.2 默认 VPC 启用 eip_snat

``` bash
# 启用默认 VPC 和上述 underlay 公网 provider subnet 互联
# cat 00-centralized-external-gw-no-ip.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: ovn-external-gw-config
  namespace: kube-system
data:
  enable-external-gw: "true"
  external-gw-nodes: "pc-node-1,pc-node-2,pc-node-3"
  type: "centralized"
  external-gw-nic: "vlan" # 用于接入 ovs 公网网桥的网卡
  external-gw-addr: "10.5.204.254/24" # underlay 物理网关的 ip
```

目前该功能已支持可以不指定 logical router port (lrp) ip 和 mac，已支持从 underlay 公网中自动分配，创建 lrp 类型的 ovn eip 资源。

如果指定了，则相当于以指定 ip 的方式创建了一个 lrp 类型的 ovn-eip。
当然也可以提前手动创建 lrp 类型的 ovn eip。

### 1.3 自定义 VPC 启用 eip snat fip 功能

集群一般需要多个网关 node 来实现高可用，配置如下：

```bash
# 首先通过添加标签指定 external-gw-nodes
kubectl label nodes pc-node-1 pc-node-2 pc-node-3 ovn.kubernetes.io/external-gw=true
```

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
# VPC 启用 enableExternal 会自动创建 lrp 关联到上述指定的公网

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

# 这里子网和之前使用子网一样，该功能在 subnet 上没有新增属性，没有任何变更
```

以上模板应用后，应该可以看到如下资源存在

```bash
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
```

``` bash
# kubectl ko nbctl lr-route-list vpc1

IPv4 Routes
Route Table <main>:
                0.0.0.0/0              10.5.204.254 dst-ip
# 目前该路由已自动维护
```

### 1.4 使用额外的公网网络

#### 1.4.1 准备额外 underlay 公网网络

额外的公网网络功能在启动默认 eip snat fip 功能后才会启用，若只有 1 个公网网卡，请使用默认 eip snat fip 功能

```yaml
# 准备 provider-network， vlan， subnet
# cat 01-extra-provider-network.yaml
apiVersion: kubeovn.io/v1
kind: ProviderNetwork
metadata:
  name: extra
spec:
  defaultInterface: vlan
# cat 02-extra-vlan.yaml
apiVersion: kubeovn.io/v1
kind: Vlan
metadata:
  name: vlan0
spec:
  id: 0
  provider: extra
# cat 03-extra-vlan-subnet.yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: extra
spec:
  protocol: IPv4
  cidrBlock: 10.10.204.0/24
  gateway: 10.10.204.254
  vlan: vlan0
  excludeIps:
  - 10.10.204.1..10.10.204.100
```

#### 1.4.2 自定义 VPC 配置

```yaml
apiVersion: kubeovn.io/v1
kind: Vpc
metadata:
  name: vpc1
spec:
  namespaces:
  - vpc1
  enableExternal: true  # 开启 enableExternal 后 VPC 会自动连接外部网络，一般是名为 external 的 ls
  extraExternalSubnets: # 配置 extraExternalSubnets 支持连接任意多个公网网络
  - extra
```

以上模板应用后，应该可以看到如下资源存在

```bash
# kubectl ko nbctl show vpc1
router 87ad06fd-71d5-4ff8-a1f0-54fa3bba1a7f (vpc1)
    port vpc1-vpc1-subnet1
        mac: "00:00:00:ED:8E:C7"
        networks: ["192.168.0.1/24"]
    port vpc1-external204
        mac: "00:00:00:EF:05:C7"
        networks: ["10.5.204.105/24"]
        gateway chassis: [7cedd14f-265b-42e5-ac17-e03e7a1f2342 276baccb-fe9c-4476-b41d-05872a94976d fd9f140c-c45d-43db-a6c0-0d4f8ea298dd]
    port vpc1-extra
        mac: "00:00:00:EF:6A:C7"
        networks: ["10.10.204.105/24"]
        gateway chassis: [7cedd14f-265b-42e5-ac17-e03e7a1f2342 276baccb-fe9c-4476-b41d-05872a94976d fd9f140c-c45d-43db-a6c0-0d4f8ea298dd]
```

## 2. ovn-eip

该功能和 iptables-eip 设计和使用方式基本一致，ovn-eip 目前有三种 type

- nat: 是指 ovn dnat，fip, snat 这三种 nat 资源类型
- lrp: 软路由基于该端口和 underlay 公网互联，该 lrp 端口的 ip 可以被其他 dnat snat 复用
- lsp: 用于 ovn 基于 bfd 的 ecmp 静态路由场景，在网关节点上提供一个 ovs internal port 作为 ecmp 路由的下一跳

``` bash
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  externalSubnet: external204
  type: nat

# 动态分配一个 eip 资源，该资源预留用于 fip 场景
```

externalSubnet 字段可不进行配置，若未配置则会使用默认公网网络，在上述配置中默认公网网络为 external204。

若要使用额外公网网络，则需要通过 externalSubnet 显式指定需要扩展使用的公网网络，在上述配置中扩展公网网络为 extra。

### 2.1 ovn-fip 为 pod 绑定一个 fip

``` bash
# kubectl get po -o wide -n vpc1 vpc-1-busybox01
NAME              READY   STATUS    RESTARTS   AGE     IP            NODE
vpc-1-busybox01   1/1     Running   0          3d15h   192.168.0.2   pc-node-2

# kubectl get ip vpc-1-busybox01.vpc1
NAME                   V4IP          V6IP   MAC                 NODE        SUBNET
vpc-1-busybox01.vpc1   192.168.0.2          00:00:00:0A:DD:27   pc-node-2   vpc1-subnet1

---

kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  externalSubnet: external204
  type: nat

---
kind: OvnFip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  ovnEip: eip-static
  ipName: vpc-1-busybox01.vpc1  # 注意这里是 ip crd 的名字，具有唯一性
  type: "centralized"           # centralized 或者 distributed

--
# 或者通过传统指定 VPC 以及 内网 ip 的方式

kind: OvnFip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  ovnEip: eip-static
  vpc: vpc1
  v4Ip: 192.168.0.2
  type: "centralized"           # centralized 或者 distributed

```

``` bash
# kubectl get ofip
NAME          VPC    V4EIP          V4IP          READY   IPTYPE   IPNAME
eip-for-vip   vpc1   10.5.204.106   192.168.0.3   true    vip      test-fip-vip
eip-static    vpc1   10.5.204.101   192.168.0.2   true             vpc-1-busybox01.vpc1
# kubectl get ofip eip-static
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

# 可以看到在 node ping 默认 VPC 下的 pod 的公网 ip 是能通的
```

``` bash
# 该公网 ip 能通的关键资源主要包括以下部分
# kubectl ko nbctl show vpc1
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

### 2.2 ovn-fip 为 vip 绑定一个 fip

为了便于一些 vip 场景的使用，比如 kubevirt 虚拟机内部我可能会使用一些 vip 提供给 keepalived，kube-vip 等场景来使用，同时支持公网访问。

那么可以基于 fip 绑定 VPC 内部的 vip 的方式来提供 vip 的公网能力。

``` bash
# 先创建 vip，eip，再将 eip 绑定到 vip
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
  type: nat

---
kind: OvnFip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-for-vip
spec:
  ovnEip: eip-for-vip
  ipType: vip         # 默认情况下 fip 是面向 pod ip 的，这里需要标注指定对接到 vip 资源
  ipName: test-fip-vip

---
# 或者通过传统指定 VPC 以及 内网 ip 的方式

kind: OvnFip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-for-vip
spec:
  ovnEip: eip-for-vip
  ipType: vip         # 默认情况下 fip 是面向 pod ip 的，这里需要标注指定对接到 vip 资源
  vpc: vpc1
  v4Ip: 192.168.0.3

```

``` bash
# kubectl get ofip
NAME          VPC    V4EIP          V4IP          READY   IPTYPE   IPNAME
eip-for-vip   vpc1   10.5.204.106   192.168.0.3   true    vip      test-fip-vip


[root@pc-node-1 fip-vip]# ping  10.5.204.106
PING 10.5.204.106 (10.5.204.106) 56(84) bytes of data.
64 bytes from 10.5.204.106: icmp_seq=1 ttl=62 time=0.694 ms
64 bytes from 10.5.204.106: icmp_seq=2 ttl=62 time=0.436 ms

# 在 node 上是 ping 得通的


# pod 内部的 ip 使用方式大致就是如下这种情况

[root@pc-node-1 fip-vip]# kubectl -n vpc1 exec -it vpc-1-busybox03 -- bash
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
    inet 192.168.0.3/24 scope global secondary eth0  # 可以看到 vip 的配置
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe56:40e5/64 scope link
       valid_lft forever preferred_lft forever

[root@vpc-1-busybox03 /]# tcpdump -i eth0 host  192.168.0.3 -netvv
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
00:00:00:ed:8e:c7 > 00:00:00:56:40:e5, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 62, id 44830, offset 0, flags [DF], proto ICMP (1), length 84)
    10.5.32.51 > 192.168.0.3: ICMP echo request, id 177, seq 1, length 64
00:00:00:56:40:e5 > 00:00:00:ed:8e:c7, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 64, id 43962, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.0.3 > 10.5.32.51: ICMP echo reply, id 177, seq 1, length 64

# pod 内部可以抓到 fip 相关的 icmp 包
```

## 3. ovn-snat

### 3.1 ovn-snat 对应一个 subnet 的 cidr

该功能和 iptables-snat 设计和使用方式基本一致

```bash
# cat 03-subnet-snat.yaml

---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-subnet-in-vpc
spec:
  externalSubnet: external204
  type: nat

---
kind: OvnSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-subnet-in-vpc
spec:
  ovnEip: snat-for-subnet-in-vpc
  vpcSubnet: vpc1-subnet1 # eip 对应整个网段

---
# 或者通过传统指定 VPC 以及 内网 subnet cidr 的方式

kind: OvnSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-subnet-in-vpc
spec:
  ovnEip: snat-for-subnet-in-vpc
  vpc: vpc1
  v4IpCidr: 192.168.0.0/24 # 该字段可以是 cidr 也可以是 ip

```

若要使用额外公网网络，则需要通过 externalSubnet 显式指定需要扩展使用的公网网络，在上述配置中扩展公网网络为 extra。

### 3.2 ovn-snat 对应到一个 pod ip

该功能和 iptables-snat 设计和使用方式基本一致

```bash
# cat 03-pod-snat.yaml

---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-pod-vpc-ip
spec:
  externalSubnet: external204
  type: nat

---
kind: OvnSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat01
spec:
  ovnEip: snat-for-pod-vpc-ip
  ipName: vpc-1-busybox02.vpc1 # eip 对应单个 pod ip

---
# 或者通过传统指定 VPC 以及 内网 ip 的方式

kind: OvnSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat-for-subnet-in-vpc
spec:
  ovnEip: snat-for-subnet-in-vpc
  vpc: vpc1
  v4IpCidr: 192.168.0.4

```

若要使用额外公网网络，则需要通过 externalSubnet 显式指定需要扩展使用的公网网络，在上述配置中扩展公网网络为 extra。

以上资源创建后，可以看到 snat 公网功能依赖的如下资源。

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
[root@pc-node-1 03-cust-vpc]# kubectl get po -A -o wide  | grep busy
vpc1            vpc-1-busybox01                                 1/1     Running   0                3d15h   192.168.0.2   pc-node-2   <none>           <none>
vpc1            vpc-1-busybox02                                 1/1     Running   0                17h     192.168.0.4   pc-node-1   <none>           <none>
vpc1            vpc-1-busybox03                                 1/1     Running   0                17h     192.168.0.5   pc-node-1   <none>           <none>
vpc1            vpc-1-busybox04                                 1/1     Running   0                17h     192.168.0.6   pc-node-3   <none>           <none>
vpc1            vpc-1-busybox05                                 1/1     Running   0                17h     192.168.0.7   pc-node-1   <none>           <none>

# kubectl exec -it -n vpc1            vpc-1-busybox04   bash
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

[root@pc-node-1 03-cust-vpc]# kubectl exec -it -n vpc1            vpc-1-busybox02   bash
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

# 可以看到两个 pod 可以分别基于这两种 snat 资源上外网
```

## 4. ovn-dnat

### 4.1 ovn-dnat 为 pod 绑定一个 dnat

```yaml

kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-dnat
spec:
  externalSubnet: underlay

---
kind: OvnDnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: eip-dnat
spec:
  ovnEip: eip-dnat
  ipName: vpc-1-busybox01.vpc1 # 注意这里是 pod ip crd 的名字，具有唯一性
  protocol: tcp
  internalPort: "22"
  externalPort: "22"


---
# 或者通过传统指定 VPC 以及 内网 ip 的方式

kind: OvnDnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: eip-dnat
spec:
  ovnEip: eip-dnat
  protocol: tcp
  internalPort: "22"
  externalPort: "22"
  vpc: vpc1
  v4Ip: 192.168.0.3

```

若要使用额外公网网络，则需要通过 externalSubnet 显式指定需要扩展使用的公网网络，在上述配置中扩展公网网络为 extra。

OvnDnatRule 的配置与 IptablesDnatRule 类似

```bash
# kubectl get oeip eip-dnat
NAME       V4IP        V6IP   MAC                 TYPE   READY
eip-dnat   10.5.49.4          00:00:00:4D:CE:49   dnat   true

# kubectl get odnat
NAME                   EIP                    PROTOCOL   V4EIP        V4IP           INTERNALPORT   EXTERNALPORT   IPNAME                                READY
eip-dnat               eip-dnat               tcp        10.5.49.4    192.168.0.3    22             22             vpc-1-busybox01.vpc1                  true

```

### 4.2 ovn-dnat 为 vip 绑定一个 dnat

```yaml

kind: OvnDnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: eip-dnat
spec:
  ipType: vip  # 默认情况下 dnat 是面向 pod ip 的，这里需要标注指定对接到 vip 资源
  ovnEip: eip-dnat
  ipName: test-dnat-vip
  protocol: tcp
  internalPort: "22"
  externalPort: "22"

---
# 或者通过传统指定 VPC 以及 内网 ip 的方式

kind: OvnDnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: eip-dnat
spec:
  ipType: vip  # 默认情况下 dnat 是面向 pod ip 的，这里需要标注指定对接到 vip 资源
  ovnEip: eip-dnat
  ipName: test-dnat-vip
  protocol: tcp
  internalPort: "22"
  externalPort: "22"
  vpc: vpc1
  v4Ip: 192.168.0.4

```

OvnDnatRule 的配置与 IptablesDnatRule 类似

```bash
# kubectl get vip test-dnat-vip
NAME            V4IP          PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET         READY
test-dnat-vip   192.168.0.4           00:00:00:D0:C0:B5                         vpc1-subnet1   true

# kubectl get oeip eip-dnat
NAME       V4IP        V6IP   MAC                 TYPE   READY
eip-dnat   10.5.49.4          00:00:00:4D:CE:49   dnat   true

# kubectl get odnat eip-dnat
NAME       EIP        PROTOCOL   V4EIP       V4IP          INTERNALPORT   EXTERNALPORT   IPNAME          READY
eip-dnat   eip-dnat   tcp        10.5.49.4   192.168.0.4   22             22             test-dnat-vip   true

```
