# 一键安装

Kube-OVN 提供了一键安装脚本和 Charts 仓库，可以帮助你快速安装一个高可用，生产就绪的 Kube-OVN 容器网络，默认部署为 Overlay 类型网络。

如果默认网络需要搭建 Underlay/Vlan 网络，请参考 [Underlay 网络支持](./underlay.md)，更多安装配置请参考 [安装和配置选项](../reference/setup-options.md)。

安装前请参考[准备工作](./prepare.md)确认环境配置正确。如果想完全删除 Kube-OVN 请参考[卸载](./uninstall.md)。

## 脚本安装

### 下载安装脚本

我们推荐在生产环境使用稳定的 release 版本，请使用下面的命令下载稳定版本安装脚本：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/refs/tags/{{ variables.version }}/dist/images/install.sh
```

如果对 master 分支的最新功能感兴趣，请使用下面的命令下载开发版本部署脚本：

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
IFACE=""                               # 容器网络所使用的宿主机网卡名，如果为空则使用 Kubernetes 中的 Node IP 所在网卡
TUNNEL_TYPE="geneve"                   # 隧道封装协议，可选 geneve, vxlan 或 stt，stt 需要单独编译 ovs 内核模块
```

可使用正则表达式来匹配网卡名，例如 `IFACE=enp6s0f0,eth.*`。

### 执行安装脚本

> 脚本执行需要有 root 权限

`bash install.sh`

等待安装完成。

### 升级

当使用该脚本进行 Kube-OVN 升级时需要注意以下几点：

1. 脚本中的 `[Step 4/6]` 会重启所有容器网络 Pod。在升级过程中，应**跳过此步骤或在脚本中将其注释掉**，以避免不必要的重启。
2. **重要提示：** 如果在 Kube-OVN 运行过程中对参数进行过调整，**务必在升级前将这些变更更新到脚本中**。否则，之前的参数调整将**被还原**。

## Helm Chart 安装

由于 Kube-OVN 的安装需要设置一些参数，因此使用 Helm 安装 Kube-OVN 需要按照以下步骤执行。

### 查看节点 IP 地址

```bash
# kubectl get node -o wide
NAME                     STATUS     ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
kube-ovn-control-plane   NotReady   control-plane   20h   v1.26.0   172.18.0.3    <none>        Ubuntu 22.04.1 LTS   5.10.104-linuxkit   containerd://1.6.9
kube-ovn-worker          NotReady   <none>          20h   v1.26.0   172.18.0.2    <none>        Ubuntu 22.04.1 LTS   5.10.104-linuxkit   containerd://1.6.9
```

### 给节点添加 label

```bash
# kubectl label node -lbeta.kubernetes.io/os=linux kubernetes.io/os=linux --overwrite
node/kube-ovn-control-plane not labeled
node/kube-ovn-worker not labeled

# kubectl label node -lnode-role.kubernetes.io/control-plane kube-ovn/role=master --overwrite
node/kube-ovn-control-plane labeled

# 以下 label 用于 dpdk 镜像的安装，非 dpdk 情况，可以忽略
# kubectl label node -lovn.kubernetes.io/ovs_dp_type!=userspace ovn.kubernetes.io/ovs_dp_type=kernel --overwrite
node/kube-ovn-control-plane labeled
node/kube-ovn-worker labeled
```

### 添加 Helm Repo 信息

```bash
# helm repo add kubeovn https://kubeovn.github.io/kube-ovn/
"kubeovn" has been added to your repositories

# helm repo list
NAME            URL
kubeovn         https://kubeovn.github.io/kube-ovn/

# helm repo update kubeovn
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "kubeovn" chart repository
Update Complete. ⎈Happy Helming!⎈

# helm search repo kubeovn
NAME                    CHART VERSION   APP VERSION     DESCRIPTION
kubeovn/kube-ovn        {{ variables.version }}        {{ variables.version }}         Helm chart for Kube-OVN
```

### 执行 helm install 安装 Kube-OVN

Chart 参数的设置，可以参考 `values.yaml` 文件中变量定义。

```bash
# helm install kube-ovn kubeovn/kube-ovn --wait -n kube-system --version {{ variables.version }}
NAME: kube-ovn
LAST DEPLOYED: Thu Apr 24 08:30:13 2025
NAMESPACE: kube-system
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

### 升级

**重要提示：** 与脚本升级类似，请确保在**使用 Helm 升级前**，所有参数调整都已更新到相应的 `values.yaml` 文件中。否则，之前的参数调整将**被还原**。

```bash
helm upgrade -f values.yaml kube-ovn kubeovn/kube-ovn --wait -n kube-system --version {{ variables.version }}
```
