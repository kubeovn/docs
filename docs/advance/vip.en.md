# VIP Reservation

In some scenarios we want to dynamically reserve part of the IP but not assign it to Pods but to other infrastructure e.g:

- Kubernetes nested Kubernetes scenarios where the upper Kubernetes uses the Underlay network take up the available addresses of the underlying Subnet.
- LB or other network infrastructure requires the use of an IP within a Subnet.

In addition, VIP can also reserve IP for Allowed-Address-Pairs to support scenarios where a single network card is configured with multiple IPs, e.g:

- Keepalived can help achieve fast failover and flexible load balancing architecture by configuring additional IP address pairs.

## Create Random Address VIP

If you just want to set aside a number of IPs and have no requirement for the IP addresses themselves, you can use the following yaml to create them:

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-dynamic-01
spec:
  subnet: ovn-default
  type: ""
```

- `subnet`: reserve the IP from this Subnet.
- `type`: Currently, two types are supported. If the value is empty, it indicates that it is only used for occupying ip addresses of ipam. `switch_lb_vip` The front-end vip address and back-end ip address of the switch lb must be on the same subnet.

Query the VIP after creation.

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
vip-dynamic-01   10.16.0.12           00:00:00:F0:DB:25                         ovn-default   true
```

It can be seen that the VIP is assigned the IP address `10.16.0.12`, which can later be used by other network infrastructures.

## Create a fixed address VIP

The IP address of the reserved VIP can be fixed using the following yaml:

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: static-vip01
spec:
  subnet: ovn-default 
  V4ip: "10.16.0.121"
```

- `subnet`: reserve the IP from this Subnet.
- `V4ip`: A fixed-assigned IP address that should within the CIDR range of `subnet`.

Query the VIP after creation:

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
static-vip01   10.16.0.121           00:00:00:F0:DB:26                         ovn-default   true
```

It can be seen that the VIP has been assigned the expected IP address.

## Pod uses VIP to bind IP

> This feature is supported starting from v1.12.

You can use annotation to assign a VIP to a Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  annotations:
    ovn.kubernetes.io/vip: vip-dynamic-01 # Specify vip
  namespace: default
spec:
  containers:
    - name: static-ip
      image: docker.io/library/nginx:alpine
```

## StatefulSet & Kubevirt VM keep VIP

Specify for `StatefulSet` and `VM` resources, these Pods their owned will reuse the VIP when these Pods recreating.

VM keep VIP must be enable the `keep-vm-ip` param in `kube-ovn-controller`. Refer [Kubevirt VM Fixed Address Settings](../guide/setup-options.en.md#kubevirt-vm)

## Create VIP to support AAP

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

VIP also supports the allocation of fixed addresses and random addresses, and the allocation method is as described above.

- `namespace`: In the AAP scenario, VIP needs to explicitly specify the namespace. VIP only allows resources in the same namespace to enable the AAP function.
- `selector`: In the AAP scenario, the node selector used to select the Pod attached to the vip has the same format as the NodeSelector in Kubernetes.

Query the Port corresponding to the VIP after creation:

```yaml
# kubectl ko nbctl show ovn-default
switch e32e1d3b-c539-45f4-ab19-be4e33a061f6 (ovn-default)
    port aap-vip
        type: virtual
```

## Pod uses VIP to enable AAP

You can use annotation to specify a VIP to enable the AAP function, and labels need to meet the conditions of the node selector in the VIP.

Pod supports specifying multiple VIPs, with a configuration format of: ovn.kubernetes.io/aaps: vip-aap,vip-aap2,vip-aap3

The AAP function supports [multiple interfaces] (./multi-nic.en.md). If the Pod is configured with multiple interfaces, AAP will configure the corresponding Port in the same subnet of the Pod and the VIP.

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

Query the configuration corresponding to the AAP after creation:

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

Virtual ip is configured as an IP reserved for VIP, while virtual parents are configured as the port corresponding to the pod that enables AAP function.

Query the configuration corresponding to the Pod after creation:

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

In addition to the IP automatically assigned during Pod creation, the VIP IP has also been successfully bound, and other Pods within the current subnet can communicate with these two IPs.
