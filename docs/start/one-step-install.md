# 一键安装

Kube-OVN 提供了一键安装脚本，可以帮助你快速安装一个高可用，生产就绪的 Kube-OVN 容器网络，默认部署为 Overlay 类型网络。

从 Kube-OVN v1.12.0 版本开始，支持 Helm Chart 安装，默认部署为 Overlay 类型网络。

如果默认网络需要搭建 Underlay/Vlan 网络，请参考 [Underlay 网络支持](./underlay.md)。

安装前请参考[准备工作](./prepare.md)确认环境配置正确。

## 脚本安装

### 下载安装脚本

我们推荐在生产环境使用稳定的 release 版本，请使用下面的命令下载稳定版本安装脚本：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install.sh
```

如果对 master 分支的最新功能感兴趣，想使用下面的命令下载开发版本部署脚本：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/images/install.sh
```

### 修改配置参数

使用编辑器打开脚本，并修改下列变量为预期值：

```bash
REGISTRY="kubeovn"                     # 镜像仓库地址
VERSION="{{ variables.version }}"                      # 镜像版本/Tag
POD_CIDR="10.16.0.0/16"                # 默认子网 CIDR 不要和 SVC/NODE/JOIN CIDR 重叠
SVC_CIDR="10.96.0.0/12"                # 需要和 apiserver 的 service-cluster-ip-range 保持一致
JOIN_CIDR="100.64.0.0/16"              # Pod 和主机通信网络 CIDR，不要和 SVC/NODE/POD CIDR 重叠 
LABEL="node-role.kubernetes.io/master" # 部署 OVN DB 节点的标签
IFACE=""                               # 容器网络所使用的的宿主机网卡名，如果为空则使用 Kubernetes 中的 Node IP 所在网卡
TUNNEL_TYPE="geneve"                   # 隧道封装协议，可选 geneve, vxlan 或 stt，stt 需要单独编译 ovs 内核模块
```

可使用正则表达式来匹配网卡名，例如 `IFACE=enp6s0f0,eth.*`。

### 执行安装脚本

`bash install.sh`

等待安装完成。

## Helm Chart 安装

由于 Kube-OVN 的安装，需要设置一些参数，因此使用 Helm 安装 Kube-OVN，需要按照以下步骤执行。

### 查看节点 IP 地址

```bash
$ kubectl get node -o wide
NAME                     STATUS     ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
kube-ovn-control-plane   NotReady   control-plane   20h   v1.26.0   172.18.0.3    <none>        Ubuntu 22.04.1 LTS   5.10.104-linuxkit   containerd://1.6.9
kube-ovn-worker          NotReady   <none>          20h   v1.26.0   172.18.0.2    <none>        Ubuntu 22.04.1 LTS   5.10.104-linuxkit   containerd://1.6.9
```

### 去掉集群 master 节点污点

```bash
$ kubectl taint node kube-ovn-control-plane node-role.kubernetes.io/control-plane:NoSchedule-
node/kube-ovn-control-plane untainted
```

如果确定不需要在 master 节点调度业务 Pod，这一步可以跳过。

### 给节点添加 label

```bash
$ kubectl label node -lbeta.kubernetes.io/os=linux kubernetes.io/os=linux --overwrite
node/kube-ovn-control-plane not labeled
node/kube-ovn-worker not labeled

$ kubectl label node -lnode-role.kubernetes.io/control-plane kube-ovn/role=master --overwrite
node/kube-ovn-control-plane labeled

# 以下 label 用于 dpdk 镜像的安装，非 dpdk 情况，可以忽略
$ kubectl label node -lovn.kubernetes.io/ovs_dp_type!=userspace ovn.kubernetes.io/ovs_dp_type=kernel --overwrite
node/kube-ovn-control-plane labeled
node/kube-ovn-worker labeled
```

### 添加 Helm Repo 信息

```bash
$ helm repo add kubeovn https://kubeovn.github.io/kube-ovn/
"kubeovn" has been added to your repositories

$ helm repo list
NAME            URL
kubeovn         https://kubeovn.github.io/kube-ovn/

$ helm search repo kubeovn
NAME                CHART VERSION   APP VERSION DESCRIPTION
kubeovn/kube-ovn    0.1.0           1.12.0      Helm chart for Kube-OVN
```

### 执行 helm install 安装 Kube-OVN

Node0IP、Node1IP、Node2IP 参数分别为集群 master 节点的 IP 地址。其他参数的设置，可以参考 values.yaml 文件中变量定义。

```bash
# 单 master 节点环境安装
$ helm install kube-ovn kubeovn/kube-ovn --set MASTER_NODES=${Node0IP}

# 以上边的 node 信息为例，执行安装命令
$ helm install kube-ovn kubeovn/kube-ovn --set MASTER_NODES=172.18.0.3
NAME: kube-ovn
LAST DEPLOYED: Fri Mar 31 12:43:43 2023
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None

# 高可用集群安装
$ helm install kube-ovn kubeovn/kube-ovn --set MASTER_NODES=${Node0IP}\,${Node1IP}\,${Node2IP}
```
