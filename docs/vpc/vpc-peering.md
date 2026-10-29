# VPC 互联

VPC 互联提供了一种将两个 VPC 网络通过逻辑路由打通的机制，从而使两个 VPC 内的工作负载可以像在同一个私有网络一样，
通过私有地址相互访问，无需通过外部网关进行 NAT 转发。

## 前提条件

1. 该功能只适用于用户自定义 VPC。
2. 为了避免路由重叠两个 VPC 内的子网 CIDR 不能重叠。
3. 目前只支持两个 VPC 的互联，更多组 VPC 之间的互联暂不支持。
4. 每个 `vpcPeerings` 条目都必须设置 `localConnectIP`，填写一个或多个带掩码的端点 IP 地址和 CIDR，多个值用逗号分隔，例如 `169.254.0.1/30` 或 `169.254.0.1/30,fd00::1/64`。每个端点的 CIDR 应与远端对应端点匹配，且不应与已有子网冲突。

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
  name: vpc-2
spec:
  vpcPeerings:
    - remoteVpc: vpc-1
      localConnectIP: 169.254.0.2/30
  staticRoutes:
    - cidr: 10.0.0.0/16
      nextHopIP: 169.254.0.1
      policy: policyDst
```

- `remoteVpc`: 互联的另一个 VPC 的名字。
- `localConnectIP`: 必填，作为互联端点的一个或多个 IP 地址和 CIDR，多个值用逗号分隔，例如 `169.254.0.1/30` 或 `169.254.0.1/30,fd00::1/64`。每个端点的 CIDR 应与远端对应端点匹配，且不应与已有子网冲突。
- `cidr`：另一端 Subnet 的 CIDR。
- `nextHopIP`：互联 VPC 另一端的 `localConnectIP`。

### 参数校验

创建或更新 VPC 时，admission webhook 会校验每个 peering 条目的 `localConnectIP`。留空时请求会被拒绝，并返回类似以下错误：

```text
localConnectIP is required for vpc peering with vpc-2, e.g. 169.254.0.1/30
```

非空值还必须是有效的 CIDR，逗号分隔的每个值都会分别校验；校验失败时不会创建互联逻辑路由端口。如果 admission webhook 被禁用，VPC controller 在 reconcile 时会执行相同的必填和 CIDR 校验并停止本次处理，因此必须在每个条目中显式填写 `localConnectIP`。

分别在两个 Subnet 下创建 Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/logical_switch: net1
  name: vpc-1-pod
spec:
  containers:
    - name: vpc-1-pod
      image: docker.io/library/nginx:alpine
---
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/logical_switch: net2
  name: vpc-2-pod
spec:
  containers:
    - name: vpc-2-pod
      image: docker.io/library/nginx:alpine
```

测试网络连通性

```bash
# kubectl exec -it vpc-1-pod -- ping $(kubectl get pod vpc-2-pod -o jsonpath='{.status.podIP}')
PING 172.31.0.2 (172.31.0.2): 56 data bytes
64 bytes from 172.31.0.2: seq=0 ttl=62 time=0.655 ms
64 bytes from 172.31.0.2: seq=1 ttl=62 time=0.086 ms
64 bytes from 172.31.0.2: seq=2 ttl=62 time=0.098 ms
^C
--- 172.31.0.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.086/0.279/0.655 ms
# kubectl exec -it vpc-2-pod -- ping $(kubectl get pod vpc-1-pod -o jsonpath='{.status.podIP}')
PING 10.0.0.2 (10.0.0.2): 56 data bytes
64 bytes from 10.0.0.2: seq=0 ttl=62 time=0.594 ms
64 bytes from 10.0.0.2: seq=1 ttl=62 time=0.093 ms
64 bytes from 10.0.0.2: seq=2 ttl=62 time=0.088 ms
^C
--- 10.0.0.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.088/0.258/0.594 ms
```
