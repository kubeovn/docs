# 删除工作节点

由于节点上 `ovs-ovn` 中运行的 `ovn-controller` 进程会定期连接 `ovn-central` 并注册相关网络信息，会导致额外
浪费资源开销并有潜在的规则冲突风险。因此在从 Kubernetes 内删除节点时，请按照下面的步骤来保证网络信息可以正常被清理。

该文档介绍删除工作节点的步骤，如需更换 `ovn-central` 所在节点，请参考[更换 ovn-central 节点](./change-ovn-central-node.md)

## 驱逐节点上所有容器

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

## 登录对应节点并停止 kubelet 和 docker 已停止对应 DaemonSet pod，

该步骤会停止 `ovs-ovn` 容器，避免向 `ovn-central` 进行注册
  
```bash
systemctl stop kubelet
systemctl stop docker
```

## 清理 node 上的 ovs/ovn 残留数据

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

## 使用 kubectl 删除节点

```bash
kubectl delete no kube-ovn-01
```

## 检查对应节点是否从 ovn-sb 中删除

下面的示例为 `kube-ovn-worker` 依然未被删除
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

## 若节点对应的 chassis 依然存在，手动进行删除

uuid 为之前命令所查出的 Chassis 对应 id

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
