# ovn eip fip snat

``` mermaid
graph LR


pod-->vpc1-subnet-->vpc1-->snat-->lrp-->external-subnet-->gw-node-external-nic
```

The pod access the public network based on the snat

``` mermaid
graph LR


pod-->vpc1-subnet-->vpc1-->fip-->lrp-->external-subnet-->local-node-external-nic
```

The pod access the public network based on the fip

## 1. Deployment

Currently allows all vpcs to share the same provider vlan subnet resources, similar to neutron ovn mode.
Also compatible with previous scenarios **default vpc enable_eip_snat**

Executing install.sh requires specifying the default public logical switch.

The design and use of this configuration item takes into account the following factors：

- Based on this configuration item can be docked to the provider network, vlan, subnet resources.
- Based on this configuration item, the default vpc enable_eip_snat function can be docked to the existing vlan, subnet resources, while supporting the ipam
- If only the default vpc's enable_eip_snat mode is used with the old pod annotaion based eip fip snat, then the following configuration is not required.
- Based on this configuration you can not use the default vpc enable_eip_snat process, only by corresponding to vlan, subnet process, can be compatible with only custom vpc use eip snat usage scenarios.

The neutron ovn mode also has a certain static file configuration designation that is, for now, generally consistent.

```bash
# When deploying you need to refer to the above scenario and specify the following parameters as needed according to the actual situation
# 1. kube-ovn-controller Startup parameters to be configured：
          - --external-gateway-vlanid=204
          - --external-gateway-switch=external204
          
# 2. kube-ovn-cni Startup parameters to be configured:
          - --external-gateway-switch=external204 

# The above configuration is consistent with the following public network configuration vlan id and resource name, 
# currently only support to specify one underlay public network as the default external public network.
```

### 1.1 Create the underlay public network

``` bash
# provider-network， vlan， subnet
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

### 1.2 Default vpc enable eip_snat

``` bash
# Enable the default vpc and the above underlay public provider subnet interconnection
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
  external-gw-nic: "vlan"
  external-gw-addr: "10.5.204.254/24"
```

This feature currently supports the ability to create lrp type ovn eip resources without specifying the lrp ip and mac, which is already supported for automatic acquisition.
If specified, it is equivalent to specifying the ip to create an ovn-eip of type lrp.
Of course, you can also manually create the lrp type ovn eip in advance.

### 1.3 Custom vpc enable eip snat fip function

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
# vpc enableExternal will automatically create an lrp association to the public network specified above

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

```

After the above template is applied, you should see the following resources exist

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
# The route currently supports automatic maintenance
```

## 2. ovn-eip

This feature is basically the same as iptables-eip design and usage, ovn-eip currently has four types

- lrp: Resources for vpc and public network connection
- fip: For ovn nat dnat_and_snat resources
- snat: For snat, supporting one-to-one to pod, and one-to-one throughout the subnet cidr
- node-ext-gw: For ovn bfd-based ecmp routing scenarios

``` bash
---
kind: OvnEip
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  externalSubnet: external204
  type: fip
  
# Dynamically allocate an eip resource that is reserved for fip scenarios
```

### 2.1 Create an fip for pod

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
  ipName: vpc-1-busybox01.vpc1  # the name of the ip crd, which is unique
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

# pod <--> node ping is working
```

``` bash
# The key resources that this public ip can pass include the following ovn nb resources

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

### 2.2 Create an fip for vip

In order to facilitate the use of some vip scenarios, such as inside kubevirt VM, keepalived use vip, kube-vip use vip, etc. the vip need public network access.

``` bash
# First create vip, eip, then bind eip to vip
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
  ipType: vip         # By default fip is for pod ip, here you need to specify the docking to vip resources
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

# node <--> pod fip is working

# The way ip is used inside the pod is roughly as follows

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
    inet 192.168.0.3/24 scope global secondary eth0  # vip here
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe56:40e5/64 scope link
       valid_lft forever preferred_lft forever

[root@vpc-1-busybox03 /]# tcpdump -i eth0 host  192.168.0.3 -netvv
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
00:00:00:ed:8e:c7 > 00:00:00:56:40:e5, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 62, id 44830, offset 0, flags [DF], proto ICMP (1), length 84)
    10.5.32.51 > 192.168.0.3: ICMP echo request, id 177, seq 1, length 64
00:00:00:56:40:e5 > 00:00:00:ed:8e:c7, ethertype IPv4 (0x0800), length 98: (tos 0x0, ttl 64, id 43962, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.0.3 > 10.5.32.51: ICMP echo reply, id 177, seq 1, length 64

# pod internal can catch fip related icmp packets

```

## 3. ovn-snat

### 3.1 ovn-snat corresponds to the CIDR of a subnet

This feature is designed and used in much the same way as iptables-snat

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
  vpcSubnet: vpc1-subnet1 # eip corresponds to the entire network segment
```

### 3.2 ovn-fip corresponds to a pod IP

This feature is designed and used in much the same way as iptables-fip

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
  ipName: vpc-1-busybox02.vpc1 # eip corresponds to a single pod ip

```

After the above resources are created, you can see the following resources that the snat public network feature depends on.

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

# the two pods can access the external network based on these two type snat resources respectively
```
