# VIP 预留 IP

VIP 即虚拟 IP，用于预留 IP 资源。VIP 设计之初参考了 OpenStack Neutron Allowed-Address-Pairs（AAP）的功能，后来又扩展支持在子网内为 OVN Switch LB Rule 提供前端 VIP。
Pod 地址分配由 `IP` 资源和 IPAM 管理，VIP 不再用于为 Pod 固定地址。
目前 VIP 只有两种使用场景：

- Allowed-Address-Pairs VIP
- Switch LB rule VIP

## 1. Allowed-Address-Pairs VIP

在该场景下我们希望动态的预留一部分 IP 但是并不分配给 Pod 而是分配给其他的基础设施启用，例如：

- Kubernetes 嵌套 Kubernetes 的场景中上层 Kubernetes 使用 Underlay 网络会占用底层 Subnet 可用地址。
- LB 或其他网络基础设施需要使用一个 Subnet 内的 IP，但不会单独起 Pod。

此外，VIP 还可以为 Allowed-Address-Pairs 预留 IP 用来支持单个网卡配置多个 IP 的场景，例如：

- Keepalived 通过配置额外的 IP 地址对，可以帮助实现快速故障切换和灵活的负载均衡架构

### 1.1 自动分配地址 VIP

如果只是为了预留若干 IP 而对 IP 地址本身没有要求可以使用下面的 yaml 进行创建：

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-dynamic-01
spec:
  subnet: ovn-default
  type: ""

```

- `subnet`: 将从该 Subnet 中预留 IP。
- `type`: 目前支持两种类型，为空表示仅用于 ipam ip 占位，`switch_lb_vip` 表示该 vip 仅用于 switch lb 前端 vip 和后端 ip 需处于同一子网。

创建成功后查询该 VIP：

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
vip-dynamic-01   10.16.0.12           00:00:00:F0:DB:25                         ovn-default   true
```

可见该 VIP 被分配了 `10.16.0.12` 的 IP 地址，该地址可以之后供其他网络基础设施使用。

### 1.2 使用固定地址 VIP

如对预留的 VIP 的 IP 地址有需求可使用下面的 yaml 进行固定分配：

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: static-vip01
spec:
  subnet: ovn-default
  v4ip: "10.16.0.121"
```

- `subnet`: 将从该 Subnet 中预留 IP。
- `v4ip`: 固定分配的 IP 地址，该地址需在 `subnet` 的 CIDR 范围内。

创建成功后查询该 VIP：

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
static-vip01   10.16.0.121           00:00:00:F0:DB:26                         ovn-default   true
```

可见该 VIP 被分配了所预期的 IP 地址。

### 1.3 Pod 使用 VIP 开启 AAP

Pod 可以使用 annotation 指定 VIP 开启 AAP 功能，Pod 的 labels 需要满足 VIP 中 `selector` 标签选择器的条件。

Pod annotation 支持指定多个 VIP，配置格式为：ovn.kubernetes.io/aaps: vip-aap,vip-aap2,vip-aap3

AAP 功能支持[多网卡场景](./multi-nic.md)，若 Pod 配置了多网卡，AAP 会对 Pod 中和 VIP 同一 subnet 的对应 Port 进行配置

#### 1.3.1 创建 VIP 支持 AAP

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-aap
spec:
  subnet: ovn-default
  namespace: default
  selector:
    - "app: aap1"
```

VIP 同样支持固定地址和随机地址的分配，分配方式如上文所述。

- `namespace`: AAP 场景下，VIP 需显式地指定命名空间，VIP 仅允许相同命名空间的资源开启 AAP 功能。
- `selector`: AAP 场景下，用于选择 VIP 所附属的 Pod 的标签选择器（作用对象为 `namespace` 内的 Pod，而非节点）。每一项以 `key: value` 的字符串形式书写（注意冒号后有空格），多项之间为 AND 关系。

创建成功后查询该 VIP 对应的 Port：

```bash
# kubectl ko nbctl show ovn-default
switch e32e1d3b-c539-45f4-ab19-be4e33a061f6 (ovn-default)
    port aap-vip
        type: virtual
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox
  annotations:
    ovn.kubernetes.io/aaps: vip-aap
  labels:
    app: aap1
spec:
  containers:
    - name: busybox
      image: busybox
      command: ["sleep", "3600"]
      securityContext:
        capabilities:
          add:
            - NET_ADMIN
```

创建成功后查询该 AAP 对应的配置：

```bash
# kubectl ko nbctl list logical_switch_port aap-vip
_uuid               : cd930750-0533-4f06-a6c0-217ddac73272
addresses           : []
dhcpv4_options      : []
dhcpv6_options      : []
dynamic_addresses   : []
enabled             : []
external_ids        : {ls=ovn-default, vendor=kube-ovn}
ha_chassis_group    : []
mirror_rules        : []
name                : aap-vip
options             : {virtual-ip="10.16.0.100", virtual-parents="busybox.default"}
parent_name         : []
port_security       : []
tag                 : []
tag_request         : []
type                : virtual
up                  : false
```

virtual-ip 被配置为 VIP 预留的 IP，virtual-parents 配置为开启 AAP 功能的 Pod 对应的 Port。

创建成功后查询该 Pod 对应的配置：

```bash
# kubectl exec -it busybox -- ip addr add 10.16.0.100/16 dev eth0
# kubectl exec -it busybox01 -- ip addr show eth0
35: eth0@if36: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1400 qdisc noqueue
    link/ether 00:00:00:e2:ab:0c brd ff:ff:ff:ff:ff:ff
    inet 10.16.0.7/16 brd 10.16.255.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet 10.16.0.100/16 scope global secondary eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fee2:ab0c/64 scope link
       valid_lft forever preferred_lft forever
```

除 Pod 创建时自动分配的 IP，VIP 的 IP 也被成功绑定，并且当前 subnet 内的其它 Pod 能和这两个 IP 进行通信。

## 2. [Switch LB rule](../vpc/vpc-internal-lb.md) vip

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: slr-01
spec:
  subnet: ovn-default
  type: switch_lb_vip

```

- `subnet`: 将从该 Subnet 中预留 IP。
- `type`: 目前支持两种类型，为空表示仅用于 ipam ip 占位，`switch_lb_vip` 表示该 vip 仅用于 switch lb 前端 vip 和后端 ip 需处于同一子网。

## 3. 从 v1.17 之前的版本升级

v1.17 移除了通过 `ovn.kubernetes.io/vip` 为 Pod 固定 IP 的功能，以及 `kube_host_vm_vip` 类型。升级前请删除使用该 annotation 的 Pod 或对应的 VIP，避免旧的 VIP 预留与 Pod 重新分配的 IP 发生冲突。

- 升级后，使用 `ovn.kubernetes.io/vip` 的 Pod 会获得普通 IPAM 地址；该 annotation 会被忽略并记录告警。
- 升级后删除这类 Pod 会释放其 IPAM 地址，但不会释放 VIP，也不会将地址交还给 VIP；其他 Pod 可能先占用该地址。只有 controller 重启且地址仍空闲时，VIP 才可能重新占用该地址。
- `kube_host_vm_vip` 不再创建或维护普通逻辑交换机端口。遗留端口会在两轮垃圾回收后被清理；如果外部工作负载仍在使用，请在升级前改用外部方式管理该端口。
- v1.17 之前 VIP 上遗留的 `ip_reserved` 标签不会自动删除，也不再参与地址预留。旧 Pod 仍占用地址时，Subnet 的 `UsingIPs` 可能暂时比实际使用量高；Pod 及其 IP 记录删除后，这个额外计数会消失，VIP 自身的预留仍会正常计数。

需要为 Pod 预留或固定地址时，请使用 [IPPool](../guide/ippool.md) 或 [Pod annotation](../guide/static-ip-mac.md)。AAP 和 Switch LB 仍继续使用 VIP。

## 4. StatefulSet 和 Kubevirt VM 保留 IP

StatefulSet 和 VM 的 IP 保留机制不依赖 VIP 资源。

对于 `StatefulSet` 和 `VM`，其 Pod 销毁后重新创建时会复用之前分配的 IP。

VM 保留 IP 需要确保 `kube-ovn-controller` 的 `keep-vm-ip` 参数为 `true`。请参考 [Kubevirt VM 固定地址开启设置](../reference/setup-options.md#kubevirt-vm)。
