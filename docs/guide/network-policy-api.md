# Network Policy API

Kube-OVN 使用 `network-policy-api v0.3.0` 提供 `v1beta1` 版本的
`ClusterNetworkPolicy`（CNP）API。启用 ANP/CNP 以及基于 DNS 名称的访问控制，
请参考[基于域名的访问控制](./egress-firewall.md)中的控制器和 DNS resolver 配置。

## 使用 `protocols` 匹配端口

CNP 的入向和出向规则使用 `protocols` 表达传输层协议和目标端口。例如：

```yaml
protocols:
  - tcp:
      destinationPort:
        number: 443
  - udp:
      destinationPort:
        range:
          start: 8000
          end: 9000
```

支持 TCP、UDP 和 SCTP 的数字端口及端口范围。`destinationNamedPort` 会针对规则选中的目标 Pod 解析端口名，并支持该名称在这些 Pod 上声明的所有协议和端口号。端口名只能针对 Pod 或 Namespace 进行解析；Node、Network 和域名类型的 peer 不提供目标 Pod，不能解析端口名。

省略 `protocols` 表示不限制传输协议或目标端口。域名类型的 peer 需要 DNS resolver，并且规则动作必须为 `Accept`。

## 从旧版本迁移

使用 `network-policy-api v0.3.0` 的 controller 和 CRD 前，必须将已有 CNP 清单从 `ports` 转换为 `protocols`。该版本不会自动迁移对象，不兼容旧的 `ports` 格式，也不提供反向迁移。

v0.3.0 CRD 同时提供 `v1alpha2` 和 `v1beta1`，其中 `v1beta1` 是存储版本。两个版本使用相同的 schema，不需要 conversion webhook。已有 `v1alpha2` 对象仍可通过 `v1beta1` 读取和写入；单独更新 CRD 不会重写已存储的对象，也不会把旧的 `ports` 字段转换为 `protocols`。

ANP 和 BANP 继续使用各自的 `v1alpha1` CRD；`network-policy-api v0.3.0` 仅发布 CNP conformance profile，不改变 ANP/BANP 的版本约束。
