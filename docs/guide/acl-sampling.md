# 实验性 NetworkPolicy ACL 采样

Kube-OVN 可以采样为 `networking.k8s.io/v1` `NetworkPolicy` 生成的 OVN ACL 决策。此功能处于实验阶段，默认关闭，适用于短期故障排查和可观测性场景，不应替代执行日志或通用报文采集器。

初始实现区分两类决策：

- `allow`：针对某条入向或出向 NetworkPolicy 规则生成的有状态 `allow-related` ACL；
- `default-deny`：没有允许规则匹配时生效的生成式丢弃 ACL。

`default-deny` 事件可能会记录拥有被采样 ACL 的 NetworkPolicy，但这种归属并不具有排他性。当多个策略选择同一个 Pod 时，采样到的 default-deny ACL 不能证明是某一条策略导致了拒绝。因此 default-deny 事件不包含规则索引。

## 要求和限制

控制器侧 ACL 采样要求 OVN 24.09 或更高版本。节点本地传输还要求满足以下全部条件：

- OVS 3.4 或更高版本；
- 使用 Linux 内核 datapath，而不是 userspace 或 DPDK datapath；
- 当前 OVS datapath 能力中存在 `psample=true`；
- OVS schema 包含 `Flow_Sample_Collector_Set.local_group_id`；
- Linux 内核提供 `psample` generic-netlink family。

只有为 Kubernetes NetworkPolicy 规则允许和 NetworkPolicy 默认拒绝生成的 Kube-OVN ACL 可以采样。不包含 DHCP 例外、网关和节点 ACL、SecurityGroup、AdminNetworkPolicy、BaselineAdminNetworkPolicy、ClusterNetworkPolicy 以及其他 ACL 生成方。

采样不会刷新 conntrack。启用此功能后，已有连接仍遵循 OVN 当前的 conntrack 状态，可能不会产生新的会话采样。

## 启用功能

两个 Helm chart 提供相同的 `aclSampling` 配置。推荐的 v2 chart 可以使用以下示例：

```yaml
aclSampling:
  enabled: true
  setID: 142
  localGroupID: 142
  appIDNew: 102
  appIDEstablished: 103
  collectorIDAllow: 1
  collectorIDDefaultDeny: 2
  allowProbabilityPercent: 1
  defaultDenyProbabilityPercent: 100
```

```bash
helm upgrade --install kube-ovn ./charts/kube-ovn-v2 \
  --set aclSampling.enabled=true
```

如需配置 classic chart，请使用 `./charts/kube-ovn`。在拆分部署或独立管理的部署中，控制器和 CNI agent 的配置必须保持一致。

对于基于 manifest 的安装器，请设置 ACL 采样环境变量后运行安装命令。安装器默认值与上面的 Helm 示例一致：

```bash
ENABLE_ACL_SAMPLING=true \
ACL_SAMPLING_SET_ID=142 \
ACL_SAMPLING_LOCAL_GROUP_ID=142 \
ACL_SAMPLING_APP_ID_NEW=102 \
ACL_SAMPLING_APP_ID_ESTABLISHED=103 \
ACL_SAMPLING_COLLECTOR_ID_ALLOW=1 \
ACL_SAMPLING_COLLECTOR_ID_DEFAULT_DENY=2 \
ACL_SAMPLING_ALLOW_PROBABILITY_PERCENT=1 \
ACL_SAMPLING_DEFAULT_DENY_PROBABILITY_PERCENT=100 \
bash dist/images/install.sh
```

这些变量是 `ENABLE_ACL_SAMPLING`、`ACL_SAMPLING_SET_ID`、`ACL_SAMPLING_LOCAL_GROUP_ID`、`ACL_SAMPLING_APP_ID_NEW`、`ACL_SAMPLING_APP_ID_ESTABLISHED`、`ACL_SAMPLING_COLLECTOR_ID_ALLOW`、`ACL_SAMPLING_COLLECTOR_ID_DEFAULT_DENY`、`ACL_SAMPLING_ALLOW_PROBABILITY_PERCENT` 和 `ACL_SAMPLING_DEFAULT_DENY_PROBABILITY_PERCENT`。需要使用其他 collector set 或采样速率时可以覆盖这些值。

配置字段的语义如下：

| 字段 | 约束 | 用途 |
| --- | --- | --- |
| `enabled` | 布尔值 | 启用控制器对象、ACL 挂载和节点本地传输。 |
| `setID` | 非零无符号 32 位整数 | 共享 OVN collector set 和 OVS collector-set ID。 |
| `localGroupID` | 无符号 32 位整数，允许为零 | OVS collector set 携带的 Linux psample group。 |
| `appIDNew` | 1 至 255 的唯一整数 | `acl-new` 采样的 application 字节。 |
| `appIDEstablished` | 1 至 255 的唯一整数 | `acl-est` 采样的 application 字节。 |
| `collectorIDAllow` | 1 至 255 的唯一整数 | allow 决策使用的 collector。 |
| `collectorIDDefaultDeny` | 1 至 255 的唯一整数 | default-deny 决策使用的 collector。 |
| `allowProbabilityPercent` | 0 至 100 的数字 | allow 决策的采样概率。 |
| `defaultDenyProbabilityPercent` | 0 至 100 的数字 | default-deny 决策的采样概率。 |

Kube-OVN 使用 `round(percent * 65535 / 100)` 将百分比转换为 OVN 的 16 位概率。概率为零时不会为对应决策挂载采样。default-deny 默认概率为 100%，在扫描或攻击期间可能产生大量事件；长时间使用时应降低该值。

配置的 ID 不得与其他应用拥有的对象冲突。Kube-OVN 可以复用匹配的未拥有 `Sampling_App`，但不会修改或删除它。未拥有的 application、collector 或节点 collector set 发生冲突时，采样不可用，并且这些对象保持不变。

## 解码和监听

镜像包含独立的 `/kube-ovn/kube-ovn-acl-sample` binary，提供两个子命令。该 binary 与 `kube-ovn` CNI plugin 分开构建。`kubectl ko acl` 会在选定的 Pod 中调用此 binary；执行 `decode` 时，wrapper 会自动补充 OVN northbound socket 地址。

解码十进制或带 `0x` 前缀的十六进制采样 metadata 值或 OVS user cookie：

```bash
kubectl ko acl decode 0x640abcde000000c8
```

在一个节点上监听，并通过 OVN northbound leader 解码收到的每个事件：

```bash
kubectl ko acl listen --node worker-1
```

监听器会读取已启用的 CNI DaemonSet 中的 `localGroupID`，在指定节点选择一个运行中的 `kube-ovn-cni` Pod，并为每个解码事件输出一个 YAML 文档。如果某个采样无法再从 NBDB 解析，监听器会将错误写入 standard error，但不会停止。

OVN 本地采样 cookie 的编码如下：

```text
63                         32 31                           0
+----------------------------+-----------------------------+
| observation domain         | Sample.metadata             |
+----------------------------+-----------------------------+

observation domain = application ID (8 bits) | datapath key (24 bits)
```

仅有 metadata 的输入可以识别 ACL 和策略，但无法识别事件来自 `acl-new` 还是 `acl-est`，也不包含逻辑 datapath key。

解码后的 YAML 对 allow 事件包含策略 UID、namespace、名称、方向和规则索引；还包含 OVN ACL UUID、action、方向、优先级、tier、match hash 以及采样 application 和 metadata。default-deny 输出使用 `policyOwner`，设置 `reason: network-policy-default-deny` 和 `attribution: non-exclusive`，并省略规则索引。

## 安全性

Linux psample 消息包含捕获的报文字节。当前 debug 命令只输出 cookie 和解码后的策略事件，但节点本地进程仍会从内核接收报文数据。因此，访问 `kubectl ko acl listen` 就具备报文观察能力，应限制为授权运维人员。使用尽可能低的采样概率，将命令输出作为敏感数据保护，并在排查完成后停止监听器。

## 故障隔离和监控

采样采用尽力而为方式。Kube-OVN 会先提交 NetworkPolicy 执行规则，再在单独的事务中挂载采样。不支持的 schema、ID 冲突、metadata 分配失败、节点能力不满足或挂载失败都不能阻止有效的 NetworkPolicy 生效。

请监控以下指标和 controller/daemon warning 日志：

| 指标 | 含义 |
| --- | --- |
| `acl_sampling_controller_available` | 启用的控制器采样路径上次成功 reconcile 时为 `1`，禁用或不可用时为 `0`。 |
| `acl_sampling_controller_failures_total{operation}` | `reconcile`、`prepare` 或 `attach` 操作的尽力而为控制器失败次数。 |
| `acl_sampling_node_available{node_name}` | 节点本地传输启用且可用时为 `1`，否则为 `0`。 |
| `acl_sampling_node_failures_total{node_name}` | 节点 collector-set reconcile 失败次数。 |

## 禁用和清理

将 controller 和 agent 上的 `aclSampling.enabled` 设回 `false`。随后 Kube-OVN 只会清除标记为其 NetworkPolicy 采样 ACL 的 sample 引用，让 OVN 垃圾回收不再引用的 `Sample` 行，删除它拥有且不再引用的 collector 和 application，并移除它拥有的节点 collector set。复用的或冲突的未拥有对象及引用会保留。
