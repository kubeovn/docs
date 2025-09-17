# VIP reserved IP

VIP Virtual IP addresses are reserved for IP addresses. The reason for the design of VIP is that the IP and POD of kube-ovn are directly related in naming, so the function of reserving IP can not be realized directly based on IP. At the beginning of the design, VIP refers to the function of Openstack neutron Allowed-Address-Pairs(AAP), which can be used for Openstack octavia load balancer projects. It can also be used to provide in-machine application (POD) IP, as seen in the aliyun terway project. In addition, because neutron has the function of reserving IP, VIP has been extended to a certain extent, so that VIP can be directly used to reserve IP for POD, but this design will lead to the function of VIP and IP become blurred, which is not an elegant way to achieve, so it is not recommended to use in production. In addition, since the Switch LB of OVN can provide a function of using the internal IP address of the subnet as the front-end VIP of the LB, the scenario of using the OVN Switch LB Rule in the subnet for the VIP is extended.
In short, there are only three use cases for VIP design at present:

- Allowed-Address-Pairs VIP
- Switch LB rule VIP
- Pod uses VIP to fix IP

## 1. Allowed-Address-Pairs VIP

In this scenario, we want to dynamically reserve a part of the IP but not allocate it to Pods but to other infrastructure enables, such as:

- Kubernetes nesting scenarios In which the upper-layer Kubernetes uses the Underlay network, the underlying Subnet addresses are used.
- LB or other network infrastructure needs to use an IP within a Subnet, but does not have a separate Pod.

In addition, VIP can reserve IP for Allowed-Address-Pairs to support the scenario in which a single NIC is configured with multiple IP addresses, for example:

- Keepalived can help with fast failover and flexible load balancing architecture by configuring additional IP address pairs

### 1.1 Automatically assign addresses to VIP

If you just want to reserve a number of IP addresses without requiring the IP address itself, you can use the following yaml to create:

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-dynamic-01
spec:
  subnet: ovn-default
  type: ""

```

- `subnet`: The IP address is reserved from the Subnet.
- `type`: Currently, two types of ip addresses are supported. If the value is empty, it indicates that the ip address is used only for ipam ip addresses. switch_lb_vip indicates that the IP address is used only for switch lb.

Query the VIP after it is created:

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
vip-dynamic-01   10.16.0.12           00:00:00:F0:DB:25                         ovn-default   true
```

It can be seen that the VIP is assigned an IP address of '10.16.0.12', which can be used by other network infrastructures later.

### 1.2 Use fixed address VIP

If there is a need for the reserved VIP IP address, the following yaml can be used for fixed allocation:

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: static-vip01
spec:
  subnet: ovn-default 
  v4ip: "10.16.0.121"
```

- `subnet`: The IP address is reserved from the Subnet.
- `v4ip`: Fixed assigned IP address, which must be within the CIDR range of 'subnet'.

Query the VIP after it is created:

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
static-vip01   10.16.0.121           00:00:00:F0:DB:26                         ovn-default   true

```

### 1.3 Pod Uses VIP to enable AAP

Pod can use annotation to specify VIP to enable AAP function. labels must meet the condition of node selector in VIP.

Pod annotation supports specifying multiple VIPs. The configuration format is: `ovn.kubernetes.io/aaps: vip-aap,vip-aap2,vip-aap3`

AAP support [multi nic](./multi-nic.en.md), if a Pod is configured with multiple nics, AAP will configure the Port corresponding to the same subnet of the Pod and VIP.

#### 1.3.1 Create VIP support AAP

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-aap
spec:
  subnet: ovn-default
  namespace: default
  selector:
    - "app: aap1"
```

VIP also supports the assignment of fixed and random addresses, as described above.

- `namespace`: In AAP scenarios, a VIP needs to specify a namespace explicitly. Only resources in the same namespace can enable the AAP function.
- `selector`: In the AAP scenario, the node selector used to select the Pod attached to the VIP has the same format as the NodeSelector format in Kubernetes.

Query the Port corresponding to the VIP:

```bash
# kubectl ko nbctl show ovn-default
switch e32e1d3b-c539-45f4-ab19-be4e33a061f6 (ovn-default)
    port aap-vip
        type: virtual
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox
  annotations:
    ovn.kubernetes.io/aaps: vip-aap
  labels:
    app: aap1
spec:
  containers:
    - name: busybox
      image: busybox
      command: ["sleep", "3600"]
      securityContext: 
        capabilities:
          add:
            - NET_ADMIN
```

Query the configuration of the AAP after the AAP is created:

```bash
# kubectl ko nbctl list logical_switch_port aap-vip
_uuid               : cd930750-0533-4f06-a6c0-217ddac73272
addresses           : []
dhcpv4_options      : []
dhcpv6_options      : []
dynamic_addresses   : []
enabled             : []
external_ids        : {ls=ovn-default, vendor=kube-ovn}
ha_chassis_group    : []
mirror_rules        : []
name                : aap-vip
options             : {virtual-ip="10.16.0.100", virtual-parents="busybox.default"}
parent_name         : []
port_security       : []
tag                 : []
tag_request         : []
type                : virtual
up                  : false
```

virtual-ip is set to the IP address reserved for the VIP, and virtual-parents is set to the Port of the Pod whose AAP function is enabled.

Query the configuration of the Pod after the POD is created:

```bash
# kubectl exec -it busybox -- ip addr add 10.16.0.100/16 dev eth0
# kubectl exec -it busybox01 -- ip addr show eth0
35: eth0@if36: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1400 qdisc noqueue 
    link/ether 00:00:00:e2:ab:0c brd ff:ff:ff:ff:ff:ff
    inet 10.16.0.7/16 brd 10.16.255.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet 10.16.0.100/16 scope global secondary eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fee2:ab0c/64 scope link 
       valid_lft forever preferred_lft forever
```

In addition to the IP assigned automatically when the Pod is created, the IP of the VIP is also successfully bound, and other Pods in the current subnet can communicate with these two IP addresses.

## 2. [SwitchLBRule](../vpc/vpc-internal-lb.en.md) VIP

!!! note

    This feature might be broken in recent versions, with users reporting that the VIP ceases to respond randomly. Issue is tracked here https://github.com/kubeovn/kube-ovn/issues/5377

VIPs with type set to `switch_lb_vip` are used when a **SwitchLBRule** wishes to have its VIP in the same CIDR as the **Subnet** in which it is deployed.

This is due to a limitation of OVN where the VIP of a loadbalancer should never be in the same CIDR as the subnet in which pods/VMs are trying to reach it. For example, a loadbalancer cannot have a VIP `10.0.0.100` if a pod in subnet `10.0.0.0/24` is expected to reach it.

The reason is that if the VIP is part of the subnet, the pods/VMs that try to reach the loadbalancer will have a local route to the VIP on their network interface. They will try to resolve the VIP's MAC address using ARP and will fail to do so because it doesn't physically exist. But if the VIP is in another subnet, the pods/VMs will forward the request to their default gateway on which a rule has been configured by OVN to NAT the traffic to the backends of the loadbalancer.

Using type `switch_lb_vip` circumvents that issue by creating a logical port that responds to ARP requests for the VIP. The traffic is redirected to the default gateway by responding with its MAC address.

The definition of such a `switch_lb_vip` VIP is simple.

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: slr-01
spec:
  subnet: ovn-default
  v4ip: 10.0.0.100
  type: switch_lb_vip
```

- `subnet`: the IP address will be reserved from this **subnet**
- `v4ip`: optional argument to use a specific IP within the subnet (SLRs only support IPv4)
- `type`: `switch_lb_vip` indicates that this VIP is used by a SwitchLB

## 3. POD Use VIP to reserve IP address

It is not recommended to use this function in production because the distinction between this function and IP function is not clear.

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: pod-use-vip
spec:
  subnet: ovn-default
  type: ""
```

> This feature has been supported since v1.12.

You can use annotations to assign a VIP to a Pod, then the pod will use the vip's ip address:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  annotations:
    ovn.kubernetes.io/vip: pod-use-vip # use vip name
  namespace: default
spec:
  containers:
    - name: static-ip
      image: docker.io/library/nginx:alpine

```

### 3.1 StatefulSet and Kubevirt VM retain VIP

Due to the particularity of 'StatefulSet' and 'VM', after their Pod is destroyed and pulled up, it will re-use the previously set VIP.

VM retention VIP needs to ensure that 'kube-ovn-controller' 'keep-vm-ip' parameter is' true '. Please refer to [Kubevirt VM enable keep its ip](../reference/setup-options.en.md#kubevirt-vm-fixed-address-settings)
