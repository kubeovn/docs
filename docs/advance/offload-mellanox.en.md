# Offload with Mellanox

Kube-OVN uses OVS for traffic forwarding in the final data plane, and the associated flow table matching,
tunnel encapsulation and other functions are CPU-intensive, which consumes a lot of CPU resources and leads to higher latency and lower throughput under heavy traffic.
Mellanox Accelerated Switching And Packet Processing (ASAP²) technology offloads OVS-related operations to an eSwitch within the eSwitch in the hardware.
This technology can shorten the data path without modifying the OVS control plane, avoiding the use of host CPU resources,
which dramatically reduce latency and significantly increase the throughput.

![](../static/hw-offload.png)

## Prerequisites

- Mellanox CX5/CX6/BlueField that support ASAP².
- CentOS 8 Stream or Linux 5.7 above.
- Since the current NIC does not support `dp_hash` and `hash` operation offload, OVN LB function should be disabled.
- In order to support offload mode, the NIC cannot do bond.

## Setup SR-IOV

Check the device ID of the NIC, in the following example it is `42:00.0`:

```bash
# lspci -nn | grep ConnectX-5
42:00.0 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]
```

Find the corresponding NIC by its device ID:

```bash
# ls -l /sys/class/net/ | grep 42:00.0
lrwxrwxrwx. 1 root root 0 Jul 22 23:16 p4p1 -> ../../devices/pci0000:40/0000:40:02.0/0000:42:00.0/net/p4p1
```

Check the number of available VFs:

```bash
# cat /sys/class/net/p4p1/device/sriov_totalvfs
8
```

Create VFs and do not exceeding the number found above:

```bash
# echo '4' > /sys/class/net/p4p1/device/sriov_numvfs
# ip link show p4p1
10: p4p1: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
    link/ether b8:59:9f:c1:ec:12 brd ff:ff:ff:ff:ff:ff
    vf 0 MAC 00:00:00:00:00:00, spoof checking off, link-state auto, trust off, query_rss off
    vf 1 MAC 00:00:00:00:00:00, spoof checking off, link-state auto, trust off, query_rss off
    vf 2 MAC 00:00:00:00:00:00, spoof checking off, link-state auto, trust off, query_rss off
    vf 3 MAC 00:00:00:00:00:00, spoof checking off, link-state auto, trust off, query_rss off
# ip link set p4p1 up
```

Find the device IDs corresponding to the above VFs:

```bash
# lspci -nn | grep ConnectX-5
42:00.0 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]
42:00.1 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]
42:00.2 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5 Virtual Function] [15b3:1018]
42:00.3 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5 Virtual Function] [15b3:1018]
42:00.4 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5 Virtual Function] [15b3:1018]
42:00.5 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5 Virtual Function] [15b3:1018]
```

Unbound the VFs from the driver:

```bash
echo 0000:42:00.2 > /sys/bus/pci/drivers/mlx5_core/unbind
echo 0000:42:00.3 > /sys/bus/pci/drivers/mlx5_core/unbind
echo 0000:42:00.4 > /sys/bus/pci/drivers/mlx5_core/unbind
echo 0000:42:00.5 > /sys/bus/pci/drivers/mlx5_core/unbind
```

Enable eSwitch mode and set up hardware offload:

```bash
devlink dev eswitch set pci/0000:42:00.0 mode switchdev
ethtool -K enp66s0f0 hw-tc-offload on
```

Rebind the driver and complete the VF setup:

```bash
echo 0000:42:00.2 > /sys/bus/pci/drivers/mlx5_core/bind
echo 0000:42:00.3 > /sys/bus/pci/drivers/mlx5_core/bind
echo 0000:42:00.4 > /sys/bus/pci/drivers/mlx5_core/bind
echo 0000:42:00.5 > /sys/bus/pci/drivers/mlx5_core/bind
```

Some behaviors of `NetworkManager` may cause driver exceptions,
if offloading problems occur we recommended to close `NetworkManager` and try again.

```bash
systemctl stop NetworkManager
systemctl disable NetworkManager
```

## Install SR-IOV Device Plugin

Since each machine has a limited number of VFs and each Pod that uses acceleration will take up VF resources,
we need to use the SR-IOV Device Plugin to manage the corresponding resources so that the scheduler knows how to schedule.

Create SR-IOV Configmap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sriovdp-config
  namespace: kube-system
data:
  config.json: |
    {
      "resourceList": [{
          "resourcePrefix": "mellanox.com",
          "resourceName": "cx5_sriov_switchdev",
          "selectors": {
                  "vendors": ["15b3"],
                  "devices": ["1018"],
                  "drivers": ["mlx5_core"]
              }
      }
      ]
    }
```

Please read the [SR-IOV device plugin](https://github.com/intel/sriov-network-device-plugin) to deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/intel/sriov-network-device-plugin/master/deployments/k8s-v1.16/sriovdp-daemonset.yaml
```

Check if SR-IOV resources have been registered to Kubernetes Node:

```bash
kubectl describe node kube-ovn-01  | grep mellanox

mellanox.com/cx5_sriov_switchdev:  4
mellanox.com/cx5_sriov_switchdev:  4
mellanox.com/cx5_sriov_switchdev  0           0
```

## Install Multus-CNI

The device IDs obtained during SR-IOV Device Plugin scheduling need to be passed to Kube-OVN via Multus-CNI, so Multus-CNI needs to be configured to perform the related tasks.

Please read [Multus-CNI Document](https://github.com/k8snetworkplumbingwg/multus-cni) to deploy：

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset.yml
```

Create `NetworkAttachmentDefinition`：

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: default
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/resourceName: mellanox.com/cx5_sriov_switchdev
spec:
  config: '{
    "cniVersion": "0.3.1",
    "name": "kube-ovn",
    "plugins":[
        {
            "type":"kube-ovn",
            "server_socket":"/run/openvswitch/kube-ovn-daemon.sock",
            "provider": "default.default.ovn"
        },
        {
            "type":"portmap",
            "capabilities":{
                "portMappings":true
            }
        }
    ]
}'
```

- `provider`: the format should be {name}.{namespace}.ovn of related `NetworkAttachmentDefinition`.

## Enable Offload in Kube-OVN

Download the scripts:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install.sh
```

Change the related options，`IFACE` should be the physic NIC and has an IP:

```bash
ENABLE_MIRROR=${ENABLE_MIRROR:-false}
HW_OFFLOAD=${HW_OFFLOAD:-true}
ENABLE_LB=${ENABLE_LB:-false}
IFACE="ensp01"
```

Install Kube-OVN：

```bash
bash install.sh
```

## Create Pods with VF NICs

Pods that use VF for network offload acceleration can be created using the following yaml:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  annotations:
    v1.multus-cni.io/default-network: default/default
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
    resources:
      requests:
        mellanox.com/cx5_sriov_switchdev: '1'
      limits:
        mellanox.com/cx5_sriov_switchdev: '1'
```

- `v1.multus-cni.io/default-network`: should be the {namespace}/{name} of related `NetworkAttachmentDefinition`.

Running the following command in the `ovs-ovn` container of the Pod run node to observe if offload success.

```bash
# ovs-appctl dpctl/dump-flows -m type=offloaded
ufid:91cc45de-e7e9-4935-8f82-1890430b0f66, skb_priority(0/0),skb_mark(0/0),ct_state(0/0x23),ct_zone(0/0),ct_mark(0/0),ct_label(0/0x1),recirc_id(0),dp_hash(0/0),in_port(5b45c61b307e_h),packet_type(ns=0/0,id=0/0),eth(src=00:00:00:c5:6d:4e,dst=00:00:00:e7:16:ce),eth_type(0x0800),ipv4(src=0.0.0.0/0.0.0.0,dst=0.0.0.0/0.0.0.0,proto=0/0,tos=0/0,ttl=0/0,frag=no), packets:941539, bytes:62142230, used:0.260s, offloaded:yes, dp:tc, actions:54235e5753b8_h
ufid:e00768d7-e652-4d79-8182-3291d852b791, skb_priority(0/0),skb_mark(0/0),ct_state(0/0x23),ct_zone(0/0),ct_mark(0/0),ct_label(0/0x1),recirc_id(0),dp_hash(0/0),in_port(54235e5753b8_h),packet_type(ns=0/0,id=0/0),eth(src=00:00:00:e7:16:ce,dst=00:00:00:c5:6d:4e),eth_type(0x0800),ipv4(src=0.0.0.0/0.0.0.0,dst=0.0.0.0/0.0.0.0,proto=0/0,tos=0/0,ttl=0/0,frag=no), packets:82386659, bytes:115944854173, used:0.260s, offloaded:yes, dp:tc, actions:5b45c61b307e_h
```

If there is `offloaded:yes, dp:tc` content, the offloading is successful.
