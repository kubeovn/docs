# IP 池使用

IP 池（IPPool）是比子网（Subnet）更细粒度的 IPAM 管理单元。你可以通过 IP 池将子网网段细分为多个单元，每个单元绑定一个或多个命名空间（Namespace）。

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
```

字段说明：

|    名称    | 用途               | 备注                                                      |
| :--------: | :----------------- | :-------------------------------------------------------- |
|   subnet   | 指定所属子网       | 必填                                                      |
|    ips     | 指定包含的 IP 范围 | 支持 <IP>、<CIDR> 以及 <IP1>..<IP2> 三种格式，支持 IPv6。 |
| namespaces | 绑定命名空间       | 可选，namespace 一旦和 IP 池绑定将不会从子网其他地址空间分配地址。 |

## 注意事项

1. 为保证与 [Workload 通用 IP Pool 固定地址](./static-ip-mac.md#workload-ip-pool) 的兼容性，IP 池的名称不能是一个 IP 地址。
2. IP 池的 `.spec.ips` 可指定超出子网范围的 IP 地址，但实际有效的 IP 地址是 `.spec.ips` 与子网 CIDR 的交集。
3. 同一个子网的不同 IP 池，不能包含相同的（有效）IP 地址。
4. IP 池的 `.spec.ips` 可动态修改。
5. IP 池会继承子网的保留 IP，从 IP 池随机分配 IP 地址时，会跳过包含在 IP 池中的保留 IP。
6. 从子网随机分配 IP 地址时，只会从子网所有 IP 池以外的范围分配。
7. 多个 IP 池可以绑定同一个 Namespace。
