# 性能调优

为了保持安装的简单和功能的完备，Kube-OVN 的默认安装脚本并没有对性能针对性的优化。如果应用对延迟和吞吐量敏感，
管理员可以通过本文档对性能进行针对性优化。

社区会不断迭代控制面板和优化面的性能，部分通用性能优化已经集成到最新版本，建议使用最新版本获得更好的默认性能。

更多关于性能优化的过程和方法论，可以观看视频分享：[Kube-OVN 容器性能优化之旅](https://www.bilibili.com/video/BV1zS4y1T73m?share_source=copy_web)。

## 基准测试

> 由于软硬件环境的差异极大，这里提供的性能测试数据只能作为参考，实际测试结果会和本文档中的结果存在较大差异。
> 建议比较优化前后的性能测试结果，和宿主机网络和容器网络的性能比较。

### Overlay 优化前后性能对比

*环境信息：*

- Kubernetes: 1.22.0
- OS: CentOS 7
- Kube-OVN: 1.8.0 *Overlay* 模式
- CPU: Intel(R) Xeon(R) E-2278G
- Network: 2*10Gbps, xmit_hash_policy=layer3+4

我们使用 `qperf -t 60 <server ip> -ub -oo msg_size:1 -vu tcp_lat tcp_bw udp_lat udp_bw` 测试
 1 字节小包下 tcp/udp 的带宽和延迟，分别测试优化前，优化后以及宿主机网络的性能：

| Type               | tcp_lat (us) | udp_lat (us) | tcp_bw (Mb/s) | udp_bw(Mb/s) |
| ------------------ | -------------| -------------| --------------| -------------|
| Kube-OVN Default   | 25.7         | 22.9         | 27.1          | 1.59         |
| Kube-OVN Optimized | 13.9         | 12.9         | 27.6          | 5.57         |
| HOST Network       | 13.1         | 12.4         | 28.2          | 6.02         |

### Overlay， Underlay 模式性能对比

下面我们会比较优化后 Kube-OVN 在不同包大小下的 Overlay 和 Underlay 性能，并和宿主机网络做比较。

*Environment*:

- Kubernetes: 1.22.0
- OS: CentOS 7
- Kube-OVN: 1.8.0
- CPU: AMD EPYC 7402P 24-Core Processor
- Network: Intel Corporation Ethernet Controller XXV710 for 25GbE SFP28

`qperf -t 60 <server ip> -ub -oo msg_size:1 -vu tcp_lat tcp_bw udp_lat udp_bw`

| Type               | tcp_lat (us) | udp_lat (us) | tcp_bw (Mb/s) | udp_bw(Mb/s) |
| ------------------ | -------------| -------------| --------------| -------------|
| Kube-OVN Overlay   | 15.2         | 14.6         | 23.6          | 2.65         |
| Kube-OVN Underlay  | 14.3         | 13.8         | 24.2          | 3.46         |
| HOST Network       | 16.6         | 15.4         | 24.8          | 2.64         |

`qperf -t 60 <server ip> -ub -oo msg_size:1K -vu tcp_lat tcp_bw udp_lat udp_bw`

| Type               | tcp_lat (us) | udp_lat (us) | tcp_bw (Gb/s) | udp_bw(Gb/s) |
| ------------------ | -------------| -------------| --------------| -------------|
| Kube-OVN Overlay   | 16.5         | 15.8         | 10.2          | 2.77         |
| Kube-OVN Underlay  | 15.9         | 14.5         | 9.6           | 3.22         |
| HOST Network       | 18.1         | 16.6         | 9.32          | 2.66         |

`qperf -t 60 <server ip> -ub -oo msg_size:4K -vu tcp_lat tcp_bw udp_lat udp_bw`

| Type               | tcp_lat (us) | udp_lat (us) | tcp_bw (Gb/s) | udp_bw(Gb/s) |
| ------------------ | -------------| -------------| --------------| -------------|
| Kube-OVN Overlay   | 34.7         | 41.6         | 16.0          | 9.23         |
| Kube-OVN Underlay  | 32.6         | 44           | 15.1          | 6.71         |
| HOST Network       | 35.9         | 45.9         | 14.6          | 5.59         |

> 在部分情况下容器网络的性能会优于宿主机网络，这是优于经过优化后容器网络路径完全绕过了 netfilter，
> 而宿主机网络由于 `kube-proxy` 的存在所有数据包均需经过 netfilter，会导致在一些环境下容器网络
> 的消耗相对更小，因此会有更好的性能表现。

## 数据平面性能优化方法

这里介绍的优化方法和软硬件环境以及所需要的功能相关，请仔细了解优化的前提条件再进行尝试。

### CPU 性能模式调整

部分环境下 CPU 运行在节能模式，该模式下性能表现将会不稳定，延迟会出现明显增加，建议使用 CPU 的性能模式获得更稳定的性能表现：

```bash
cpupower frequency-set -g performance
```

### 网卡硬件队列调整

在流量增大的情况下，缓冲队列过短可能导致较高的丢包率导致性能显著下降，需要进行调整

检查当前网卡队列长度：

```bash
# ethtool -g eno1
 Ring parameters for eno1:
 Pre-set maximums:
 RX:             4096
 RX Mini:        0
 RX Jumbo:       0
 TX:             4096
 Current hardware settings:
 RX:             255
 RX Mini:        0
 RX Jumbo:       0
 TX:             255
```

增加队列长度至最大值：

```bash
ethtool -G eno1 rx 4096
ethtool -G eno1 tx 4096
```

### 使用 tuned 优化系统参数

[tuned](https://tuned-project.org/) 可以使用一系列预置的 profile 文件保存了针对特定场景的一系列系统优化配置。

针对延迟优先场景：

```bash
tuned-adm profile network-latency
```

针对吞吐量优先场景：

```bash
tuned-adm profile network-throughput
```

### 中断绑定

我们推荐禁用 `irqbalance` 并将网卡中断和特定 CPU 进行绑定，来避免在多个 CPU 之间切换导致的性能波动。

### 关闭 OVN LB

OVN 的 L2 LB 实现过程中需要调用内核的 `conntrack` 模块并进行 recirculate 导致大量的 CPU 开销，经测试该功能会带来 20% 左右的 CPU 开销，
在 Overlay 网络模式下可以使用 `kube-proxy` 完成 Service 转发功能，获得更好的 Pod-to-Pod 性能。可以在 `kube-ovn-controller` 中关闭该功能：

```yaml
command:
- /kube-ovn/start-controller.sh
args:
...
- --enable-lb=false
...
```

> Underlay 模式下 `kube-proxy` 无法使用 iptables 或 ipvs 控制容器网络流量，如需关闭 LB 功能需要确认是否不需要 Service 功能。

### 内核 FastPath 模块

由于容器网络和宿主机网络在不同的 network ns，数据包在跨宿主机传输时会多次经过 netfilter 模块，会带来近 20% 的 CPU 开销。由于大部分情况下
容器网络内应用无须使用 netfilter 模块的功能，`FastPath` 模块可以绕过 netfilter 降低 CPU 开销。

> 如容器网络内需要使用 netfilter 提供的功能如 iptables，ipvs，nftables 等，该模块会使相关功能失效。

由于内核模块和内核版本相关，无法提供一个单一适应所有内核的内核模块制品。

用户需要手动进行编译，方法参考[手动编译 FastPath 模块](./fastpath.md)

获得内核模块后可在每个节点使用 `insmod kube_ovn_fastpath.ko` 加载 `FastPath` 模块，并使用 `dmesg` 验证模块加载成功：

```bash
# dmesg
...
[619631.323788] init_module,kube_ovn_fastpath_local_out
[619631.323798] init_module,kube_ovn_fastpath_post_routing
[619631.323800] init_module,kube_ovn_fastpath_pre_routing
[619631.323801] init_module,kube_ovn_fastpath_local_in
...
```

### OVS 内核模块优化

OVS 的 flow 处理包括哈希计算，匹配等操作会消耗大约 10% 左右的 CPU 资源。现代 x86 CPU 上的一些指令集例如 `popcnt` 和 `sse4.2` 可以
加速相关计算过程，但内核默认编译未开启相关选项。经测试在开启相应指令集优化后，flow 相关操作 CPU 消耗将会降至 5% 左右。

和 `FastPath` 模块的编译类似，由于内核模块和内核版本相关，无法提供一个单一适应所有内核的内核模块制品，用户需要手动编译。

使用该内核模块前请先确认 CPU 是否支持相关指令集：

```bash
cat /proc/cpuinfo  | grep popcnt
cat /proc/cpuinfo  | grep sse4_2
```

#### CentOS 下编译安装

安装相关编译依赖和内核头文件：

```bash
yum install -y gcc kernel-devel-$(uname -r) python3 autoconf automake libtool rpm-build openssl-devel
```

编译 OVS 内核模块并生成对应 RPM 文件:

```bash
git clone -b branch-2.17 --depth=1 https://github.com/openvswitch/ovs.git
cd ovs
curl -s  https://github.com/kubeovn/ovs/commit/2d2c83c26d4217446918f39d5cd5838e9ac27b32.patch |  git apply
./boot.sh
./configure --with-linux=/lib/modules/$(uname -r)/build CFLAGS="-g -O2 -mpopcnt -msse4.2"
make rpm-fedora-kmod
cd rpm/rpmbuild/RPMS/x86_64/
```

复制 RPM 到每个节点并进行安装：

```bash
rpm -i openvswitch-kmod-2.15.2-1.el7.x86_64.rpm
```

若之前已经启动过 Kube-OVN，旧版本 OVS 模块已加载至内核，建议重启机器重新加载新版内核模块。

#### Ubuntu 下编译安装

安装相关编译依赖和内核头文件：

```bash
apt install -y autoconf automake libtool gcc build-essential libssl-dev
```

编译 OVS 内核模块并安装：

```bash
apt install -y autoconf automake libtool gcc build-essential libssl-dev

git clone -b branch-2.17 --depth=1 https://github.com/openvswitch/ovs.git
cd ovs
curl -s  https://github.com/kubeovn/ovs/commit/2d2c83c26d4217446918f39d5cd5838e9ac27b32.patch |  git apply
./boot.sh
./configure --prefix=/usr/ --localstatedir=/var --enable-ssl --with-linux=/lib/modules/$(uname -r)/build
make -j `nproc`
make install
make modules_install

cat > /etc/depmod.d/openvswitch.conf << EOF
override openvswitch * extra
override vport-* * extra
EOF

depmod -a
cp debian/openvswitch-switch.init /etc/init.d/openvswitch-switch
/etc/init.d/openvswitch-switch force-reload-kmod
```

若之前已经启动过 Kube-OVN，旧版本 OVS 模块已加载至内核，建议重启机器重新加载新版内核模块。

### 使用 STT 类型隧道

常见的隧道封装协议例如 Geneve 和 Vxlan 使用 UDP 协议对数据包进行封装，在内核中有良好的支持。但是当使用 UDP 封装 TCP 数据包时，
现代操作系统和网卡针对 TCP 协议的优化和 offload 功能将无法顺利工作，导致 TCP 的吞吐量出现显著下降。在虚拟化场景下由于 CPU 的限制，
TCP 大包的吞吐量甚至可能只有宿主机网络的十分之一。

STT 提供了一种创新式的使用 TCP 格式数据包进行封装的隧道协议，该封装只是模拟了 TCP 协议的头部格式，并没有真正建立 TCP 连接，但是可以
充分利用现代操作系统和网卡的 TCP 优化能力。在我们的测试中 TCP 大包的吞吐量能有数倍的提升，达到接近宿主机网络的性能水平。

STT 隧道并没有预安装在内核内，需要通过编译 OVS 内核模块来安装，OVS 内核模块的编译方法可以参考上一节。

STT 隧道开启：

```bash
kubectl set env daemonset/ovs-ovn -n kube-system TUNNEL_TYPE=stt

kubectl delete pod -n kube-system -lapp=ovs
```
