# 安装和配置选项

在[一键安装中](../start/one-step-install.md)我们使用默认配置进行安装，Kube-OVN 还支持更多
自定义配置，可在安装脚本中进行配置或者之后更改各个组件的参数来进行配置。本文档将会介绍这些自定义选项
作用，以及如何进行配置。

## 内置网络设置

Kube-OVN 在安装时会配置两个内置子网：

1. default 子网，作为 Pod 分配 IP 使用的默认子网，默认 cidr 为 10.16.0.0/16，网关为 10.16.0.1
2. node 子网，作为 Node 和 Pod 之间进行网络通信的特殊子网, 默认 cidr 为 100.64.0.0/16，网关为 100.64.0.1

在安装时可以通过安装脚本内的配置进行更改

```bash
POD_CIDR="10.16.0.0/16"
POD_GATEWAY="10.16.0.1"
JOIN_CIDR="100.64.0.0/16"
EXCLUDE_IPS=""
```

`EXCLUDE_IP` 可设置 `POD_CIDR` 不进行分配的地址范围，格式为：`192.168.10.20..192.168.10.30`

需要注意 Overlay 情况下这两个网络不能和已有的主机网络和 Service CIDR 冲突。

在安装后可以对这两个网络的地址范围进行修改请参考[修改默认子网](../ops/change-default-subnet.md)和[修改 Join 子网](../ops/change-join-subnet.md)

## Service 网段配置

由于部分 kube-proxy 设置的 iptables 和路由规则会和 Kube-OVN 设置的规则产生交集，Kube-OVN 需要知道
Service 的 CIDR 来正确设置对应的规则。

在安装脚本中可以通过修改：
```bash
SVC_CIDR="10.96.0.0/12"  
```
来进行配置。

也可以在安装后通过修改 `kube-ovn-controller` Deployment 的参数：
```yaml
args:
--service-cluster-ip-range=10.96.0.0/12
```
来进行修改。

## Overlay 网卡选择

在节点存在多块网卡的情况下，Kube-OVN 默认会选择 Kubernetes Node IP 对应的网卡作为容器间跨节点通信的网卡并建立对应的隧道。

如果需要选择其他的网卡建立容器隧道，可以在安装脚本中修改：
```bash
IFACE=eth1
```
该选项支持以逗号所分隔正则表达式,例如`ens[a-z0-9]*,eth[a-z0-9]*`

安装后也可通过修改 `kube-ovn-cni` DaemonSet 的参数进行调整：
```yaml
args:
  - --iface=eth1
```

如果每台机器的网卡名均不同，且没有固定规律，可以使用节点 annotation `ovn.kubernetes.io/tunnel_interface`
进行每个节点的逐一配置，有该 annotation 节点会覆盖 `iface` 的配置，优先使用 annotation
```bash
kubectl annotate node no1 ovn.kubernetes.io/tunnel_interface=ethx
```

## MTU 设置

由于 Overlay 封装需要占据额外的空间，Kube-OVN 在创建容器网卡时会根据选择网卡的 MTU 进行容器网卡的 MTU 调整，
默认情况下 Overlay 子网下 Pod 网卡 MTU 为主机网卡 MTU - 100，Underlay 子网下，Pod 网卡和主机网卡有相同 MTU。

如果需要调整 Overlay 子网下 MTU 的大小，可以修改 `kube-ovn-cni` DaemonSet 的参数：
```yaml
args:
- --mtu=1333
```

## 全局流量镜像开启设置

在开启全局流量镜像的情况下，Kube-OVN 会在每个节点上创建一块 `mirror0` 的虚拟网卡，复制当前机器所有容器网络流量到该网卡上，
用户可以通过 tcpdump 及其他工具进行流量分析，该功能可以在安装脚本中通过下面的配置开启：
```bash
ENABLE_MIRROR=tue
```

也可在安装后通过修改 `kube-ovn-cni` DaemonSet 的参数方式进行调整:
```yaml
args:
- --enable-mirror=true
```

流量镜像的能力在默认安装中为关闭，如果需要细粒度的流量镜像或需要将流量镜像到额外的网卡请参考[容器网络流量镜像](mirror.md)

## LB 开启设置

Kube-OVN 使用 OVN 中的 L2 LB 来实现 Service 转发，在 Overlay 场景中，用户可以选择使用 Kube-Proxy 来完成 Service 流量转发,
也可以选择使用 Cilium Chain 的方式利用 eBPF 实现 Service 达到更好的性能，在这种情况下可以关闭 Kube-OVN 的 LB 
以达到控制面和数据面更好的性能。

该功能可以在安装脚本中进行配置：
```bash
ENABLE_LB=false
```

或者在安装后通过更改 `kube-ovn-controller` Deployment 的参数进行配置：
```yaml
args:
- --enable-lb=false
```

LB 的能力在默认安装中为开启。

## NetworkPolicy 开启设置

Kube-OVN 使用 OVN 中的 ACL 来实现 NetworkPolicy，用户可以选择不需要使用 NetworkPolicy 
或者使用 Cilium Chain 的方式利用 eBPF 实现 NetworkPolicy ，
在这种情况下可以关闭 Kube-OVN 的 NetworkPolicy 功能以达到控制面和数据面更好的性能。

该功能可以在安装脚本中进行配置：
```bash
ENABLE_NP=false
```

或者在安装后通过更改 `kube-ovn-controller` Deployment 的参数进行配置：
```yaml
args:
- --enable-np=false
```

NetworkPolicy 的能力在默认安装中为开启。

## EIP 和 SNAT 开启设置

默认网络下如果无需使用 EIP 和 SNAT 的能力，可以选择关闭相关功能，以减少 `kube-ovn-controller` 在创建和更新
网络时的检查消耗，在大规模集群环境下可以提升处理速度，

该功能可在安装脚本中进行配置：
```bash
ENABLE_EIP_SNAT=false
```

或者在安装后通过更改 `kube-ovn-controller` Deployment 的参数进行配置：
```yaml
args:
  - --enable-eip-snat=false
```

EIP 和 SNAT 的能力在默认安装中为开启。该功能的相关使用和其他可配参数请参考[EIP 和 SNAT 配置](./eip-snat.md)

## 集中式网关 ECMP 开启设置

集中式网关支持主备和 ECMP 两种高可用模式，如果需要启用 ECMP 模式，
需要更改 `kube-ovn-controller` Deployment 的参数进行配置:
```yaml
args:
- --enable-ecmp=true 
```

集中式网关默认安装下为主备模式，更多网关相关内容请参考[子网使用](./subnet.md)

## Kubevirt VM 固定地址开启设置

针对 Kubevirt 创建的 VM 实例，`kube-ovn-controller` 可以按照类似 StatefulSet Pod 的方式进行 IP 地址分配和管理。
以达到 VM 实例在生命周期内启停，升级，迁移等操作过程中地址固定不变，更符虚拟化合用户的实际使用体验。

该功能默认关闭，若要使用此功能，需要在 `kube-ovn-controller` Deployment 的启动命令中开启如下参数：
```yaml
args:
- --keep-vm-ip=true
```

## CNI 配置相关设置

Kube-OVN 默认会在 `/opt/cni/bin` 目录下安装 CNI 执行文件，在 `/etc/cni/net.d` 目录下安装 CNI 配置文件 `01-kube-ovn.conflist`。
如果需要更改安装位置和 CNI 配置文件的优先级，可以通过安装脚本的下列参数进行调整：
```bash
CNI_CONF_DIR="/etc/cni/net.d"
CNI_BIN_DIR="/opt/cni/bin"
CNI_CONFIG_PRIORITY="01"
```

或者在安装后更改 `kube-ovn-cni` DaemonSet 的 Volume 挂载和启动参数：
```yaml
volumes:
- name: cni-conf
  hostPath:
    path: "/etc/cni/net.d"
- name: cni-bin
  hostPath:
    path:"/opt/cni/bin"

args:
- --cni-conf-name=01-kube-ovn.conflist
```

## 隧道类型设置

Kube-OVN 默认 Overlay 的封装模式为 Geneve，如果想更换为 Vxlan 或 STT，可以通过安装脚本的下列参数进行调整：
```bash
TUNNEL_TYPE="vxlan"
```

或者在安装后更改 `ovs-ovn` DaemonSet 的环境变量：
```yaml
env:
- name: TUNNEL_TYPE
  value: "vxlan"
```

如果需要使用 STT 隧道需要额外编译 ovs 的内核模块，请参考[性能调优](../advance/performance-tuning.md)。

不同协议在实际使用中的区别请参考[隧道协议说明](../reference/tunnel-protocol.md)。

## SSL 设置
OVN DB 的 API 接口支持 SSL 加密来保证连接安全，如要开启可调整安装脚本中的如下参数:
```bash
ENABLE_SSL=true
```

SSL 功能默认安装下为关闭模式。
