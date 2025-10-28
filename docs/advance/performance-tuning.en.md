# Performance Tuning

To keep the installation simple and feature-complete, the default installation script for Kube-OVN does not have performance-specific optimizations.
If the applications are sensitive to latency and throughput, administrators can use this document to make specific performance optimizations.

The community will continue to iterate on the performance.
Some general performance optimizations have been integrated into the latest version,
so it is recommended to use the latest version to get better default performance.

For more on the process and methodology of performance optimization, please watch the video [Kube-OVN 容器性能优化之旅](https://www.bilibili.com/video/BV1zS4y1T73m?share_source=copy_web){: target="_blank" }.

## Common Misunderstandings about Network Performance

Performance tuning and comparison is an exciting topic, and performance data comparisons under different configurations can be fascinating, but all of this may have minimal effect in real application scenarios. Below are some common misconceptions about network performance to help you better judge whether network tuning is needed.

1. The latency introduced by CNI is about tens of nanoseconds per packet. If your application's request processing takes tens of milliseconds, even if CNI has no latency at all, the impact on application latency performance is minimal.
2. Common network performance tests are packet sending tests. If one network plugin needs 10ns to process each packet while another needs 20ns, there will be a double performance difference, but for real applications with tens of milliseconds processing time, the difference is not significant.
3. Contrary to first impressions, the bottleneck affecting network performance is usually the CPU. Better and more CPUs bring more significant performance improvements.
4. If you need extreme network performance, it's best to use network solutions like Macvlan or SR-IOV that adopt ultra-lightweight or hardware virtualization technologies.

## Benchmarking

> Because the hardware and software environments vary greatly, the performance test data provided here can only be used as a reference,
> and the actual test results may differ significantly from the results in this document.
> It is recommended to compare the performance test results before and after optimization,
> and the performance comparison between the host network and the container network.

### Overlay Performance Comparison before and after Optimization

*Environment:*

- Kubernetes: 1.22.0
- OS: CentOS 7
- Kube-OVN: 1.8.0 *Overlay* Mode
- CPU: Intel(R) Xeon(R) E-2278G
- Network: 2*10Gbps, xmit_hash_policy=layer3+4

We use `qperf -t 60 <server ip> -ub -oo msg_size:1 -vu tcp_lat tcp_bw udp_lat udp_bw`
to test the bandwidth and latency of TCP/UDP with 1-byte packets.

| Type               | tcp_lat (us) | udp_lat (us) | tcp_bw (Mb/s) | udp_bw(Mb/s) |
| ------------------ | -------------| -------------| --------------| -------------|
| Kube-OVN Default   | 25.7         | 22.9         | 27.1          | 1.59         |
| Kube-OVN Optimized | 13.9         | 12.9         | 27.6          | 5.57         |
| HOST Network       | 13.1         | 12.4         | 28.2          | 6.02         |

### Overlay and Underlay Comparison

Next, we compare the overlay and underlay performance of the optimized Kube-OVN at different packet sizes with the host network.

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

> In some cases the container network outperforms the host network, this is because the container network path is optimized to completely bypass netfilter.
> Due to the existence of `kube-proxy`, all packets in host network have to go through netfilter, which will lead to more CPU consumption,
> so that container network in some environments has better performance.

## Dataplane performance optimization methods

The optimization methods described here are related to the hardware and software environment and the desired functionality,
so please carefully understand the prerequisites for optimization before attempting it.

### CPU Performance Mode Tuning

In some environments the CPU is running in power saving mode, performance in this mode will be unstable and latency will increase significantly,
it is recommended to use the CPU's performance mode for more stable performance.

```bash
cpupower frequency-set -g performance
```

### NIC Hardware Queue Adjustment

In the case of increased traffic, a small buffer queue may lead to significant performance degradation due to a high packet loss rate and needs to be tuned.

Check the current NIC queue length:

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

Increase the queue length to the maximum:

```bash
ethtool -G eno1 rx 4096
ethtool -G eno1 tx 4096
```

### Optimize with tuned

[tuned](https://tuned-project.org/){: target="_blank" } can use a series of preconfigured profile files to perform system optimizations for a specific scenario.

For latency-first scenarios:

```bash
tuned-adm profile network-latency
```

For throughput-first scenarios:

```bash
tuned-adm profile network-throughput
```

### Interrupt Binding

We recommend disabling `irqbalance` and binding NIC interrupts to specific CPUs to avoid performance fluctuations caused by switching between multiple CPUs.

### Disable OVN LB

The L2 LB implementation of OVN requires calling the kernel's `conntrack` module and recirculate, resulting in a significant CPU overhead, which is tested to be around 20%.
For Overlay networks you can use `kube-proxy` to complete the service forwarding function for better Pod-to-Pod performance.
This can be turned off in `kube-ovn-controller` args:

```yaml
command:
- /kube-ovn/start-controller.sh
args:
...
- --enable-lb=false
...
```

> In Underlay mode `kube-proxy` cannot use iptables or ipvs to control container network traffic,
> if you want to disable the LB function, you need to confirm whether you do not need the Service function.

### Skip Conntrack Processing for Specific Target Addresses

In some scenarios, you may need to use OVN LB for Service forwarding, but also have traffic to specific destinations that doesn't require Service or NetworkPolicy processing. For example, Pods in Subnet A directly accessing addresses in Subnet B. To accelerate this traffic, you can configure `kube-ovn-controller` to skip conntrack processing for these destinations using the `--skip-conntrack-dst-cidrs` parameter:

```yaml
    --skip-conntrack-dst-cidrs="10.17.0.0/16,169.254.169.245/32"
```

### FastPath Kernel Module

Since the container network and the host network are on different network ns, the packets will pass through the netfilter module several times when they are transmitted across the host, which results in a CPU overhead of nearly 20%.
The `FastPath` module can reduce CPU overhead by bypassing netfilter, since in most cases applications within a container network do not need to use the functionality of the netfilter module.

> If you need to use the functions provided by netfilter such as iptables, ipvs, nftables, etc. in the container network, this module will disable the related functions.

Since kernel modules are kernel version dependent, it is not possible to provide a single kernel module artifact that adapts to all kernels.

You need to compile it manually, see [Compiling FastPath Module](./fastpath.md)

After obtaining the kernel module, you can load the `FastPath` module on each node
using `insmod kube_ovn_fastpath.ko` and verify that the module was loaded successfully using `dmesg`:

```bash
# dmesg
...
[619631.323788] init_module,kube_ovn_fastpath_local_out
[619631.323798] init_module,kube_ovn_fastpath_post_routing
[619631.323800] init_module,kube_ovn_fastpath_pre_routing
[619631.323801] init_module,kube_ovn_fastpath_local_in
...
```

### OVS Kernel Module Optimization

OVS flow processing including hashing, matching, etc. consumes about 10% of the CPU resources.
Some instruction sets on modern x86 CPUs such as `popcnt` and `sse4.2` can speed up the computation process,
but the kernel is not compiled with these options enabled.
It has been tested that the CPU consumption of flow-related operations is reduced to about 5%
when the corresponding instruction set optimizations are enabled.

Similar to the compilation of the `FastPath` module, it is not possible to provide a single kernel module artifact for all kernels.
Users need to compile it manually.

Before using this kernel module, please check if the CPU supports the following instruction set:

```bash
cat /proc/cpuinfo  | grep popcnt
cat /proc/cpuinfo  | grep sse4_2
```

#### Compile and Install in CentOS

Install the relevant compilation dependencies and kernel headers:

```bash
yum install -y gcc kernel-devel-$(uname -r) python3 autoconf automake libtool rpm-build openssl-devel
```

Compile the OVS kernel module and generate the corresponding RPM:

```bash
git clone -b branch-3.5 --depth=1 https://github.com/openvswitch/ovs.git
cd ovs
curl -s  https://github.com/kubeovn/ovs/commit/2d2c83c26d4217446918f39d5cd5838e9ac27b32.patch |  git apply
./boot.sh
./configure --with-linux=/lib/modules/$(uname -r)/build CFLAGS="-g -O2 -mpopcnt -msse4.2"
make rpm-fedora-kmod
cd rpm/rpmbuild/RPMS/x86_64/
```

Copy the RPM to each node and install:

```bash
rpm -i openvswitch-kmod-3.5.1-1.el7.x86_64.rpm
```

If you have previously started Kube-OVN and the older version of the OVS module has been loaded into the kernel.
It is recommended to reboot the machine to reload the new version of the kernel module.

#### Compile and Install in Ubuntu

Install the relevant compilation dependencies and kernel headers:

```bash
apt install -y autoconf automake libtool gcc build-essential libssl-dev
```

Compile the OVS kernel module and install:

```bash
git clone -b branch-3.5 --depth=1 https://github.com/openvswitch/ovs.git
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

If you have previously started Kube-OVN and the older version of the OVS module has been loaded into the kernel.
It is recommended to reboot the machine to reload the new version of the kernel module.

### Using STT Type Tunnel

!!! warning

    Open vSwitch upstream removed support for STT tunnels in version 3.6 [commit](https://github.com/openvswitch/ovs/commit/19b89416203f3b3b212fb01c30c81ea1b77624eb){: target="_blank" }. This solution will no longer receive upstream support in the future.

Common tunnel encapsulation protocols such as Geneve and Vxlan use the UDP protocol to encapsulate packets and are well supported in the kernel.
However, when TCP packets are encapsulated using UDP, the optimization and offload features of modern operating systems and
network cards for the TCP protocol do not work well, resulting in a significant drop in TCP throughput.
In some virtualization scenarios, due to CPU limitations, TCP packet throughput may even be a tenth of that of the host network.

STT provides an innovative tunneling protocol that uses TCP formatted header for encapsulation.
This encapsulation only emulates the TCP protocol header format without actually establishing a TCP connection,
but can take full advantage of the TCP optimization capabilities of modern operating systems and network cards.
In our tests TCP packet throughput can be improved several times, reaching performance levels close to those of the host network.

The STT tunnel is not pre-installed in the kernel and needs to be installed by compiling the OVS kernel module, which can be found in the previous section.

Enable STT tunnel:

```bash
kubectl set env daemonset/ovs-ovn -n kube-system TUNNEL_TYPE=stt

kubectl delete pod -n kube-system -lapp=ovs
```
