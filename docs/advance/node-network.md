# Overlay 网络封装网卡选择

在一些场景下，用户希望容器 Overlay 网络使用主机不同的网卡进行 tunnel 封装，从而实现：

- **存储网络分离**：存储流量走专用高速网卡，业务流量走普通网卡。
- **业务网络隔离**：不同业务子网使用不同物理网卡，实现物理层面的网络隔离。
- **网络带宽控制**：通过物理网卡分离实现带宽隔离，避免业务流量相互干扰。

## 默认封装网卡选择

在节点存在多块网卡的情况下，Kube-OVN 默认会选择 Kubernetes Node IP 对应的网卡作为容器间跨节点通信的网卡并建立对应的隧道。

如果需要选择其他的网卡建立容器隧道，可以在安装脚本中修改：

```bash
IFACE=eth1
```

该选项支持以逗号分隔的正则表达式，例如 `ens[a-z0-9]*,eth[a-z0-9]*`。

安装后也可通过修改 `kube-ovn-cni` DaemonSet 的参数进行调整：

```yaml
args:
- --iface=eth1
```

如果每台机器的网卡名均不同，且没有固定规律，可以使用节点 annotation `ovn.kubernetes.io/tunnel_interface`
进行每个节点的逐一配置，拥有该 annotation 节点会覆盖 `iface` 的配置，优先使用 annotation。

```bash
kubectl annotate node no1 ovn.kubernetes.io/tunnel_interface=ethx
```

## 为不同子网指定封装网卡

除了全局默认的封装网卡配置外，Kube-OVN 还支持为不同子网指定使用主机不同的网卡 IP 进行 tunnel 封装，从而实现容器网络通过主机不同网卡进行转发。

### 前提条件

- 主机需要配置多块网卡，且各网卡均已配置 IP 地址。
- 各网卡对应的网络需要能够互通（同一网络平面内的主机之间）。
- 该功能仅支持 Overlay 类型子网。

### 工作原理

1. 用户在 Node 上通过注解声明多个网络平面及其对应的封装 IP。
2. 在 Subnet 中通过 `nodeNetwork` 字段指定该子网使用哪个网络平面。
3. kube-ovn-daemon 监听节点注解变化，将所有封装 IP 设置到 OVS。
4. 当 Pod 创建时，如果其所属子网配置了 `nodeNetwork`，则会为该 Pod 的 OVS 端口设置对应的封装 IP。

### 配置节点网络

在需要配置多网络平面的节点上，添加 `ovn.kubernetes.io/node_networks` 注解。注解值为 JSON 格式，key 为网络名称，value 为该网络对应的封装 IP。

```bash
kubectl annotate node <node-name> ovn.kubernetes.io/node_networks='{"storage": "192.168.100.10", "app": "172.16.0.10"}'
```

上述命令定义了两个网络平面：

- `storage`：使用 IP `192.168.100.10`（假设该 IP 配置在高速存储网卡上）
- `app`：使用 IP `172.16.0.10`（假设该 IP 配置在业务网卡上）

对于多节点集群，需要在每个节点上配置对应的网络注解，确保同一网络名称在不同节点上使用的是同一网络平面的 IP。

### 配置子网

创建子网时，通过 `spec.nodeNetwork` 字段指定该子网使用的网络平面：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: storage-subnet
spec:
  protocol: IPv4
  cidrBlock: 10.100.0.0/16
  gateway: 10.100.0.1
  nodeNetwork: storage
```

该配置表示 `storage-subnet` 子网下的 Pod 将使用 `storage` 网络平面进行 tunnel 封装。

如果不配置 `nodeNetwork` 字段，子网将使用默认的封装 IP（由 `IFACE` 参数指定的网卡 IP）。

### 验证配置

#### 检查 OVS 封装 IP 配置

在节点上执行以下命令，查看 OVS 配置的封装 IP：

```bash
ovs-vsctl get open . external-ids:ovn-encap-ip
```

输出应包含所有配置的封装 IP，例如：

```text
"192.168.1.10,192.168.100.10,172.16.0.10"
```

查看默认封装 IP：

```bash
ovs-vsctl get open . external-ids:ovn-encap-ip-default
```

#### 检查 Pod 端口的封装 IP

创建 Pod 后，可以检查 Pod 对应 OVS 端口的封装 IP 设置：

```bash
ovs-vsctl --columns=external_ids find interface external-ids:iface-id="<pod-name>.<namespace>"
```

如果子网配置了 `nodeNetwork`，输出中应包含 `encap-ip` 字段：

```text
external_ids        : {encap-ip="192.168.100.10", iface-id="test-pod.default", ...}
```

### 使用示例

以下是一个完整的存储网络分离示例：

#### 1. 配置节点网络注解

假设集群有两个节点，每个节点都有两块网卡：

- `eth0`：业务网卡，IP 分别为 `192.168.1.10` 和 `192.168.1.11`
- `eth1`：存储网卡，IP 分别为 `10.10.10.10` 和 `10.10.10.11`

```bash
kubectl annotate node node1 ovn.kubernetes.io/node_networks='{"storage": "10.10.10.10"}'
kubectl annotate node node2 ovn.kubernetes.io/node_networks='{"storage": "10.10.10.11"}'
```

#### 2. 创建存储子网

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: storage-net
spec:
  protocol: IPv4
  cidrBlock: 10.200.0.0/16
  gateway: 10.200.0.1
  nodeNetwork: storage
  namespaces:
  - storage-namespace
```

#### 3. 创建使用存储网络的 Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
  namespace: storage-namespace
spec:
  containers:
  - name: app
    image: docker.io/library/nginx:alpine
```

该 Pod 的网络流量将通过存储网卡（`eth1`）进行转发。

### 注意事项

1. 确保同一网络平面内的所有节点之间网络互通。
2. 节点注解中配置的 IP 必须是该节点上实际存在的有效 IP 地址。
3. 该功能仅适用于 Overlay 类型子网，Underlay 子网不支持此配置。如需配置 Underlay 网络，请参考 [Underlay 网络安装](../start/underlay.md)。
4. 如果子网未配置 `nodeNetwork`，或配置的网络名称在节点上不存在，将使用默认封装 IP。
5. 如果 Pod 调度到的节点上不存在子网指定的 `nodeNetwork` 对应的注解，Pod 将会运行失败。请确保所有可能调度到的节点都配置了相应的网络注解。
6. 在进行节点增加或节点网络调整时，需要及时更新对应节点的 `ovn.kubernetes.io/node_networks` 注解，避免 Pod 运行失败。
