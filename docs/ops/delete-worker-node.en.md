# Delete Work Node

If the node is simply removed from Kubernetes, the `ovn-controller` process running in `ovs-ovn` on the node will periodically
connect to `ovn-central` to register relevant network information.
This leads to additional resource waste and potential rule conflict risk.
Therefore, when removing nodes from within Kubernetes, follow the steps below to ensure that related resources are cleaned up properly.

This document describes the steps to delete a worker node, if you want to change the node where `ovn-central` is located, please refer to [Replace ovn-central Node](./change-ovn-central-node.en.md).

## Evict Pods on the Node

````bash
 # kubectl drain kube-ovn-worker --ignore-daemonsets --force
 node/kube-ovn-worker cordoned
 WARNING: ignoring DaemonSet-managed Pods: kube-system/kube-ovn-cni-zt74b, kube-system/kube-ovn-pinger-5rxfs, kube-system/kube-proxy-jpmnm, kube-system/ovs-ovn-v2kll
 evicting pod kube-system/coredns-64897985d-qsgpt
 evicting pod local-path-storage/local-path-provisioner-5ddd94ff66-llss6
 evicting pod kube-system/kube-ovn-controller-8459db5ff4-94lxb
 pod/kube-ovn-controller-8459db5ff4-94lxb evicted
 pod/coredns-64897985d-qsgpt evicted
 pod/local-path-provisioner-5ddd94ff66-llss6 evicted
 node/kube-ovn-worker drained
````

## Stop kubelet and docker

This step stops the `ovs-ovn` container to avoid registering information to `ovn-central`.
Log into the corresponding node and run the following commands:
  
```bash
systemctl stop kubelet
systemctl stop docker
```

If using containerd as the CRI, the following command needs to be executed to stop the `ovs-ovn` container:

```bash
crictl rm -f $(crictl ps | grep openvswitch | awk '{print $1}')
```

## Cleanup Files on Node

```bash
rm -rf /var/run/openvswitch
rm -rf /var/run/ovn
rm -rf /etc/origin/openvswitch/
rm -rf /etc/origin/ovn/
rm -rf /etc/cni/net.d/00-kube-ovn.conflist
rm -rf /etc/cni/net.d/01-kube-ovn.conflist
rm -rf /var/log/openvswitch
rm -rf /var/log/ovn
```

## Delete the Node

```bash
kubectl delete no kube-ovn-01
```

## Check If Node Removed from OVN-SB

In the example below, the node `kube-ovn-worker` is not removed:

```bash
# kubectl ko sbctl show
Chassis "b0564934-5a0d-4804-a4c0-476c93596a17"
  hostname: kube-ovn-worker
  Encap geneve
      ip: "172.18.0.2"
      options: {csum="true"}
  Port_Binding kube-ovn-pinger-5rxfs.kube-system
Chassis "6a29de7e-d731-4eaf-bacd-2f239ee52b28"
  hostname: kube-ovn-control-plane
  Encap geneve
      ip: "172.18.0.3"
      options: {csum="true"}
  Port_Binding coredns-64897985d-nbfln.kube-system
  Port_Binding node-kube-ovn-control-plane
  Port_Binding local-path-provisioner-5ddd94ff66-h4tn9.local-path-storage
  Port_Binding kube-ovn-pinger-hf2p6.kube-system
  Port_Binding coredns-64897985d-fhwlw.kube-system
```

## Delete the Chassis Manually

Use the uuid find above to delete the chassis:

```bash
# kubectl ko sbctl chassis-del b0564934-5a0d-4804-a4c0-476c93596a17
# kubectl ko sbctl show
Chassis "6a29de7e-d731-4eaf-bacd-2f239ee52b28"
  hostname: kube-ovn-control-plane
  Encap geneve
      ip: "172.18.0.3"
      options: {csum="true"}
  Port_Binding coredns-64897985d-nbfln.kube-system
  Port_Binding node-kube-ovn-control-plane
  Port_Binding local-path-provisioner-5ddd94ff66-h4tn9.local-path-storage
  Port_Binding kube-ovn-pinger-hf2p6.kube-system
  Port_Binding coredns-64897985d-fhwlw.kube-system
```
