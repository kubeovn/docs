# Offload with YUSUR

Kube-OVN uses OVS for traffic forwarding in the final data plane, and the associated flow table matching, tunnel encapsulation and other functions are CPU-intensive, which consumes a lot of CPU resources and leads to higher latency and lower throughput under heavy traffic.YUSUR CONFLUX-22OOE series SmartNIC can offload OVS-related operations to the hardware. This technology can shorten the data path without modifying the OVS control plane, avoiding the use of host CPU resources, which dramatically reduce latency and significantly increase the throughput.

!!! note

    The solution described in this article was verified in 2024. However, hardware NICs may now have new features, and some limitations mentioned may have been resolved. Please consult your hardware vendor for the latest technical constraints and capabilities.

## Prerequisites

- YUSUR CONFLUX-22OOE series SmartNIC.
- ensure hados(Heterogeneous Agile Developing & Operating System) installed.
- Enable SR-IOV in BIOS.

## Installation Guide

### Setting Up SR-IOV

1. Based on the vendor ID (1f47) of the YUSUR CONFLUX-22OOE series SmartNIC, identify the device IDs of the network card on the host, such as (00:0a.0) and (00:0b.0), which correspond to the two physical ports on the 2200E. You can select one according to the fiber connection status.

```bash
lspci | grep 1f47
00:0a.0 Ethernet controller: Device 1f47:1001 (rev 10)
00:0b.0 Ethernet controller: Device 1f47:1001 (rev 10)
```

2. Check available VF number:

``` bash
cat /sys/bus/pci/devices/0000\:00\:0a.0/sriov_totalvfs
256
```

3. Create VFs and do not exceeding the number found above:

```bash
echo 7 > /sys/bus/pci/devices/0000\:00\:0a.0/sriov_numvfs
```

4. Find the device IDs corresponding to the above VFs:

```bash
lspci | grep 1f47
00:0a.0 Ethernet controller: Device 1f47:1001 (rev 10)
00:0a.1 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.2 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.3 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.4 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.5 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.6 Ethernet controller: Device 1f47:110f (rev 10)
00:0a.7 Ethernet controller: Device 1f47:110f (rev 10)
00:0b.0 Ethernet controller: Device 1f47:1001 (rev 10)
```

### Configure and install SR-IOV Device Plugin

1. Create an SR-IOV related ConfigMap to facilitate the SR-IOV Device Plugin installation, enabling it to locate VF resources on nodes based on this configuration and provide them for Pod usage:

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
                "resourceName": "sriov_dpu",
                "resourcePrefix": "yusur.tech",
                "selectors": {
                    "vendors": ["1f47"],
                    "devices": ["110f"]
                }}
        ]
    }
 
```

2. Install and run the SR-IOV Device Plugin.

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/sriov-network-device-plugin/v3.6.2/deployments/sriovdp-daemonset.yaml
```

3. Check if SR-IOV resources have been registered to Kubernetes Node:

```bash
kubectl describe node node1 | grep yusur
  yusur.tech/sriov_dpu:  7
  yusur.tech/sriov_dpu:  7
  yusur.tech/sriov_dpu  0           0
```

## Install Multus-CNI

The device IDs obtained during SR-IOV Device Plugin scheduling need to be passed to Kube-OVN via Multus-CNI, so Multus-CNI needs to be configured to perform the related tasks.

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/v4.0.2/deployments/multus-daemonset-thick.yml
```

Create `NetworkAttachmentDefinition`:

```yaml
apiVersion:
  "k8s.cni.cncf.io/v1"
kind:
  NetworkAttachmentDefinition
metadata:
  name: test
  namespace: kube-system
  annotations:
    k8s.v1.cni.cncf.io/resourceName: yusur.tech/sriov_dpu
spec:
  config: '{
    "cniVersion": "0.3.1",
    "name": "kube-ovn",
    "plugins":[
        {
            "type":"kube-ovn",
            "server_socket":"/run/openvswitch/kube-ovn-daemon.sock",
            "provider": "test.kube-system.ovn"
        },
        {
            "type":"portmap",
            "capabilities":{
                "portMappings":true
            }
        }
    ]
}
```

- `provider`: the format should be `{name}.{namespace}.ovn` of related NetworkAttachmentDefinition.

## Enable Offload in Kube-OVN

1. Download the scripts:

```bash
wget https://github.com/kubeovn/kube-ovn/blob/release-1.12/dist/images/install.sh
```

Change the related options, `IFACE` should be the physic NIC and has an IP:

```bash
ENABLE_MIRROR=${ENABLE_MIRROR:-false}
HW_OFFLOAD=${HW_OFFLOAD:-true}
ENABLE_LB=${ENABLE_LB:-false}
IFACE="p0"
```

2. Install Kube-OVN:

```bash
bash install.sh
```

### Create Pods with VF NICsCreate Pods with VF NICs

Pods that use VF for network offload acceleration can be created using the following yaml:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  namespace: default
  annotations:
    v1.multus-cni.io/default-network: kube-system/test
spec:
  containers:
    - name: nginx
      image: docker.io/library/nginx:alpine
      resources:
        requests:
          yusur.tech/sriov_dpu: '1'
        limits:
          yusur.tech/sriov_dpu: '1'
```

- `v1.multus-cni.io/default-network`: should be the `{namespace}/{name}` of related NetworkAttachmentDefinition.

### Offload verification

Running the following command in the `ovs-ovn` container of the Pod run node to observe if offload success.

```bash
# ovs-appctl dpctl/dump-flows -m type=offloaded
ufid:67c2e10f-92d4-4574-be70-d072815ff166, skb_priority(0/0),skb_mark(0/0),ct_state(0/0x23),ct_zone(0/0),ct_mark(0/0),ct_label(0/0),recirc_id(0),dp_hash(0/0),in_port(d85b161b6840_h),packet_type(ns=0/0,id=0/0),eth(src=0a:c9:1c:70:01:09,dst=8a:18:a4:22:b7:7d),eth_type(0x0800),ipv4(src=10.0.1.10,dst=10.0.1.6,proto=6,tos=0/0x3,ttl=0/0,frag=no),tcp(src=60774,dst=9001), packets:75021, bytes:109521630, offload_packets:75019, offload_bytes:109521498, used:3.990s,offloaded:yes,dp:tc, actions:set(tunnel(tun_id=0x5,dst=192.168.201.12,ttl=64,tp_dst=6081,geneve({class=0x102,type=0x80,len=4,0xa0006}),flags(csum|key))),genev_sys_6081
ufid:7940666e-a0bd-42a5-8116-1e84e81bb338, skb_priority(0/0),tunnel(tun_id=0x5,src=192.168.201.12,dst=192.168.201.11,ttl=0/0,tp_dst=6081,geneve({class=0x102,type=0x80,len=4,0x6000a}),flags(+key)),skb_mark(0/0),ct_state(0/0),ct_zone(0/0),ct_mark(0/0),ct_label(0/0),recirc_id(0),dp_hash(0/0),in_port(genev_sys_6081),packet_type(ns=0/0,id=0/0),eth(src=8a:18:a4:22:b7:7d,dst=0a:c9:1c:70:01:09),eth_type(0x0800),ipv4(src=10.0.1.6,dst=10.0.1.10,proto=6,tos=0/0,ttl=0/0,frag=no),tcp(src=9001,dst=60774), packets:6946, bytes:459664, offload_packets:6944, offload_bytes:459532, used:4.170s, dp:tc,offloaded:yes,actions:d85b161b6840_h
```
