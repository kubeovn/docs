# 其他常见问题

## 麒麟 ARM 系统跨主机容器访问间歇失败

### 现象

麒麟 ARM 系统和部分国产化网卡 offload 配合存在问题，会导致容器网络间歇故障。

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

根本解决需要和麒麟以及对应网卡厂商沟通，更新系统和驱动。临时解决可先关闭物理
网卡的 `tx offload` 但是会导致 tcp 性能有较明显下降。

```bash
ethtool -K eth0 tx off
```

经社区反馈使用 `4.19.90-25.16.v2101` 内核后可以解决该问题。

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
