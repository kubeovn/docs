# 其他常见问题

为了更好的分析问题请先参考 [总体架构](../reference/architecture.md) 了解 Kube-OVN 的组件和组件之间的交互。

## 通用排查步骤

1. 判断网络链路问题：
    - 测试 Pod 和 Pod 之间是否互通
    - 测试 Pod 和宿主机之间是否互通
    - 测试 Pod 访问 Service 是否正常
    - 测试 Pod 解析域名是否正常
    - 测试 Pod 访问外部网络是否正常
    - 观察出问题节点 `kube-ovn-pinger` 日志，确认是否存在网络访问失败的情况
2. 检查各个组件日志，判断是否有错误日志输出
    - 检查 Pod 日志，确认是否存在网络访问失败的情况
    - 检查节点 kube-ovn-cni 日志，确认 CNI 是否存处理错误
    - 检查节点 ovs-ovn 日志，确认是否存在 OVS 处理错误
    - 检查 kube-ovn-controller 日志，确认是否存在控制器处理错误
    - 检查 ovn-central 日志，确认是否存在 OVN 处理错误
    - 检查节点 dmesg 日志，确认是否存在内核处理错误
    - 检查节点 `netstat -s` 日志，确认是否存在网络错误
3. 检查各个组件监控信息，判断是否存在 CPU, 内存和 IO 方面的监控异常

以上的日志和信息可通过 `kubectl ko logs` 命令进行收集

## Pod 创建失败，事件提示 IP 冲突

### 现象

Pod 无法进入 Running 状态，kubectl describe Pod 提示事件 `duplicate IPv4 address <ip> found on logical switch port <port>`

### 解决方法

1. 确认当前 Pod 为非固定 IP Pod，若为固定 IP 则说明 IP 已被占用，需要更换 IP 或删除已占用 IP Pod
2. 检查 kube-ovn-controller 日志，过滤冲突 IP 的申请和释放过程
3. 观察是否存在 kube-ovn-controller 重启或者切主过程导致 IP 回收错误
4. `kubectl ko nbctl show` 观察 OVN 数据库中实际分配端口和 IP 情况
5. 若 OVN 数据库中信息和实际 Kubernetes 信息不一致，存在残留 IP 端口，需要手动通过 `kubectl ko nbctl del-port <port>` 进行清理

## Pod 创建失败，事件提示 ping gateway failed

### 现象

Pod 无法进入 Running 状态，kubectl describe Pod 提示事件 `network <ip> with gateway <gw ip> is not ready for interface eth0 after 30 checks`

### 解决方法

1. `kubectl ko sbctl show` 确认 Pod 端口信息是否已经存在
2. 若信息不存在，收集 ovn-central 和 ovs-ovn 日志信息，观察是否存在错误，并重启 ovn-central 和 ovs-ovn 重试解决
3. 若信息存在，观察是否存在网络策略阻止 Pod 访问网关
4. 若为 Underlay 网络，询问网络管理员底层网络是否有安全限制，参考 [Underlay 网络安装](../start/underlay.md) 文档

## Pod 无法访问外部网络

### 现象

默认 VPC 下 Pod 在集群内访问正常，无法访问集群外部网络。

### 解决方法

1. 使用 `kubectl ko trace` 判断 OVN 逻辑流表链路上是否存在 ACL 限制
2. 若存在 ACL 限制，调整 ACL 策略
3. 若不存在 ACL 限制，查看 Subnet stats 信息，确认网关节点信息是否正确，且网关节点网络正常
4. 若网关节点信息不正确，或对应节点出现网络异常，修改 Subnet Spec 更新为新的网关节点
5. 收集 `kube-ovn-controller` 日志，确认是否存在网关切换的异常日志

## Pod IP 不在指定的 CIDR 内

### 现象

Pod 创建成功，但是 IP 不在指定的 CIDR 内。

### 解决方法

1. 查找主机路径的 `/etc/cni/net.d/` 目录下是否存在其他非 Kube-OVN 的 CNI 配置文件
2. 若存在，重命名该文件，或者删除该文件
3. 重启 kubelet 以及对应节点上的所有 Pod

## Debug Pod 无法正常创建

### 现象

kubectl debug 创建的 Pod 一直处于 ContainerCreating 状态，Pod Event 报错 network not ready 或 no address allocated

### 解决方法

创建 debug Pod 后，导出其 yaml 文件，删除 yaml 中的 Annotation：

```yaml
ovn.kubernetes.io/ip_address
ovn.kubernetes.io/mac_address
ovn.kubernetes.io/allocated
ovn.kubernetes.io/routed
```

删除 debug Pod，使用修改后的 yaml 创建新的 debug Pod。

## ARM 系统跨主机容器访问间歇失败

### 现象

ARM 系统和部分网卡 Offload 配合存在问题，会导致容器网络间歇故障。

使用 `netstat` 确认问题：

```bash
# netstat -us
IcmpMsg:
    InType0: 22
    InType3: 24
    InType8: 117852
    OutType0: 117852
    OutType3: 29
    OutType8: 22
Udp:
    3040636 packets received
    0 packets to unknown port received.
    4 packet receive errors
    602 packets sent
    0 receive buffer errors
    0 send buffer errors
    InCsumErrors: 4
UdpLite:
IpExt:
    InBcastPkts: 10244
    InOctets: 4446320361
    OutOctets: 1496815600
    InBcastOctets: 3095950
    InNoECTPkts: 7683903
```

若存在 `InCsumErrors`，且随着访问失败增加，可确认是该问题。

### 解决方法

根本解决需要和操作系统以及对应网卡厂商沟通，更新系统和驱动。临时解决可先关闭物理
网卡的 `tx offload` 但是会导致 TCP 性能有较明显下降。

```bash
ethtool -K eth0 tx off
```

经社区用户反馈 CentOS 7 和麒麟操作系统都可能出现类似问题，其中麒麟操作系统在 `4.19.90-25.16.v2101` 内核后可以解决该问题。

## Pod 访问 Service 不通

### 现象

Pod 内无法访问 Service 对应的服务，`dmesg` 显示异常：

```bash
netlink: Unknown conntrack attr (type=6, max=5)
openvswitch: netlink: Flow actions may not be safe on all matching packets.
```

该日志说明内核内 OVS 版本过低不支持对应 NAT 操作。

### 解决方法

1. 升级内核模块或手动编译 OVS 内核模块。
2. 若只使用 Overlay 网络可以更改 `kube-ovn-controller` 启动参数设置 `--enable-lb=false`
关闭 OVN LB 使用 kube-proxy 进行 Service 转发。

## ovn-central 出现频繁选主

### 现象

从 v1.11.x 版本开始，1w Pod 以上的集群，如果 OVN NB 或者 SB 出现频繁选主的情况，可能原因是 Kube-OVN 周期进行了 ovsdb-server/compact 动作，影响到选主逻辑。

### 解决方法

可以给 ovn-central 配置环境变量如下，关闭 compact：

```yaml
- name: ENABLE_COMPACT
  value: "false"
```
