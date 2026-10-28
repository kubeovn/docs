# IP 池使用

IP 池（IPPool）是比子网（Subnet）更细粒度的 IPAM 管理单元。你可以通过 IP 池将子网网段细分为多个单元，每个单元绑定到特定的命名空间（Namespace）或者 Workload 之上。

## 使用方法

使用示例：

```yaml
apiVersion: kubeovn.io/v1
kind: IPPool
metadata:
  name: pool-1
spec:
  subnet: ovn-default
  ips:
  - "10.16.0.201"
  - "10.16.0.210/30"
  - "10.16.0.220..10.16.0.230"
  namespaces:
  - ns-1
  enableAddressSet: true
```

绑定到特定 Workload：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ippool
  labels:
    app: ippool
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ippool
  template:
    metadata:
      labels:
        app: ippool
      annotations:
        ovn.kubernetes.io/ip_pool: pool-1
    spec:
      containers:
      - name: ippool
        image: docker.io/library/nginx:alpine
```

## 使用命名 IP 池

当 `ovn.kubernetes.io/ip_pool` 的值是 IPPool 名称（例如 `pool-1`）时，默认网络的 Pod 可以不设置
`ovn.kubernetes.io/logical_switch`。控制器会使用 `pool-1.spec.subnet` 作为 Pod 的子网，
并设置 Pod 的 `logical_switch`、`cidr` 和 `gateway` 注解：

```yaml
metadata:
  annotations:
    ovn.kubernetes.io/ip_pool: pool-1
```

如果显式设置 `ovn.kubernetes.io/logical_switch`，应确保它与 `IPPool.spec.subnet` 一致；
子网不一致未必会被拒绝。

对于多网卡 Pod，可以使用 `<provider>.kubernetes.io/ip_pool` 为指定 provider 选择命名 IP
池。provider 的子网独立于 IPPool 选择；应确保两者一致，包括显式设置
`<provider>.kubernetes.io/logical_switch` 时。子网不一致未必会被拒绝。值为单个 IP、
逗号分隔的 IP 列表，或每组 IPv4、IPv6 地址以逗号配对且各组以分号分隔的双栈列表时，
仍按固定 IP 注解处理，而不是按 IPPool 名称解析。

`spec.namespaces` 指定该 IPPool 可参与自动选池的命名空间，不限制显式指定该 IPPool 的 Pod。
列表为空时不会自动选择该池。普通 Pod 删除后，其地址会释放，IPPool 的使用计数也会更新；
StatefulSet 和 VM 的 Pod 可能保留地址，直到所属 Workload 被删除。

字段说明：

| 名称 | 用途 | 备注 |
| :--------: | :----------------- | :-------------------------------------------------------- |
| subnet | 指定所属子网 | 必填 |
| ips | 指定包含的 IP 范围 | 支持 <IP>、<CIDR> 以及 <IP1>..<IP2> 三种格式，支持 IPv6。 |
| namespaces | 绑定命名空间 | 可选。列出该 IPPool 可参与自动选池的命名空间，不限制显式指定该池的 Pod。 |
| enableAddressSet | 是否自动创建同名的 AddressSet | 默认 false，设置为 true 后 ACL 和策略路由可以使用对应 AddressSet 进行策略控制 |

## 注意事项

1. 为保证与 [Workload 通用 IP Pool 固定地址](./static-ip-mac.md#workload-ip-pool) 的兼容性，IP 池的名称不能是一个 IP 地址。
2. IP 池的 `.spec.ips` 可指定超出子网范围的 IP 地址，但实际有效的 IP 地址是 `.spec.ips` 与子网 CIDR 的交集。
3. 同一个子网的不同 IP 池，不能包含相同的（有效）IP 地址。
4. IP 池的 `.spec.ips` 可动态修改。
5. IP 池会继承子网的保留 IP，从 IP 池随机分配 IP 地址时，会跳过包含在 IP 池中的保留 IP。
6. 从子网随机分配 IP 地址时，只会从子网所有 IP 池以外的范围分配。
7. 多个 IP 池可以绑定同一个 Namespace。
8. IP 池的 `.spec.enableAddressSet` 默认为 `false`。设置为 `true` 后，会创建一个与 IP 池对应的 OVN NB 数据库 AddressSet 对象，并将 IP 池中的所有 IP 地址添加到该 AddressSet 中。你可以在 NetworkPolicy 或 VPC 逻辑路由策略中使用该 AddressSet 对象。
