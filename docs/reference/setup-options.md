# 安装和配置选项

在[一键安装中](../start/one-step-install.md)我们使用默认配置进行安装，Kube-OVN 还支持更多
自定义配置，可在安装脚本中进行配置，或者之后更改各个组件的参数来进行配置。本文档将会介绍这些自定义选项
的作用，以及如何进行配置。

## 内置网络设置

Kube-OVN 在安装时会配置两个内置子网：

1. `default` 子网，作为 Pod 分配 IP 使用的默认子网，默认 CIDR 为 `10.16.0.0/16`，网关为 `10.16.0.1`。
2. `join` 子网，作为 Node 和 Pod 之间进行网络通信的特殊子网, 默认 CIDR 为 `100.64.0.0/16`，网关为 `100.64.0.1`。

在安装时可以通过安装脚本内的配置进行更改：

```bash
POD_CIDR="10.16.0.0/16"
POD_GATEWAY="10.16.0.1"
JOIN_CIDR="100.64.0.0/16"
EXCLUDE_IPS=""
```

`EXCLUDE_IP` 可设置 `POD_CIDR` 不进行分配的地址范围，格式为：`192.168.10.20..192.168.10.30`。

需要注意 Overlay 情况下这两个网络不能和已有的主机网络和 Service CIDR 冲突。

在安装后可以对这两个网络的地址范围进行修改请参考[修改默认子网](../ops/change-default-subnet.md)和[修改 Join 子网](../ops/change-join-subnet.md)。

## Service 网段配置

由于部分 `kube-proxy` 设置的 iptables 和路由规则会和 Kube-OVN 设置的规则产生交集，因此 Kube-OVN 需要知道
Service 的 CIDR 来正确设置对应的规则。

在安装脚本中可以通过修改：

```bash
SVC_CIDR="10.96.0.0/12"  
```

来进行配置。

也可以在安装后通过修改 `kube-ovn-controller` Deployment 的参数：

```yaml
args:
- --service-cluster-ip-range=10.96.0.0/12
```

来进行修改。

## Overlay 网卡选择

在节点存在多块网卡的情况下，Kube-OVN 默认会选择 Kubernetes Node IP 对应的网卡作为容器间跨节点通信的网卡并建立对应的隧道。

如果需要选择其他的网卡建立容器隧道，可以在安装脚本中修改：

```bash
IFACE=eth1
```

该选项支持以逗号分隔的正则表达式，例如 `ens[a-z0-9]*,eth[a-z0-9]*`。

安装后也可通过修改 `kube-ovn-cni` DaemonSet 的参数进行调整：

```yaml
args:
- --iface=eth1
```

如果每台机器的网卡名均不同，且没有固定规律，可以使用节点 annotation `ovn.kubernetes.io/tunnel_interface`
进行每个节点的逐一配置，拥有该 annotation 节点会覆盖 `iface` 的配置，优先使用 annotation。

```bash
kubectl annotate node no1 ovn.kubernetes.io/tunnel_interface=ethx
```

如需为不同子网指定不同的封装网卡，请参考 [Overlay 网络封装网卡选择](../advance/node-network.md)。

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
ENABLE_MIRROR=true
```

也可在安装后通过修改 `kube-ovn-cni` DaemonSet 的参数方式进行调整:

```yaml
args:
- --enable-mirror=true
```

流量镜像的能力在默认安装中为关闭，如果需要细粒度的流量镜像或需要将流量镜像到额外的网卡请参考[容器网络流量镜像](../guide/mirror.md)。

## LB 开启设置

在 Underlay 的场景中，kube-proxy 无法截获容器网络流量，因此无法实现 Service 转发的功能。在这种情况下可以通过开启 OVN 内置的 L2 LB 的能力来实现 ClusterIP 的转发能力。在无需 Service 转发能力的场景下可以通过关闭 LB 能力来获得更好的性能。需要注意的事该功能只实现了容器网络的 ClusterIP 转发能力，无法替代 kube-proxy 的全部能力，不能替代 kube-proxy。

该功能可以在安装脚本中进行配置：

```bash
ENABLE_LB=false
```

或者在安装后通过更改 `kube-ovn-controller` Deployment 的参数进行配置：

```yaml
args:
- --enable-lb=false
```

LB 的功能在默认安装中为开启。

从 Kube-OVN v1.12.0 版本开始，在 subnet crd 定义中增加了 spec 字段 `enableLb`，将 Kube-OVN 的 LB 功能迁移到子网层级，可以基于不同的子网分别设置是否开启 LB 功能。`kube-ovn-controller` Deployment 中的 `enable-lb` 参数作为全局参数，控制是否创建 load-balancer 记录，子网中新增的 `enableLb` 参数用于控制子网是否关联 load-balancer 记录。之前版本升级到 v1.12.0 之后，子网 `enableLb` 参数会自动继承原有的全局开关参数取值。

## NetworkPolicy 开启设置

Kube-OVN 使用 OVN 中的 ACL 来实现 NetworkPolicy，用户可以选择关闭 NetworkPolicy 功能
或者使用 Cilium Chain 的方式利用 eBPF 实现 NetworkPolicy，
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
网络时的检查消耗，在大规模集群环境下可以提升处理速度。

该功能可在安装脚本中进行配置：

```bash
ENABLE_EIP_SNAT=false
```

或者在安装后通过更改 `kube-ovn-controller` Deployment 的参数进行配置：

```yaml
args:
- --enable-eip-snat=false
```

EIP 和 SNAT 的能力在默认安装中为开启。该功能的相关使用和其他可配参数请参考 [EIP 和 SNAT 配置](../guide/eip-snat.md)。

## Load Balancer 类型 Service 支持开启设置

默认 VPC 下可通过开启该选项来支持 Load Balancer 类型 Service。该功能的相关使用和其他可配参数请参考 [LoadBalancer 类型 Service](../guide/loadbalancer-service.md)。

该功能默认关闭，可在安装脚本中进行配置：

```bash
ENABLE_LB_SVC=true
```

或者在安装后通过更改 `kube-ovn-controller` Deployment 的参数进行配置：

```yaml
args:
- --enable-lb-svc=true
```

## 集中式网关 ECMP 开启设置

集中式网关支持主备和 ECMP 两种高可用模式，如果需要启用 ECMP 模式，
需要更改 `kube-ovn-controller` Deployment 的参数进行配置:

```yaml
args:
- --enable-ecmp=true 
```

从 Kube-OVN v1.12.0 版本开始，在 subnet crd 定义中增加了 spec 字段 `enableEcmp`，将集中式子网 ECMP 开关控制迁移到子网层级，可以基于不同的子网分别设置是否开启 ECMP 模式。原有的 `kube-ovn-controller` Deployment 中的 `enable-ecmp` 参数不再使用。之前版本升级到 v1.12.0 之后，子网开关会自动继承原有的全局开关参数取值。

集中式网关默认安装下为主备模式，更多网关相关内容请参考[子网使用](../guide/subnet.md)。

## Kubevirt VM 固定地址开启设置

针对 Kubevirt 创建的 VM 实例，`kube-ovn-controller` 可以按照类似 StatefulSet Pod 的方式进行 IP 地址分配和管理。
以达到 VM 实例在生命周期内启停，升级，迁移等操作过程中地址固定不变，更符合虚拟化合用户的实际使用体验。

该功能在 1.10.6 后默认开启，若要关闭此功能，需要在 `kube-ovn-controller` Deployment 的启动命令中设置如下参数：

```yaml
args:
- --keep-vm-ip=false
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
...
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

不同协议在实际使用中的区别请参考[隧道协议说明](tunnel-protocol.md)。

## SSL 设置

OVN DB 的 API 接口支持 SSL 加密来保证连接安全，如要开启可调整安装脚本中的如下参数:

```bash
ENABLE_SSL=true
```

SSL 功能默认安装下为关闭模式。

## 跳过 conntrack 的目的 CIDR 列表

针对部分需要绕过 conntrack 处理的目的网段（例如已通过其他方式做 NAT/会话保持的旁路流量），可在安装脚本或 `kube-ovn-controller` 启动参数中配置跳过列表，多个 CIDR 以逗号分隔：

```bash
SKIP_CONNTRACK_DST_CIDRS="10.10.0.0/16,fd00:10::/64"
```

```yaml
args:
- --skip-conntrack-dst-cidrs=10.10.0.0/16,fd00:10::/64
```

默认为空。

## 启用 OVN IPSec

启用后 Kube-OVN 会通过 OVN 内置的 IPSec 能力对节点间的 Geneve/Vxlan/STT 隧道进行加密，并自动签发证书。

```bash
ENABLE_OVN_IPSEC=true
```

控制器与 daemon 均需要打开该开关：

```yaml
args:
- --enable-ovn-ipsec=true
```

详细配置参考 [OVN IPSec](../advance/ovn-ipsec.md)。

## AdminNetworkPolicy / DNS 名称解析支持

启用 AdminNetworkPolicy（ANP/CNP）以及基于 DNS 名称的访问控制（依赖 `DNSNameResolver` CRD）：

```bash
ENABLE_ANP=true
ENABLE_DNS_NAME_RESOLVER=true
```

```yaml
args:
- --enable-anp=true
- --enable-dns-name-resolver=true
```

详细使用见[基于域名的访问控制](../guide/egress-firewall.md)。

## VPC NAT Gateway 总开关

控制是否启用 VPC NAT Gateway 相关 controller。默认开启：

```bash
ENABLE_NAT_GW=true
```

或在 `ovn-vpc-nat-gw-config` ConfigMap 中通过 `enable-vpc-nat-gw` 字段控制运行时开关。

## ovn-northd 线程数

针对大规模集群，可调整 `ovn-northd` 处理线程数以加速增量计算：

```bash
OVN_NORTHD_N_THREADS=4
```

默认 1。需结合节点 CPU 资源评估。

## NetworkPolicy 执行模式

Kube-OVN 支持 `standard`/`lax` 两种 NetworkPolicy 执行模式，可通过下列方式全局配置默认值：

```bash
NP_ENFORCEMENT=standard
```

```yaml
args:
- --np-enforcement=standard
```

也可在单条 NetworkPolicy 上通过 `ovn.kubernetes.io/network_policy_enforcement` annotation 覆盖。详见 [NetworkPolicy 支持](../guide/networkpolicy.md)。

## VXLAN 关闭 TX checksum offload

部分网卡 VXLAN 隧道封装存在 checksum offload 兼容问题，可关闭：

```bash
SET_VXLAN_TX_OFF=true
```

```yaml
args:
- --set-vxlan-tx-off=true
```

## KubeVirt 实时迁移优化

启用后控制器会针对 KubeVirt 实时迁移过程优化端口绑定切换，减少迁移瞬时丢包。默认开启：

```bash
ENABLE_LIVE_MIGRATION_OPTIMIZE=true
```

## OVN LB 偏好本地 endpoint

启用后 OVN 内置 LoadBalancer 会偏好同节点的 endpoint，配合 `externalTrafficPolicy=Local` 使用：

```bash
ENABLE_OVN_LB_PREFER_LOCAL=true
```

```yaml
args:
- --enable-ovn-lb-prefer-local=true
```

## 外部网关 ConfigMap 命名空间

集中式外部网关相关 ConfigMap（如 `external-gw-config`）默认在 `kube-system`。可通过下列参数迁移到其他命名空间：

```bash
EXTERNAL_GATEWAY_CONFIG_NS=kube-system
```

## Non-Primary CNI 模式

在该模式下 Kube-OVN 仅作为 attachment network 提供方，不再分配 Pod 主网络 IP，主网络由其他 CNI 负责。controller 与 daemon 均需要打开此开关：

```yaml
args:
- --non-primary-cni-mode=true
```

或通过 Helm `cni_conf.NON_PRIMARY_CNI=true`（chart v1）/`cni.nonPrimaryCNI=true`（chart v2）配置。详见 [Non-Primary CNI 模式](../start/non-primary-mode.md)。

## 绑定本地 ip

kube-ovn-controller/kube-ovn-cni/kube-ovn-monitor 这些服务支持绑定本地 ip，该功能设计原因主要是因为某些场景下出于安全考虑不允许服务绑定 0.0.0.0 （比如该服务部署在某个对外网关上，外部用户可以直接通过公网 ip 并指定端口去访问到该服务），该功能默认是打开的，由安装脚本中如下参数控制：

```bash
ENABLE_BIND_LOCAL_IP=true
```

以 kube-ovn-monitor 为例，开启功能后会把服务绑定本地的 pod ip 如下：

```bash
# netstat -tunlp |grep kube-ovn
tcp        0      0 172.18.0.5:10661        0.0.0.0:*               LISTEN      2612/./kube-ovn-mon
```

安装后也可通过修改服务的 deployment 或者 daemonSet 的环境变量参数进行调整：

```yaml
env:
- name: ENABLE_BIND_LOCAL_IP
  value: "false"
```
