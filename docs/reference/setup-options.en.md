# Installation and Configuration Options

In [One-Click Installation](../start/one-step-install.en.md) we use the default configuration for installation.
Kube-OVN also supports more custom configurations, which can be configured in the installation script,
or later by changing the parameters of individual components.
This document will describe what these customization options do, and how to configure them.

## Built-in Network Settings

Kube-OVN will configure two built-in Subnets during installation:

1. `default` Subnet, as the default subnet used by the Pod to assign IPs, with a default CIDR of `10.16.0.0/16` and a gateway of `10.16.0.1`.
2. The `join` subnet, as a special subnet for network communication between the Node and Pod, has a default CIDR of `100.64.0.0/16` and a gateway of `100.64.0.1`.

The configuration of these two subnets can be changed during installation via the installation scripts variables:

```bash
POD_CIDR="10.16.0.0/16"
POD_GATEWAY="10.16.0.1"
JOIN_CIDR="100.64.0.0/16"
EXCLUDE_IPS=""
```

`EXCLUDE_IP` sets the address range for which `kube-ovn-controller` will not automatically assign from it, the format is: `192.168.10.20..192.168.10.30`.

Note that in the Overlay case these two Subnets CIDRs cannot conflict with existing host networks and Service CIDRs.

You can change the address range of both Subnets after installation by referring to [Change Subnet CIDR](../ops/change-default-subnet.en.md) and [Change Join Subnet CIDR](../ops/change-join-subnet.en.md).

## Config Service CIDR

Since some of the iptables and routing rules set by `kube-proxy` will conflict with the rules set by Kube-OVN,
Kube-OVN needs to know the CIDR of the service to set the corresponding rules correctly.

This can be done by modifying the installation script:

```bash
SVC_CIDR="10.96.0.0/12"  
```

You can also modify the args of the `kube-ovn-controller` Deployment after installation:

```yaml
args:
- --service-cluster-ip-range=10.96.0.0/12
```

## Overlay NIC Selection

In the case of multiple NICs on a node, Kube-OVN will select the NIC corresponding to the Kubernetes Node IP as the NIC
for cross-node communication between containers and establish the corresponding tunnel.

If you need to select another NIC to create a container tunnel, you can change it in the installation script:

```bash
IFACE=eth1
```

This option supports regular expressions separated by commas, e.g. 'ens[a-z0-9]*,eth[a-z0-9]*'.

It can also be adjusted after installation by modifying the args of the `kube-ovn-cni` DaemonSet:

```yaml
args:
- --iface=eth1
```

If each machine has a different NIC name and there is no fixed pattern, you can use the node annotation `ovn.kubernetes.io/tunnel_interface` to configure each node one by one.
This annotation will override the configuration of `iface`.

```bash
kubectl annotate node no1 ovn.kubernetes.io/tunnel_interface=ethx
```

## Config MTU

Since Overlay encapsulation requires additional space, Kube-OVN will adjust the MTU of the container NIC based on the MTU of the selected NIC when creating the container NIC.
By default, the Pod NIC MTU is the host NIC MTU - 100 on the Overlay Subnet, and the Pod NIC and host NIC have the same MTU on the Underlay Subnet.

If you need to adjust the size of the MTU under the Overlay subnet, you can modify the parameters of the `kube-ovn-cni` DaemonSet:

```yaml
args:
- --mtu=1333
```

## Global Traffic Mirroring Setting

When global traffic mirroring is enabled, Kube-OVN will create a `mirror0` virtual NIC on each node
and copy all container network traffic from the current machine to that NIC,
Users can perform traffic analysis with tcpdump and other tools. This function can be enabled in the installation script:

```bash
ENABLE_MIRROR=true
```

It can also be adjusted after installation by modifying the args of the `kube-ovn-cni` DaemonSet:

```yaml
args:
- --enable-mirror=true
```

The ability to mirror traffic is disabled in the default installation,
if you need fine-grained traffic mirroring or need to mirror traffic to additional NICs please refer to [Traffic Mirror](../guide/mirror.en.md).

## LB Settings

In Underlay scenarios, `kube-proxy` cannot intercept container network traffic, so it cannot implement Service forwarding functionality. In this case, you can enable OVN's built-in L2 LB capability to implement ClusterIP forwarding. In scenarios where Service forwarding capability is not needed, you can disable the LB capability to achieve better performance. Note that this feature only implements ClusterIP forwarding for container networks and cannot replace all capabilities of `kube-proxy`, so it cannot replace `kube-proxy`.

This feature can be configured in the installation script:

```bash
ENABLE_LB=false
```

It can also be configured after installation by changing the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-lb=false
```

The LB feature is enabled in the default installation.

The spec field `enableLb` has been added to the subnet crd definition since Kube-OVN v1.12.0 to migrate the LB function of Kube-OVN to the subnet level. You can set whether to enable the LB function based on different subnets. The `enable-lb` parameter in the `kube-ovn-controller` deployment is used as a global switch to control whether to create a load-balancer record. The `enableLb` parameter added in the subnet is used to control whether the subnet is associated with a load-balancer record. After the previous version is upgraded to v1.12.0, the `enableLb` parameter of the subnet will automatically inherit the value of the original global switch parameter.

## NetworkPolicy Settings

Kube-OVN uses ACLs in OVN to implement NetworkPolicy.
Users can choose to disable the NetworkPolicy feature or use the Cilium Chain approach to implement NetworkPolicy using eBPF.
In this case, the NetworkPolicy feature of Kube-OVN can be disabled to achieve better performance on the control plane and data plane.

This feature can be configured in the installation script:

```bash
ENABLE_NP=false
```

It can also be configured after installation by changing the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-np=false
```

NetworkPolicy is enabled by default.

## EIP and SNAT Settings

If the EIP and SNAT capabilities are not required on the default VPC,
users can choose to disable them to reduce the performance overhead of `kube-ovn-controller` in
large scale cluster environments and improve processing speed.

This feature can be configured in the installation script:

```bash
ENABLE_EIP_SNAT=false
```

It can also be configured after installation by changing the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-eip-snat=false
```

EIP and SNAT is enabled by default. More information can refer to [EIP and SNAT](../guide/eip-snat.en.md).

## Centralized Gateway ECMP Settings

The centralized gateway supports two mode of high availability, primary-backup and ECMP.
If you want to enable ECMP mode, you need to change the args of `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-ecmp=true 
```

Centralized gateway default installation under the primary-backup mode, more gateway-related content please refer to [Config Subnet](../guide/subnet.en.md).

The spec field `enableEcmp` has been added to the subnet crd definition since Kube-OVN v1.12.0 to migrate the ECMP switch to the subnet level. You can set whether to enable ECMP mode based on different subnets. The `enable-ecmp` parameter in the `kube-ovn-controller` deployment is no longer used. After the previous version is upgraded to v1.12.0, the subnet switch will automatically inherit the value of the original global switch parameter.

## Kubevirt VM Fixed Address Settings

For VM instances created by Kubevirt, `kube-ovn-controller` can assign and manage IP addresses in a similar way to the StatefulSet Pod.
This allows VM instances address fixed during start-up, shutdown, upgrade, migration, and other operations throughout their lifecycle,
making them more compatible with the actual virtualization user experience.

This feature is enabled by default after v1.10.6. To disable this feature, you need to change the following args in the `kube-ovn-controller` Deployment:

```yaml
args:
- --keep-vm-ip=false
```

## CNI Settings

By default, Kube-OVN installs the CNI binary in the `/opt/cni/bin` directory
and the CNI configuration file `01-kube-ovn.conflist` in the `/etc/cni/net.d` directory.
If you need to change the installation location and the priority of the CNI configuration file,
you can modify the following parameters of the installation script.

```bash
CNI_CONF_DIR="/etc/cni/net.d"
CNI_BIN_DIR="/opt/cni/bin"
CNI_CONFIG_PRIORITY="01"
```

Or change the Volume mount and args of the `kube-ovn-cni` DaemonSet after installation:

```yaml
volumes:
- name: cni-conf
  hostPath:
    path: "/etc/cni/net.d"
- name: cni-bin
  hostPath:
    path:"/opt/cni/bin"
...
args:
- --cni-conf-name=01-kube-ovn.conflist
```

## Tunnel Type Settings

The default encapsulation mode of Kube-OVN Overlay is Geneve,
if you want to change it to Vxlan or STT,
please adjust the following parameters in the installation script:

```bash
TUNNEL_TYPE="vxlan"
```

Or change the environment variables of `ovs-ovn` DaemonSet after installation:

```yaml
env:
- name: TUNNEL_TYPE
  value: "vxlan"
```

If you need to use the STT tunnel and need to compile additional kernel modules for ovs, please refer to [Performance Tuning](../advance/performance-tuning.en.md).

Please refer to [Tunneling Protocol Selection](../reference/tunnel-protocol.en.md) for the differences between the different protocols in practice.

## SSL Settings

The OVN DB API interface supports SSL encryption to secure the connection.
To enable it, adjust the following parameters in the installation script:

```bash
ENABLE_SSL=true
```

The SSL is disabled by default.
