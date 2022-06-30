# Prerequisites

Kube-OVN is a CNI-compliant network system that depends on the Kubernetes environment and 
the corresponding kernel network module for its operation.
Below are the operating system and software versions tested, 
the environment configuration and the ports that need to be opened.

## Software Version
- Kubernetes >= 1.16，1.19 and above is recommended.
- Docker >= 1.12.6, Containerd >= 1.3.4.
- OS: CentOS 7/8, Ubuntu 16.04/18.04/20.04.
- For other Linux distributions, please make sure `geneve`, `openvswitch`, `ip_tables` and `iptable_nat` kernel modules exist.

*Attention*：

1. For CentOS kernel version 3.10.0-862 bug exists in `netfilter` modules that lead Kube-OVN embed nat and lb failure.Please update kernel and check [Floating IPs broken after kernel upgrade to Centos/RHEL 7.5 - DNAT not working](https://bugs.launchpad.net/neutron/+bug/1776778).
2. For kernel version 4.4, the related `openvswitch` module has some issues for ct，please update kernel version or manually compile `openvswitch` kernel module.
3. When building Geneve tunnel IPv6 in kernel should be enabled，check the kernel bootstrap options with `cat /proc/cmdline`.Check [Geneve tunnels don't work when ipv6 is disabled](https://bugs.launchpad.net/ubuntu/+source/linux/+bug/1794232) for the detail bug info.

## Environment Setup
- Kernel should enable IPv6, if kernel bootstrap options contain `ipv6.disable=1`, it should be set to `0`.
- `kube-proxy` works, Kube-OVN can visit `kube-apiserver` from Service ClusterIP.
- Make sure kubelet enabled `CNI` and find cni-bin and cni-conf in default directories, kubelet bootstrap options should contain `--network-plugin=cni --cni-bin-dir=/opt/cni/bin --cni-conf-dir=/etc/cni/net.d`.
- Make sure no other CNI installed or has been removed，check if any config files still exist in`/etc/cni/net.d/`.

## Ports Need Open
| Component            | Port                                           | Usage                               |
|----------------------|------------------------------------------------|-------------------------------------|
| ovn-central          | 6641/tcp, 6642/tcp, 6643/tcp, 6644/tcp         | ovn-db and raft server listen ports |
| ovs-ovn	             | Geneve 6081/udp, STT 7471/tcp, Vxlan 4789/udp  | tunnel ports                        |
| kube-ovn-controller  | 10660/tcp                                      | metrics port                        |
| kube-ovn-daemon      | 10665/tcp                                      | metrics port                        |
| kube-ovn-monitor     | 10661/tcp                                      | metrics port                        |
