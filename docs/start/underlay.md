# Underlay 网络安装

默认情况下 Kube-OVN 的默认子网使用 Geneve 对跨主机流量进行封装，在基础设施之上抽象出一层虚拟的 Overlay 网络。

对于希望容器网络直接使用物理网络地址段情况，可以将 Kube-OVN 的默认子网工作在 Underlay 模式，可以直接给容器分配物理网络中的地址资源，达到更好的性能以及和物理网络的连通性。

![topology](../static/vlan-topology.png)

## 功能限制
该模式下 Kube-OVN 网络表现和 Macvlan 类似，但相比 Macvlan 提供了地址管理，固定IP，服务发现，网络策略和 QoS 等功能。

但由于该模式下容器网络直接使用物理网络资源进行包转发，Overlay 模式下的 SNAT/EIP， 分布式网关/集中式网关等 L3 功能无法使用。

## 和 Macvlan 比较

Kube-OVN 的 Underlay 模式和 Macvlan 工作模式十分类似，在功能和性能上主要有以下几个区别：

1. 由于 Macvlan 的内核路径更短，并且不需要 OVS 对数据包进行处理，Macvlan 在吞吐量和延迟性能指标上表现会更好。
2. Kube-OVN 通过流表提供了 arp-proxy 功能，可以缓解大规模网络下的 arp 广播风暴风险。
3. 由于 Macvlan 工作在内核底层，会绕过宿主机的 netfilter，Service 和 NetworkPolicy 功能需要额外开发。Kube-OVN 通过 OVS 流表提供了 Service 和 NetworkPolicy 的能力。

## 硬件环境要求

在 Underlay 模式下， OVS 将会桥接一个节点网卡到 OVS 网桥，并将数据包直接通过该节点网卡对外发送，L2/L3 层面的转发能力需要依赖底层网络设备。
需要预先在底层网络设备配置对应的网关、Vlan 和安全策略等配置。

1. 对于 OpenStack 的 VM 环境，需要将对应网络端口的 `PortSecurity` 关闭。
2. 对于 VMware 的 vswtich 网络，需要将 `MAC Address Changes`, `Forged Transmits` 和 `Promiscuous Mode Operation` 设置为 `allow`。
3. 公有云，例如 AWS、GCE、阿里云等由于不支持用户自定义 Mac 无法支持 Underlay 模式网络。
4. 对于 Service 访问流量，Pod 会将数据包首先发送至网关，网关需要有能将数据包转发会本网段的能力。

对于管理网和容器网使用同一个网卡的情况下，Kube-OVN 会将网卡的 Mac 地址、IP 地址、路由以及 MTU 将转移或复制至对应的 OVS Bridge，
以支持单网卡部署 Underlay 网络。OVS Bridge 名称格式为 `br-PROVIDER_NAME`，`PROVIDER_NAME` 为 Provider 网络名称（默认为 provider）。

## 安装方式

### 部署时指定网络模式

该部署模式将默认子网设置为 Underlay 模式，所有未指定子网的 Pod 均会默认运行在 Underlay 网络中

#### 下载安装脚本
```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/release-1.10/dist/images/install.sh
```

#### 修改脚本中相应配置
```bash
NETWORK_TYPE          # 设置为 vlan
VLAN_INTERFACE_NAME   # 设置为宿主机上承担容器流量的网卡，例如 eth1
VLAN_ID               # 交换机所接受的 VLAN Tag，若设置为 0 则不做 VLAN 封装
POD_CIDR              # 设置为物理网络 CIDR， 例如 192.168.1.0/24
POD_GATEWAY           # 设置为物理网络网关，例如192.168.1.1
EXCLUDE_IPS           # 排除范围，避免容器网段和物理网络已用 IP 冲突，例如 192.168.1.1..192.168.1.100
```

#### 运行安装脚本
```bash
bash install.sh
```

### 通过 CRD 动态创建 Underlay 网络

该方式可在安装后动态的创建某个 Underlay 子网供 Pod 使用。

#### 创建 ProviderNetwork

创建如下 ProviderNetwork 并应用:

```yml
apiVersion: kubeovn.io/v1
kind: ProviderNetwork
metadata:
  name: net1
spec:
  defaultInterface: eth1
  customInterfaces:
    - interface: eth2
      nodes:
        - node1
  excludeNodes:
    - node2
```

**注意：ProviderNetwork 资源名称的长度不得超过 12。**

`defaultInterface` 为默认使用的节点网卡名称；`customInterfaces` 为可选项，可针对特定节点指定需要使用的网卡；`excludeNodes` 也是可选项，用于指定不桥接网卡的节点。

ProviderNetwork 创建成功后，各节点（除 excludeNodes 外）中会创建名为 br-net1（格式为 `br-NAME`）的 OVS 网桥，并将指定的节点网卡桥接至此网桥。

`excludeNodes` 中的节点会被添加 `net1.provider-network.ovn.kubernetes.io/exclude=true` 标签，其它节点会被添加如下标签：

| Key                                               | Value | 描述                                                 |
| ------------------------------------------------- | ----- | ---------------------------------------------------- |
| net1.provider-network.ovn.kubernetes.io/ready     | true  | 节点中的桥接工作已完成，ProviderNetwork 在节点中可用 |
| net1.provider-network.ovn.kubernetes.io/interface | eth1  | 节点中被桥接的网卡的名称                             |
| net1.provider-network.ovn.kubernetes.io/mtu       | 1500  | 节点中被桥接的网卡的 MTU                             |

> 如果节点网卡上已经配置了 IP，则 IP 地址和网卡上的路由会被转移至对应的 OVS 网桥。

#### 创建 VLAN

创建如下 VLAN 并应用：

```yml
apiVersion: kubeovn.io/v1
kind: Vlan
metadata:
  name: vlan1
spec:
  id: 0
  provider: net1
```

`id` 为 VLAN ID/Tag，`provider` 为需要使用的 ProviderNetwork 的名称。多个 VLAN 可以引用同一个 ProviderNetwork。

#### 创建 Subnet

示例如下：

```yml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: subnet1
spec:
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  vlan: vlan1
```

将 `vlan` 的值指定为需要使用的 VLAN 名称即可。多个 Subnet 可以引用同一个 VLAN。

## 容器创建
可按正常容器创建方式进行创建，查看容器 IP 是否在规定范围内，以及容器是否可以和物理网络互通。

如有固定 IP 需求，可参考 [Pod 固定 IP 和 Mac](../guide/static-ip-mac.md)

## 使用逻辑网关

对于物理网络不存在网关的情况，Kube-OVN 支持在 Underlay 模式的子网中配置使用逻辑网关。
若要使用此功能，设置子网的 `spec.logicalGateway` 为 `true` 即可：

```yml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: subnet1
spec:
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  vlan: vlan1
  logicalGateway: true
```

开启此功能后，Pod 不使用外部网关，而是使用 Kube-OVN 创建的逻辑路由器（Logical Router）。对于跨网段通信，由逻辑路由器进行转发。
