# NodeLocal DNSCache 和 kube-ovn 适配

NodeLocal DNSCache 是通过集群节点上作为 DaemonSet 运行 DNS 缓存来提高集群 DNS 性能，该功能也可以和 kube-ovn 适配。

## 节点本地 DNS 缓存部署

### 部署 k8s 的节点本地 DNS 缓存

该步骤参考 k8s 官网配置 [nodelocaldnscache](https://kubernetes.io/zh-cn/docs/tasks/administer-cluster/nodelocaldns/)。

使用以下脚本部署：

```bash
#!bin/bash

localdns=169.254.20.10
domain=cluster.local
kubedns=10.96.0.10

wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml
sed -i "s/__PILLAR__LOCAL__DNS__/$localdns/g; s/__PILLAR__DNS__DOMAIN__/$domain/g; s/,__PILLAR__DNS__SERVER__//g; s/__PILLAR__CLUSTER__DNS__/$kubedns/g" nodelocaldns.yaml

kubectl apply -f nodelocaldns.yaml
```

修改每个节点上的 kubelet 配置文件，将 /var/lib/kubelet/config.yaml 中的 clusterDNS 字段修改为本地 dns ip 169.254.20.10，然后重启 kubelet 服务。

### kube-ovn 相应 DNS 配置

部署好 k8s 的 nodelocaldnscache 组件后， kube-ovn 需要做出下面修改：

#### underlay subnet 开启 u2o 开关

如果是 underlay subnet 需要使用本地 DNS 功能，需要开启 u2o 功能，即在 kubectl edit subnet {your subnet} 中配置 spec.u2oInterconnection = true , 如果是 overlay subnet 则不需要这步操作。

#### 给 kube-ovn-controller 指定对应的本地 dns ip

```bash
kubectl patch deployment kube-ovn-controller -n kube-system --type=json -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--node-local-dns-ip=169.254.20.10"}]'
```

#### 重建已经创建的 pod

这步原因是让 pod 重新生成 /etc/resolv.conf 让 nameserver 指向本地 dns ip，如果没有重建 pod 的 nameserver 将仍然使用集群的 dns cluster ip。同时 u2o 开关如果开启也需要重建 pod 来重新生成 pod 网关。

## 验证节点本地 DNS 缓存功能

以上配置完成后可以找到 pod 验证如下，可以看到 pod 的 dns 服务器是指向本地 169.254.20.10 ，并成功解析域名：

```bash
# kubectl exec -it pod1 -- nslookup github.com
Server:         169.254.20.10
Address:        169.254.20.10:53


Name:   github.com
Address: 20.205.243.166
```