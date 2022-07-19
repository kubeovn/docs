# 一键安装

Kube-OVN 提供了一键安装脚本，可以帮助你快速安装一个高可用，生产就绪的 Kube-OVN 容器网络，默认部署为 Overlay 类型网络。

如果默认网络需要搭建 Underlay/Vlan 网络，请参考 [Underlay 网络支持](./underlay.md)。

安装前请参考[准备工作](./prepare.md)确认环境配置正确。

## 下载安装脚本

我们推荐在生产环境使用稳定的 release 版本，请使用下面的命令下载稳定版本安装脚本：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install.sh
```

如果对 master 分支的最新功能感兴趣，想使用下面的命令下载开发版本部署脚本：

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/images/install.sh
```

## 修改配置参数

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

## 执行安装脚本

`bash install.sh`

等待安装完成。
