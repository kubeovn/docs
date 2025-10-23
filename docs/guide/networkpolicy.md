# NetworkPolicy 使用

NetworkPolicy 是 Kubernetes 提供的一种网络策略接口，用于控制 Pod 之间以及 Pod 与其他网络端点之间的网络流量。
Kube-OVN 通过 OVN 的 ACL 机制来实现了 Kubernetes NetworkPolicy 的规范，在这之上提供了两种不同严格程度的规则模式来适应不同场景以及 NetworkPolicy 日志功能来排查规则问题。

## Kube-OVN 中的实现机制

Kube-OVN 通过 OVN（Open Virtual Network）的原生能力来实现 NetworkPolicy，主要使用了三个 OVN 组件：

### Port Group（端口组）

当创建一个 NetworkPolicy 时，Kube-OVN 会为该策略创建一个 Port Group，用于将所有匹配 `podSelector` 的 Pod 的逻辑端口组织在一起。
Port Group 的名称格式为 `<策略名>.<命名空间名>`，其中 `-` 会被替换为 `.`。

### Address Set（地址集）

Address Set 用于存储 NetworkPolicy 规则中定义的允许或拒绝访问的 IP 地址集合。对于每个 NetworkPolicy 规则，
Kube-OVN 会根据 `podSelector`、`namespaceSelector` 或 `ipBlock` 计算出对应的 IP 地址，并存储在 Address Set 中。

为每个 NetworkPolicy 的 Ingress 和 Egress 规则分别创建 Allow 和 Except 两类 Address Set：

- `<策略名>.<命名空间名>.ingress.allow`：允许的入向 IP 地址
- `<策略名>.<命名空间名>.ingress.except`：排除的入向 IP 地址
- `<策略名>.<命名空间名>.egress.allow`：允许的出向 IP 地址
- `<策略名>.<命名空间名>.egress.except`：排除的出向 IP 地址

### ACL（访问控制列表）

ACL 是 OVN 中实际执行流量控制的组件。Kube-OVN 将 NetworkPolicy 规则转换为 OVN ACL 规则，
并关联到对应的 Port Group 上。ACL 规则包含匹配条件、优先级和动作（允许或拒绝）。

Kube-OVN 为 NetworkPolicy 使用的 ACL 优先级范围：

- Ingress Allow 规则：优先级 2001
- Egress Allow 规则：优先级 2001
- Default Deny 规则：优先级 1000

通过这种方式，Kube-OVN 能够高效地实现 Kubernetes NetworkPolicy 的语义，并充分利用 OVN 的分布式 ACL 能力。

## 注意事项

### 与其他访问控制机制的关系

Kube-OVN 同时支持多种网络访问控制机制：

- **NetworkPolicy**：Kubernetes 标准的网络策略
- **Network Policy API**：AdminNetworkPolicy 和 BaselineAdminNetworkPolicy
- **Subnet ACL**：子网级别的访问控制
- **Security Group**：安全组

这些机制在底层都是通过 OVN ACL 实现的。虽然 NetworkPolicy 和 Network Policy API 在设计时考虑了规则分层以避免优先级冲突，
但同时使用多种访问控制机制可能导致规则管理复杂和优先级冲突。**建议不要同时使用多种访问控制规则。**

### Named Port 的使用限制

NetworkPolicy 规范支持使用 Named Port 来指定端口，例如：

```yaml
ports:
- protocol: TCP
  port: http
```

Kube-OVN 对 Named Port 的支持存在限制：**当前只支持 Named Port 映射到同一个端口号**。

如果集群中存在多个 Pod 使用相同的 Named Port 名称但映射到不同的端口号，NetworkPolicy 将无法正确工作并可能出现错误。
例如，如果 Pod A 的 `http` 端口映射到 8080，而 Pod B 的 `http` 端口映射到 8081，则使用 `port: http` 的 NetworkPolicy 规则会出现问题。

建议在使用 Named Port 时，确保所有相关 Pod 的同名端口映射到相同的端口号，或者直接使用数字端口号来避免此问题。

### IPBlock Except 规则的性能影响

NetworkPolicy 的 `ipBlock` 规则支持 `except` 字段来排除特定的 IP 地址段：

```yaml
egress:
- to:
  - ipBlock:
      cidr: 10.0.0.0/8
      except:
      - 10.0.1.0/24
      - 10.0.2.0/24
```

在 OVN 的流表实现中，`except` 规则会导致流表的显著膨胀。每个 `except` 子网都需要额外的 ACL 规则来实现，
这会增加 OVN 数据库的大小和流表处理的复杂度，对网络性能产生负面影响。

**建议尽可能避免使用 `except` 规则。** 如果必须排除某些 IP 地址段，考虑以下替代方案：

- 将 CIDR 拆分为多个不重叠的较小网段，直接指定允许的网段
- 使用更精确的 `podSelector` 或 `namespaceSelector` 来替代 IP 地址过滤

## NetworkPolicy 日志

Kube-OVN 提供了 NetworkPolicy 日志功能，可以帮助管理员快速定位网络策略规则是否生效，以及排查网络连通性问题。

!!! warning

    NetworkPolicy 日志功能一旦开启，对每个命中规则的数据包都需要打印日志，会带来额外的性能开销。
    在恶意攻击场景下，短时间大量日志可能会耗尽 CPU 资源。
    
    建议在生产环境中默认关闭日志功能，仅在需要排查问题时动态开启。
    
    OVN 上游已支持 [ACL Log Meter](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#ACL_TABLE) 用于限制 ACL 日志生成速度，Kube-OVN 将在未来版本中支持该特性。

### 启用日志记录

在需要开启日志记录的 NetworkPolicy 中增加 annotation `ovn.kubernetes.io/enable_log`：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
  annotations:
    ovn.kubernetes.io/enable_log: "true"
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

启用日志后，默认只会记录被拒绝（Drop）的流量日志。

### 查看日志

日志会记录在 Pod 所在节点的 `/var/log/ovn/ovn-controller.log` 文件中：

```bash
# tail -f /var/log/ovn/ovn-controller.log
2022-07-20T05:55:03.229Z|00394|acl_log(ovn_pinctrl0)|INFO|name="np/default-deny-ingress.default/IPv4/0", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.10,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=54343,tp_dst=53
```

日志中包含了详细的五元组信息（源 IP、目的 IP、协议、源端口、目的端口），方便进行问题排查。

### 记录允许的流量

从 Kube-OVN v1.13.0 开始，支持通过 `ovn.kubernetes.io/log_acl_actions` annotation 来记录允许（Allow）的流量：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-client
  namespace: default
  annotations:
    ovn.kubernetes.io/enable_log: "true"
    ovn.kubernetes.io/log_acl_actions: "allow"
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: client
```

`ovn.kubernetes.io/log_acl_actions` 的值可以是：

- `drop`：仅记录被拒绝的流量（默认）
- `allow`：仅记录被允许的流量
- `allow,drop`：同时记录允许和拒绝的流量

查看允许流量的日志：

```bash
# tail -f /var/log/ovn/ovn-controller.log
2024-08-14T09:27:49.590Z|00004|acl_log(ovn_pinctrl0)|INFO|name="np/allow-from-client.default/ingress/IPv4/0", verdict=allow, severity=info, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=96:7b:b0:2f:a0:1a,dl_dst=a6:e5:1b:c2:1b:f8,nw_src=10.16.0.7,nw_dst=10.16.0.12,nw_tos=0,nw_ecn=0,nw_ttl=64,nw_frag=no,icmp_type=8,icmp_code=0
```

### 关闭日志记录

将 annotation `ovn.kubernetes.io/enable_log` 设置为 `false` 即可关闭日志：

```bash
kubectl annotate networkpolicy -n default allow-from-client ovn.kubernetes.io/enable_log=false --overwrite
```

## 策略执行模式

Kube-OVN 支持两种不同严格程度的执行模式：

- **standard**：默认模式，会严格按照 NetworkPolicy 的规范执行策略，任何不在规则里的 IP 流量都会被拒绝。
- **lax**：在某些场景下放宽限制，提供更好的兼容性，该模式下只会对 TCP/UDP/SCTP 流量拒绝，也就是说不在规则里的 ICMP 或其他 L4 协议的 IP 流量会被放行，同时会放行 DHCP 的 UDP 流量以便更好适应虚拟化的场景。

可以通过在 NetworkPolicy 上添加 annotation 来指定执行模式：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example-policy
  namespace: default
  annotations:
    ovn.kubernetes.io/enforcement: "lax"
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

也可以在 Kube-OVN 控制器启动时通过参数 `--network-policy-enforcement` 全局配置默认的执行模式。
