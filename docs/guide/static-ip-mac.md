# 固定地址

Kube-OVN 默认会根据 Pod 所在 Namespace 所属的子网中随机分配 IP 和 Mac。
针对工作负载需要固定地址的情况，Kube-OVN 根据不同的场景，提供了多种固定地址的方法：

- 单个 Pod 固定 IP/Mac。
- 同一交换机下多网卡分别固定 IP/MAC（多网卡接入同一子网时按网卡指定）。
- Workload 通用 IP Pool 方式指定固定地址范围。
- StatefulSet 固定地址。
- KubeVirt VM 固定地址。
- 使用 Multus 给附属网卡固定地址。

## 单个 Pod 固定 IP 和 Mac

可以在创建 Pod 时通过 annotation 来指定 Pod 运行时所需的 IP/Mac, `kube-ovn-controller`
运行时将会跳过地址随机分配阶段，经过冲突检测后直接使用指定地址，如下所示：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  annotations:
    ovn.kubernetes.io/ip_address: 10.16.0.15   // 双栈地址使用逗号分隔 10.16.0.15,fd00:10:16::15
    ovn.kubernetes.io/mac_address: 00:00:00:53:6B:B6
spec:
  containers:
  - name: static-ip
    image: docker.io/library/nginx:alpine
```

在使用 annotation 定义单个 Pod IP/Mac 时需要注意以下几点：

1. 所使用的 IP/Mac 不能和已有的 IP/Mac 冲突。
2. IP 必须在所属子网的 CIDR 内。
3. 可以只指定 IP 或 Mac，只指定一个时，另一个会随机分配。

## 同一交换机下多网卡分别固定 IP/MAC

当 Pod 或 VM 通过 Multus 挂载了多个网卡且这些网卡接入**同一逻辑交换机**时，可为每个网卡分别指定静态 IP/MAC。需在 Multus 的 `k8s.v1.cni.cncf.io/networks` 中为每个挂载指定不同的 `interface` 名称，再使用按网卡区分的 annotation：

- `<nadName>.<nadNamespace>.kubernetes.io/ip_address.<interfaceName>`：指定该网卡的静态 IP
- `<nadName>.<nadNamespace>.kubernetes.io/mac_address.<interfaceName>`：指定该网卡的静态 MAC

其中 `<nadName>`、`<nadNamespace>` 为 NetworkAttachmentDefinition 的名称与命名空间，`<interfaceName>` 须与 Multus 中该挂载的 `interface` 一致。未使用上述按网卡 annotation 时，仍可使用扁平 annotation `ovn.kubernetes.io/ip_address` / `ovn.kubernetes.io/mac_address` 作为回退（作用于主网卡或单网卡场景）。

示例：同一 NAD 挂载两次到同一子网，两个网卡分别固定 IP/MAC：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-if-static
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/networks: '[{"name": "attachnet", "namespace": "default", "interface": "net1"}, {"name": "attachnet", "namespace": "default", "interface": "net2"}]'
    attachnet.default.kubernetes.io/ip_address.net1: 172.17.0.100
    attachnet.default.kubernetes.io/mac_address.net1: 00:00:00:53:6B:B1
    attachnet.default.kubernetes.io/ip_address.net2: 172.17.0.101
    attachnet.default.kubernetes.io/mac_address.net2: 00:00:00:53:6B:B2
spec:
  containers:
  - name: multi-if-static
    image: docker.io/library/nginx:alpine
```

## Workload 通用 IP Pool 固定地址

Kube-OVN 支持通过 annotation `ovn.kubernetes.io/ip_pool` 给 Workload（Deployment/StatefulSet/DaemonSet/Job/CronJob）设置固定 IP。
`kube-ovn-controller` 会自动选择 `ovn.kubernetes.io/ip_pool` 中指定的 IP 并进行冲突检测。

IP Pool 的 Annotation 需要加在 `template` 内的 `annotation` 字段，除了 Kubernetes 内置的 Workload 类型，
其他用户自定义的 Workload 也可以使用同样的方式进行固定地址分配。

### Deployment 固定 IP 示例

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
        ovn.kubernetes.io/ip_pool: 10.16.0.15,10.16.0.16,10.16.0.17 // 双栈地址使用分号进行分隔 10.16.0.15,fd00:10:16::000E;10.16.0.16,fd00:10:16::000F;10.16.0.17,fd00:10:16::0010
    spec:
      containers:
      - name: ippool
        image: docker.io/library/nginx:alpine
```

对 Workload 使用固定 IP 需要注意以下几点：

1. `ovn.kubernetes.io/ip_pool` 中的 IP 应该属于所在子网的 CIDR 内。
2. `ovn.kubernetes.io/ip_pool` 中的 IP 不能和已使用的 IP 冲突。
3. 当 `ovn.kubernetes.io/ip_pool` 中的 IP 数量小于 replicas 数量时，多出的 Pod 将无法创建。你需要根据 Workload 的更新策略以及扩容规划调整 `ovn.kubernetes.io/ip_pool` 中 IP 的数量。

## StatefulSet 固定地址

StatefulSet 默认支持固定 IP，而且和其他 Workload 相同，可以使用 `ovn.kubernetes.io/ip_pool` 来指定 Pod 使用的 IP 范围。

由于 StatefulSet 多用于有状态服务，对网络标示的固定有更高的要求，Kube-OVN 做了特殊的强化：

1. Pod 会按顺序分配 `ovn.kubernetes.io/ip_pool` 中的 IP。例如 StatefulSet 的名字为 web，则 web-0 会使用 `ovn.kubernetes.io/ip_pool` 中的第一个 IP， web-1 会使用第二个 IP，以此类推。
2. StatefulSet Pod 在更新或删除的过程中 OVN 中的 logical_switch_port 不会删除，新生成的 Pod 直接复用旧的 interface 信息。因此 Pod 可以复用 IP/Mac 及其他网络信息，达到和 StatefulSet Volume 类似的状态保留功能。
3. 基于 2 的能力，对于没有 `ovn.kubernetes.io/ip_pool` 注解的 StatefulSet，Pod 第一次生成时会随机分配 IP/Mac，之后在整个 StatefulSet 的生命周期内，网络信息都会保持固定。

### StatefulSet 示例

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx"
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: docker.io/library/nginx:alpine
        ports:
        - containerPort: 80
          name: web
```

可以尝试删除 StatefulSet 下 Pod 观察 Pod IP 变化信息。

### 更新 StatefulSet Pod IP

由于 StatefulSet 下的 IP 和 Pod Name 生命周期绑定，直接更新 Statefulset 的 `ovn.kubernetes.io/ip_pool` Annotation 无法更新 Pod 的 IP。

如果遇到需要更新 StatefulSet Pod IP 的场景请先将 StatefulSet 的副本数 scale 到 0，之后再更新 Annotation 并恢复 StatefulSet 副本数。

## KubeVirt VM 固定地址

针对 KubeVirt 创建的 VM 实例，`kube-ovn-controller` 可以按照类似 StatefulSet Pod 的方式进行 IP 地址分配和管理。
以达到 VM 实例在生命周期内启停，升级，迁移等操作过程中地址固定不变，更符合虚拟化用户的实际使用体验。具体操作请参考 [VM 固定 IP](../kubevirt/static-ip.md)。

## 使用 Multus 给附属网卡固定地址

在使用 Multus 给 Pod 配置多网卡的情况下，针对 Kube-OVN 类型的网卡可以通过特定的 annotation 来配置固定地址，对于非 Kube-OVN 的其他 CNI，Kube-OVN 也可以单独提供 IPAM 能力来使得其他 CNI 也具备固定地址的能力。具体操作请参考[多网卡管理](../advance/multi-nic.md)。
