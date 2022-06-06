# 手动编译 FastPath 模块

经过数据平面的性能 Profile，Netfilter 在容器内和宿主机上的相关处理消耗了 20% 左右的 CPU 资源，FastPath 模块可以绕过 Netfilter 从而
降低 CPU 的消耗和延迟，并提升吞吐量。本文档将介绍如何手动编译 FastPath 模块。

## 下载相关内核模块代码

```bash
git clone --depth=1 https://github.com/kubeovn/kube-ovn.git
```

## 安装依赖

这里以 CentOS 为例下载相关依赖

```bash
yum install -y kernel-devel-$(uname -r) gcc elfutils-libelf-devel
```

## 编译相关模块

针对 3.x 的内核：
```bash
cd kube-ovn/fastpath
make all
```

针对 4.x 的内核
```bash
cd kube-ovn/fastpath/4.18
cp ../Makefile .
make all
```

## 安装内核模块

将 `kube_ovn_fastpath.ko` 复制到每个需要性能优化的节点，执行下列命令：

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

如需卸载模块，可使用下列命令：

```bash
rmmod kube_ovn_fastpath.ko
```

> 该模块在机器重启后不会自动加载，如需自动加载请根据系统弄配置编写相应自启动脚本。
