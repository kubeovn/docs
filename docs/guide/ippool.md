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

字段说明：

| 名称 | 用途 | 备注 |
| :--------: | :----------------- | :-------------------------------------------------------- |
| subnet | 指定所属子网 | 必填 |
| ips | 指定包含的 IP 范围 | 支持 <IP>、<CIDR> 以及 <IP1>..<IP2> 三种格式，支持 IPv6。 |
| namespaces | 绑定命名空间 | 可选。绑定的命名空间下的 Pod 将只会从绑定的 IP 池中分配 IP，而不会从子网内其他范围分配。 |
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
