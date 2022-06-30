# VPC Peering

VPC 互联提供了一种将两个 VPC 网络通过逻辑路由打通的机制，从而使两个 VPC 内的工作负载可以像在同一个私有网络一样，
通过私有地址相互访问，无需通过外部网关进行 NAT 转发。

## 前提条件
1. 该功能只适用于用户自定义 VPC。
2. 为了避免路由重叠两个 VPC 内的子网 CIDR 不能重叠。
3. 目前只支持两个 VPC 的互联，更多组 VPC 之间的互联暂不支持。

## 使用方式

首先创建两个不互联的 VPC，每个 VPC 下各有一个 Subnet，Subnet 的 CIDR 互不重叠。

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-1
spec: {}
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net1
spec:
  vpc: vpc-1
  cidrBlock: 10.0.0.0/16
---
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-2
spec: {}
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net2
spec:
  vpc: vpc-2
  cidrBlock: 172.31.0.0/16
```

在每个 VPC 内分别增加 `vpcPeerings` 和对应的静态路由：

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-1
spec: 
  vpcPeerings:
    - remoteVpc: vpc-2
      localConnectIP: 169.254.0.1/30
  staticRoutes:
    - cidr: 172.31.0.0/16
      nextHopIP: 169.254.0.2
      policy: policyDst
---
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-1
spec:
  vpcPeerings:
    - remoteVpc: vpc-2
      localConnectIP: 169.254.0.2/30
  staticRoutes:
    - cidr: 10.0.0.0/16
      nextHopIP: 169.254.0.1
      policy: policyDst
```

- `remoteVpc`: 互联的另一个 VPC 的名字。
- `localConnectIP`: 作为互联端点的 IP 地址和 CIDR，注意两端 IP 应属于同一 CIDR，且不能和已有子网冲突。
- `cidr`：另一端 Subnet 的 CIDR。
- `nextHopIP`：互联 VPC 另一端的 `localConnectIP`。
