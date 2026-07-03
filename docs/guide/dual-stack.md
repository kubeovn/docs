# 双栈使用

Kube-OVN 中不同的子网可以支持不同的协议，一个集群内可以同时存在 IPv4，IPv6 和双栈类型的子网。
建议在一个集群内使用统一的协议类型以简化使用和维护。

为了支持双栈，需要主机网络满足双栈要求，同时需要对 Kubernetes 相关参数做调整，
请参考 Kubernetes 的[双栈官方指导](https://kubernetes.io/docs/concepts/services-networking/dual-stack)。

## 创建双栈子网

在配置双栈时，只需要设置对应子网 CIDR 格式为 `cidr=<IPv4 CIDR>,<IPv6 CIDR>` 即可。
CIDR 顺序要求 IPv4 在前，IPv6 在后，如下所示：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata: 
  name: ovn-test
spec:
  cidrBlock: 10.16.0.0/16,fd00:10:16::/64
  excludeIps:
  - 10.16.0.1
  - fd00:10:16::1
  gateway: 10.16.0.1,fd00:10:16::1
```

如果需要在安装时默认子网使用双栈，需要在安装脚本中修改如下参数（`install.sh` 双栈下的默认掩码为 `/112`，更易避开常见 ULA 段；如希望使用 `/64` 也允许，但要确保不与节点/Service CIDR 冲突）：

```bash
POD_CIDR="10.16.0.0/16,fd00:10:16::/112"
JOIN_CIDR="100.64.0.0/16,fd00:100:64::/112"
```

## 查看 Pod 地址

配置双栈网络的 Pod 将会从该子网同时分配 IPv4 和 IPv6 的地址，分配结果会显示在 Pod 的 annotation 中:

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/allocated: "true"
    ovn.kubernetes.io/cidr: 10.16.0.0/16,fd00:10:16::/64
    ovn.kubernetes.io/gateway: 10.16.0.1,fd00:10:16::1
    ovn.kubernetes.io/ip_address: 10.16.0.9,fd00:10:16::9
    ovn.kubernetes.io/logical_switch: ovn-default
    ovn.kubernetes.io/mac_address: 00:00:00:14:88:09
    ovn.kubernetes.io/routed: "true"
...
podIP: 10.16.0.9
  podIPs:
  - ip: 10.16.0.9
  - ip: fd00:10:16::9
```

## 为单个 Pod 或网卡选择 IP 协议族

在双栈子网中，如果某个 Pod 或某块网卡只需要分配 IPv4 或 IPv6 地址，可以在创建 Pod 时使用 `ip_family` annotation。
未设置该 annotation 时，Kube-OVN 仍保持默认双栈分配行为。
以下示例假设目标 Pod 或网卡使用的 Subnet 为双栈子网。

默认网络使用 `ovn.kubernetes.io/ip_family`：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ipv4-only
  annotations:
    ovn.kubernetes.io/ip_family: ipv4
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

支持的取值为 `ipv4` 和 `ipv6`。该功能仅用于从双栈子网中选择单个协议族，不会改变子网自身的协议类型。
如果在 IPv4 单栈子网中请求 `ipv6`，或在 IPv6 单栈子网中请求 `ipv4`，Pod 将无法分配地址。

对于通过 Multus 添加的附属网卡，使用 `<provider>.kubernetes.io/ip_family`。`<provider>` 需要和对应 NetworkAttachmentDefinition 或 Subnet 中的 provider 一致：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: attach-ipv6-only
  annotations:
    k8s.v1.cni.cncf.io/networks: default/attachnet
    attachnet.default.ovn.kubernetes.io/ip_family: ipv6
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

当同一个 NetworkAttachmentDefinition 被多次挂载并指定了不同的 `interface` 名称时，Kube-OVN 会按带有接口名的 provider 读取 annotation。
例如 `net1` 只分配 IPv4，`net2` 只分配 IPv6：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: attach-mixed-family
  annotations:
    k8s.v1.cni.cncf.io/networks: '[{"name": "attachnet", "namespace": "default", "interface": "net1"}, {"name": "attachnet", "namespace": "default", "interface": "net2"}]'
    attachnet.default.ovn.net1.kubernetes.io/ip_family: ipv4
    attachnet.default.ovn.net2.kubernetes.io/ip_family: ipv6
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

如果同时设置了静态 IP，例如 `ovn.kubernetes.io/ip_address`、`<provider>.kubernetes.io/ip_address`，或同一 NetworkAttachmentDefinition 多接口场景下的 `<nadName>.<nadNamespace>.kubernetes.io/ip_address.<interfaceName>`，静态 IP 的协议族必须和 `ip_family` 一致。
