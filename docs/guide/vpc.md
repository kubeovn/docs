# VPC 使用

Kube-OVN 支持多租户隔离级别的 VPC 网络。不同 VPC 网络相互独立，可以分别配置 Subnet 网段，
路由策略，安全策略，出网网关，EIP 等配置。

> VPC 主要用于有多租户网络强隔离的场景，部分常见 Kubernetes 网络假设在多租户网络下存在冲突。
> 例如节点和 Pod 互访，NodePort 功能，基于网络访问的健康检查和 DNS 能力在多租户网络场景暂不支持。
> 为了方便常见 Kubernetes 的使用场景，Kube-OVN 默认 VPC 做了特殊设计，该 VPC 下的 Subnet 
> 可以满足 Kubernetes 规范。用户自定义 VPC 支持本文档介绍的静态路由，EIP 和 NAT 网关等功能。
> 常见隔离需求可通过默认 VPC 下的网络策略和子网 ACL 实现，在使用自定义 VPC 前请明确是否需要
> VPC 级别的隔离，以及自定义 VPC 下的限制。

## 创建自定义 VPC

创建两个 VPC：

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  namespaces:
  - ns1
---
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-2
spec: {}
```
- `namespaces` 可以限定只有哪些 Namespace 可以使用当前 VPC，若为空则不限定。

创建两个子网，分属两个不同的 VPC 并有相同的 CIDR:

```yaml
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net1
spec:
  vpc: test-vpc-1
  cidrBlock: 10.0.1.0/24
  protocol: IPv4
  namespaces:
    - ns1
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net2
spec:
  vpc: test-vpc-2
  cidrBlock: 10.0.1.0/24
  protocol: IPv4
  namespaces:
    - ns2
```

分别在两个 Namespace 下创建 Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/logical_switch: net1
  namespace: ns1
  name: vpc1-pod
---
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/logical_switch: net2
  namespace: ns2
  name: vpc2-pod
```

运行成功后可观察两个 Pod 地址属于同一个 CIDR，但由于运行在不同的租户 VPC，两个 Pod 无法相互访问。

## 创建 VPC 网关

> 自定义 VPC 下的子网不支持默认 VPC 下的分布式网关和集中式网关

VPC 内容器访问外部网络需要通过 VPC 网关，VPC 网关可以打通物理网络和租户网络，并提供
浮动 IP，SNAT 和 DNAT 功能。

VPC 网关功能依赖 Multus-CNI 的多网卡功能，安装请参考 [multus-cni](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/quickstart.md)

### 配置外部网络

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: ovn-vpc-external-network
spec:
  protocol: IPv4
  provider: ovn-vpc-external-network.kube-system
  cidrBlock: 192.168.0.0/24
  gateway: 192.168.0.1  # IP address of the physical gateway
  excludeIps:
  - 192.168.0.1..192.168.0.10
---
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: ovn-vpc-external-network
  namespace: kube-system
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "macvlan",
      "master": "eth1",
      "mode": "bridge",
      "ipam": {
        "type": "kube-ovn",
        "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
        "provider": "ovn-vpc-external-network.kube-system"
      }
    }'
```

- 该 Subnet 用来管理可用的外部地址，请和网络管理沟通给出可用的物理段 IP。
- VPC 网关使用 Macvlan 做物理网络配置，`NetworkAttachmentDefinition` 的 `master` 需为对应物理网路网卡的网卡名。
- `provider` 格式为 `<NetworkAttachmentDefinition Name>.<NetworkAttachmentDefinition Namespace>`

### 开启 VPC 网关功能

VPC 网关功能需要通过 `kube-system` 下的 `ovn-vpc-nat-gw-config` 开启：
```yaml
kind: ConfigMap
apiVersion: v1
metadata:
  name: ovn-vpc-nat-gw-config
  namespace: kube-system
data:
  image: 'kubeovn/vpc-nat-gateway:v1.10.0' 
  enable-vpc-nat-gw: 'true'
  nic: eth1
```

- `image`: 网关 Pod 所使用的镜像
- `enable-vpc-nat-gw`： 控制是否启用 VPC 网关功能
- `nic`: Macvlan master 网卡名

### 创建 VPC 网关并配置默认路由

```yaml
kind: VpcNatGateway
apiVersion: kubeovn.io/v1
metadata:
  name: gw1
spec:
  vpc: test-vpc-1
  subnet: net1
  lanIp: 10.0.1.254
  selector:
    - "kubernetes.io/hostname: kube-ovn-worker"
    - "kubernetes.io/os: linux"
  staticRoutes:
    - cidr: 0.0.0.0/0
      nextHopIP: 10.0.1.254
      policy: policyDst
```

- `subnet`： 为 VPC 内某个 Subnet 名，VPC 网关 Pod 会在该子网下用 `lanIp` 来连接租户网络
- `lanIp`：`subnet` 内某个未被使用的 IP，VPC 网关 Pod 最终会使用该 Pod
- `selector`: VPC 网关 Pod 的节点选择器
- `nextHopIP`：需和 `lanIp` 相同

### 创建 EIP

EIP 为外部网络段的某个 IP 分配给 VPC 网关后可进行浮动IP，SNAT 和 DNAT 操作

随机分配一个地址给 EIP：
```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-random
spec:
  natGwDp: gw1
```

固定 EIP 地址分配：

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  natGwDp: gw1
  v4ip: 10.0.1.111
```

### 创建 DNAT 规则
```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eipd01
spec:
  natGwDp: gw1
  
---
kind: IptablesDnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: dnat01
spec:
  eip: eipd01 
  externalPort: '8888'
  internalIp: 10.0.1.10
  internalPort: '80'
  protocol: tcp
```

### 创建 SNAT 规则
```yaml
---
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eips01
spec:
  natGwDp: gw1
---
kind: IptablesSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat01
spec
  eip: eips01
  internalCIDR: 10.0.1.0/24
```

### 创建浮动 IP
```yaml
---
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eipf01
spec:
  natGwDp: gw1

---
kind: IptablesFIPRule
apiVersion: kubeovn.io/v1
metadata:
  name: fip01
spec:
  eip: eipf01
  internalIp: 10.0.1.5
```

## 自定义路由

在自定义 VPC 内，用户可以自定义网络内部的路由规则，结合网关实现更灵活的转发。
Kube-OVN 支持静态路由和更为灵活的策略路由。

### 静态路由
```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  staticRoutes:
    - cidr: 0.0.0.0/0
      nextHopIP: 10.0.1.254
      policy: policyDst
    - cidr: 172.31.0.0/24
      nextHopIP: 10.0.1.253
      policy: policySrc
```

- `policy`: 支持目的地址路由 `policyDst` 和源地址路由 `policySrc`。
- 当路由规则存在重叠时，CIDR 掩码较长的规则优先级更高，若掩码长度相同则目的地址路由优先于源地址路由。

### 策略路由

针对静态路由匹配的流量，可通过策略路由进行更细粒度的控制。策略路由提供了更精确的匹配规则，优先级控制
和更多的转发动作。该功能为 OVN 内部逻辑路由器策略功能的一个对外暴露，更多使用信息请参考 [Logical Router Policy](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#Logical_Router_Policy_TABLE)

简单示例如下：
```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  policyRoutes:
    - action: drop
      match: ip4.src==10.0.1.0/24 && ip4.dst==10.0.1.250
      priority: 11
    - action: reroute
      match: ip4.src==10.0.1.0/24
      nextHopIP: 10.0.1.252
      priority: 10
```
