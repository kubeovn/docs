# DHCP

在使用 `managedTap`、`SR-IOV` 或 `DPDK` 类型网络时，KubeVirt 内置的 DHCP 无法在该网络模式下工作。Kube-OVN 可以利用 OVN 的 DHCP 能力在子网级别或 Pod 级别设置
 DHCP 选项，从而帮助该网络类型的 KubeVirt 虚机正常使用 DHCP 获得分配的 IP 地址。同时 Kube-OVN 的 DHCP 还提供了 DHCPv6, IPv6RA, DNS，TFTP 等 DHCP 高级选项，用户可以根据自己的需求定义 DHCP 服务的具体行为。

!!! warning

    对于 `bridge` 类型网络，KubeVirt 的 DHCP 会先于 Kube-OVN 拦截并响应 DHCP 请求，因此 Kube-OVN 设置的 DHCP 功能无法生效。如果要使用 Kube-OVN 提供的高级 DHCP 能力，
    我们推荐使用 `managedTap` 类型网络替换 `bridge` 类型网络。`managedTap` 类型网络的配置请参考[配置 managedTap 类型网络](dual-stack.md#managedtap)。

## 子网级别 DHCP 配置

子网 DHCP 的配置如下：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: sn-dual
spec:
  cidrBlock: "10.0.0.0/24,240e::a00/120"
  default: false
  disableGatewayCheck: true
  disableInterConnection: false
  excludeIps:
    - 10.0.0.1
    - 240e::a01
  gateway: 10.0.0.1,240e::a01
  gatewayNode: ''
  gatewayType: distributed
  natOutgoing: false
  private: false
  protocol: Dual
  provider: ovn
  vpc: vpc-test
  enableDHCP: true
  dhcpV4Options: "lease_time=3600,router=10.0.0.1,server_id=169.254.0.254,server_mac=00:00:00:2E:2F:B8"
  dhcpV6Options: "server_id=00:00:00:2E:2F:C5"
  enableIPv6RA: true
  ipv6RAConfigs: "address_mode=dhcpv6_stateful,max_interval=30,min_interval=5,send_periodic=true"
```

- `enableDHCP`: 是否开启子网的 DHCP 功能。
- `dhcpV4Options`,`dhcpV6Options`: 该字段直接暴露 ovn-nb 内 DHCP 相关选项，请参考 [DHCP Options](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#DHCP_Options_TABLE){: target = "_blank" }。
默认值分别为 `"lease_time=3600, router=$ipv4_gateway, server_id=169.254.0.254, server_mac=$random_mac"` 和 `server_id=$random_mac`。
- `enableIPv6RA`: 是否开启 DHCPv6 的路由广播功能。
- `ipv6RAConfigs`：该字段直接暴露 ovn-nb 内 Logical_Router_Port 相关选项，请参考 [Logical Router Port](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#Logical_Router_Port_TABLE){: target = "_blank" }。默认值为
`address_mode=dhcpv6_stateful, max_interval=30, min_interval=5, send_periodic=true`。

## Pod 级别 DHCP 配置

除了子网级别的 DHCP 配置外，Kube-OVN 还支持通过 Pod 注解为每个 Pod 的网络接口单独配置 DHCP 选项。Pod 级别的 DHCP 配置具有最高优先级，会覆盖子网级别的 DHCP 设置，并且不受子网 `enableDHCP` 设置的影响。

### 注解格式

```bash
# 主网络（provider 为 "ovn"）
ovn.kubernetes.io/dhcp-v4-options: "lease_time=3600,router=10.0.0.1,dns_server=8.8.8.8"
ovn.kubernetes.io/dhcp-v6-options: "server_id=00:00:00:00:00:01"

# 附加网络（provider 为 "net1.ns1.ovn"）
net1.ns1.ovn.kubernetes.io/dhcp-v4-options: "lease_time=7200"
```

注解的 key 格式为 `<provider>.kubernetes.io/dhcp-v4-options` 和 `<provider>.kubernetes.io/dhcp-v6-options`，其中 `<provider>` 为网络提供者名称。对于默认网络，provider 为 `ovn`；对于通过 Multus 添加的附加网络，provider 格式为 `<net-attach-def-name>.<namespace>.ovn`。

### 使用示例

以下示例为 Pod 设置自定义的 DHCPv4 选项：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dhcp-pod
  annotations:
    ovn.kubernetes.io/dhcp-v4-options: "lease_time=3600,router=10.0.0.1,dns_server=8.8.8.8"
    ovn.kubernetes.io/dhcp-v6-options: "server_id=00:00:00:00:00:01"
spec:
  containers:
    - name: test
      image: docker.io/library/nginx:alpine
```

对于 Multus 多网卡场景，可以按 provider 分别设置不同网络接口的 DHCP 选项：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-nic-dhcp-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: '[{"name": "net1", "namespace": "ns1"}]'
    ovn.kubernetes.io/dhcp-v4-options: "lease_time=3600,router=10.0.0.1"
    net1.ns1.ovn.kubernetes.io/dhcp-v4-options: "lease_time=7200,router=10.0.1.1"
spec:
  containers:
    - name: test
      image: docker.io/library/nginx:alpine
```

### 优先级说明

DHCP 选项的优先级从高到低为：

1. **Pod 注解**：通过 `<provider>.kubernetes.io/dhcp-v4-options` 和 `<provider>.kubernetes.io/dhcp-v6-options` 设置的 Pod 级别 DHCP 选项。
2. **子网配置**：通过 Subnet CRD 的 `dhcpV4Options` 和 `dhcpV6Options` 字段设置的子网级别 DHCP 选项。

当 Pod 设置了 DHCP 注解时，将完全使用 Pod 注解中的 DHCP 配置，忽略子网级别的设置。

!!! note

    删除正在运行的 Pod 上的 DHCP 注解不会立即恢复 DHCP 设置，需要重启 Pod 才能生效。
