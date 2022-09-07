# 卸载 Calico 安装 Kube-OVN

若 Kubernetes 集群已安装 Calico 需要变更为 Kube-OVN 可以参考本文档。

> 本文以 Calico v3.24.1 为例，其它 Calico 版本需要根据实际情况进行调整。

## 准备工作

为了保证切换 CNI 过程中集群网络保持畅通，Calico ippool 需要开启 nat outgoing，**或**在所有节点上关闭 rp_filter：

```sh
sysctl net.ipv4.conf.all.rp_filter=0
sysctl net.ipv4.conf.default.rp_filter=0
# IPIP 模式
sysctl net.ipv4.conf.tunl0.rp_filter=0
# VXLAN 模式
sysctl net.ipv4.conf.vxlan/calico.rp_filter=0
# 路由模式，eth0 需要修改为实际使用的网卡
sysctl net.ipv4.conf.eth0.rp_filter=0
```

## 部署 Kube-OVN

### 下载安装脚本

```sh
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/release-1.10/dist/images/install.sh
```

### 修改安装脚本

将安装脚本中重建 Pod 的部分删除：

```sh
echo "[Step 4/6] Delete pod that not in host network mode"
for ns in $(kubectl get ns --no-headers -o custom-columns=NAME:.metadata.name); do
  for pod in $(kubectl get pod --no-headers -n "$ns" --field-selector spec.restartPolicy=Always -o custom-columns=NAME:.metadata.name,HOST:spec.hostNetwork | awk '{if ($2!="true") print $1}'); do
    kubectl delete pod "$pod" -n "$ns" --ignore-not-found
  done
done
```

按需修改以下配置：

```sh
REGISTRY="kubeovn"                     # 镜像仓库地址
VERSION="v1.10.6"                      # 镜像版本/Tag
POD_CIDR="10.16.0.0/16"                # 默认子网 CIDR 不要和 SVC/NODE/JOIN CIDR 重叠
SVC_CIDR="10.96.0.0/12"                # 需要和 apiserver 的 service-cluster-ip-range 保持一致
JOIN_CIDR="100.64.0.0/16"              # Pod 和主机通信网络 CIDR，不要和 SVC/NODE/POD CIDR 重叠 
LABEL="node-role.kubernetes.io/master" # 部署 OVN DB 节点的标签
IFACE=""                               # 容器网络所使用的的宿主机网卡名，如果为空则使用 Kubernetes 中的 Node IP 所在网卡
TUNNEL_TYPE="geneve"                   # 隧道封装协议，可选 geneve, vxlan 或 stt，stt 需要单独编译 ovs 内核模块
```

**注意**：POD_CIDR 及 JOIN_CIDR 不可与 Calico ippool 的 CIDR 冲突，且 POD_CIDR 需要包含足够多的 IP 来容纳集群中已有的 Pod。

### 执行安装脚本

```sh
bash install.sh
```

## 逐个节点迁移

按照以下方法为每个节点逐个进行迁移。
**注意**：命令中的 *\<NODE\>* 需要替换为节点名称。

### 驱逐节点

```sh
kubectl drain --ignore-daemonsets <NODE>
```

若此命令一直等待 Pod 被驱逐，执行以下命令强制删除被驱逐的 Pod：

```sh
kubectl get pod -A --field-selector=spec.nodeName=<NODE> --no-headers | \
    awk '$4=="Terminating" {print $1" "$2}' | \
    while read s; do kubectl delete pod --force -n $s; done
```

### 重启节点

在节点中执行：

```sh
shutdown -r 0
```

### 恢复节点

```sh
kubectl uncordon <NODE>
```

## 卸载 Calico

### 删除 k8s 资源

```sh
kubectl -n kube-system delete deploy calico-kube-controllers
kubectl -n kube-system delete ds calico-node
kubectl -n kube-system delete cm calico-config
# 删除 CRD 及相关资源
kubectl get crd -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | while read crd; do
  if ! echo $crd | grep '.crd.projectcalico.org$' >/dev/null; then
    continue
  fi

  for name in $(kubectl get $crd -o jsonpath='{.items[*].metadata.name}'); do
    kubectl delete $crd $name
  done
  kubectl delete crd $crd
done
# 其它资源
kubectl delete --ignore-not-found clusterrolebinding calico-node calico-kube-controllers
kubectl delete --ignore-not-found clusterrole calico-node calico-kube-controllers
kubectl delete --ignore-not-found sa -n kube-system calico-kube-controllers calico-node
kubectl delete --ignore-not-found pdb -n kube-system calico-kube-controllers
```

### 清理节点文件

在每个节点中执行：

```sh
rm -f /etc/cni/net.d/10-calico.conflist /etc/cni/net.d/calico-kubeconfig
rm -f /opt/cni/bin/calico /opt/cni/bin/calico-ipam
```
