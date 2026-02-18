# 多网络 NetworkPolicy

## 概述

默认情况下，Kube-OVN 会将 NetworkPolicy 应用到 `podSelector` 选中的 Pod 上的所有 OVN 接口。

对于多网卡 Pod，可以通过以下注解将策略限定到指定 Provider：

- `ovn.kubernetes.io/network_policy_for`

这样可以让一条策略只作用于指定接口，而不是 Pod 的全部接口。

## 注解格式

注解值为逗号分隔：

```yaml
metadata:
  annotations:
    ovn.kubernetes.io/network_policy_for: "ovn,default/net-a,default/net-b"
```

支持的条目格式：

- `ovn`（默认 OVN Provider）
- `<namespace>/<net-attach-def>`

示例：

- `ovn`
- `default/net-a`
- `ovn,default/net-a`

## Provider 匹配行为

- 不设置注解：保持原有行为，策略作用于所有 OVN Provider。
- 非法条目会被忽略并记录日志。
- 如果所有条目都非法，则不会选中任何 Provider，策略不会选中端口。
- 重复条目会自动去重。

`<namespace>/<net-attach-def>` 在 Kube-OVN 内部会映射为 Provider 名称格式：

- `<nad-name>.<nad-namespace>.ovn`

## Service ClusterIP 行为

在解析策略 peer 地址时，仅当选中的 Provider 所属子网位于**默认 VPC**时，才会将 Service ClusterIP 加入地址集。

如果 Provider 位于自定义 VPC，则不会加入 Service ClusterIP。

## 示例

假设 Pod 有以下接口：

- 默认 OVN Provider（`ovn`）
- `default/net-a`
- `default/net-b`

那么：

- 不设置 `network_policy_for`：
  - 策略作用于 `ovn`、`net-a`、`net-b`
- `network_policy_for: default/net-a`：
  - 策略仅作用于 `net-a`
- `network_policy_for: ovn,default/net-b`：
  - 策略作用于 `ovn` 和 `net-b`

## 说明

- 该注解只用于限定策略作用的 Provider/接口范围，不改变 Kubernetes NetworkPolicy 本身语义。
- 建议显式配置注解值，避免策略范围过大或过小。
