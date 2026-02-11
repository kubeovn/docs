# 手动编译 FastPath 模块

经过数据平面的性能 Profile，`Netfilter` 在容器内和宿主机上的相关处理消耗了 20% 左右的 CPU 资源，FastPath 模块可以绕过 `Netfilter` 从而
降低 CPU 的消耗和延迟，并提升吞吐量。本文档将介绍如何手动编译 FastPath 模块。

## 下载相关内核模块代码

```bash
git clone --depth=1 https://github.com/kubeovn/kube-ovn.git
```

## 安装依赖

针对 RPM 系统（如 CentOS、RHEL）：

```bash
yum install -y kernel-devel-$(uname -r) gcc elfutils-libelf-devel
```

针对 DEB 系统（如 Ubuntu、Debian）：

```bash
apt install -y linux-headers-$(uname -r) build-essential
```

## 编译相关模块

针对 3.x 的内核：

```bash
cd kube-ovn/fastpath/3.x
make all
```

针对 4.x ~ 6.x 的内核：

```bash
cd kube-ovn/fastpath/4.x-6.x
make all
```

## 安装内核模块

将 `kube_ovn_fastpath.ko` 复制到每个需要性能优化的节点，并执行以下命令安装：

```bash
insmod kube_ovn_fastpath.ko
```

使用 `dmesg` 确认安装成功：

```bash
# dmesg
[619631.323788] init_module,kube_ovn_fastpath_local_out
[619631.323798] init_module,kube_ovn_fastpath_post_routing
[619631.323800] init_module,kube_ovn_fastpath_pre_routing
[619631.323801] init_module,kube_ovn_fastpath_local_in
```

如需卸载模块，可使用以下命令：

```bash
rmmod kube_ovn_fastpath.ko
```

> 该模块在机器重启后不会自动加载，如需自动加载请根据系统配置编写相应自启动脚本。
