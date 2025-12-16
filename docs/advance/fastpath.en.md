# Compile FastPath Module

After a data plane performance profile, `netfilter` consumes about 20% of CPU resources for related processing within the container and on the host.
The FastPath module can bypass `netfilter` to reduce CPU consumption and latency, and increase throughput.
This document will describe how to compile the FastPath module manually.

## Download Related Code

```bash
git clone --depth=1 https://github.com/kubeovn/kube-ovn.git
```

## Install Dependencies

Here is an example of CentOS dependencies to download:

```bash
yum install -y kernel-devel-$(uname -r) gcc elfutils-libelf-devel
```

## Compile the Module

For the 3.x kernel:

```bash
cd kube-ovn/fastpath
make all
```

For the 4.x kernel:

```bash
cd kube-ovn/fastpath/4.18
cp ../Makefile .
make all
```

## Install the Kernel Module

Copy `kube_ovn_fastpath.ko` to each node that needs performance optimization, and run the following command:

```bash
insmod kube_ovn_fastpath.ko
```

Use `dmesg` to confirm successful installation:

```bash
# dmesg
[619631.323788] init_module,kube_ovn_fastpath_local_out
[619631.323798] init_module,kube_ovn_fastpath_post_routing
[619631.323800] init_module,kube_ovn_fastpath_pre_routing
[619631.323801] init_module,kube_ovn_fastpath_local_in
```

To uninstall a module, use the following command.

```bash
rmmod kube_ovn_fastpath.ko
```

> This module will not be loaded automatically after machine reboot. If you want to load it automatically, please write
> the corresponding autostart script according to the system configuration.
