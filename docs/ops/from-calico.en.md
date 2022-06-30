# Install Kube-OVN From Calico

若 Kubernetes 集群已安装 Calico 需要变更为 Kube-OVN 可以参考本文档。

> 由于 Calico 各个版本的安装可能存在差异，并且更换过程中已有 Pod 网络
> 会中断，建议提前做好规划，并参照不同版本 Calico 安装差异进行调整。

## 卸载 Calico 组件

Operator 安装模式 Calico 卸载：

```bash
kubectl delete -f https://projectcalico.docs.tigera.io/manifests/tigera-operator.yaml
kubectl delete -f https://projectcalico.docs.tigera.io/manifests/custom-resources.yaml
```

Manifest 安装模式 Calico 卸载：

```bash
kubectl delete -f https://projectcalico.docs.tigera.io/manifests/calico.yaml 
```

## 残留配置清理

根据环境具体情况，在每台机器删除 CNI 相关配置文件：

```bash
rm -f /etc/cni/net.d/10-calico.conflist
rm -f /etc/cni/net.d/calico-kubeconfig
```

Calico 依然会在节点上残留路由规则，iptables 规则，veth 网络接口等配置信息，
建议重启节点清理相关配置，避免出现难以排查的问题。

## 安装 Kube-OVN

可参考[一键安装](../start/one-step-install.md)正常进行安装。
