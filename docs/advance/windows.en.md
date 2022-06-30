# Windows Support

Kube-OVN 支持包含 Windows 系统节点的 Kubernetes 集群网络，可以将 Windows 容器的网络统一接入进行管理。

## 前提条件

- 参考 [Adding Windows nodes](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/adding-windows-nodes/) 增加 Windows 节点。
- Windows 节点必须安装 KB4489899 补丁以使 Overlay/VXLAN 网络正常工作，建议更新系统至最新版本。
- Windows 节点必须安装 Hyper-V 及管理工具。
- 由于 Windows 限制隧道封装只能使用 Vxlan 模式。
- 暂不支持 SSL，IPv6，双栈，QoS 功能。
- 暂不支持动态子网，动态隧道接口功能，需在安装 Windows 节点前完成子网创建，并固定网络接口。
- 不支持多个 `ProviderNetwork`，且无法动态调整桥接接口配置。

## 安装 OVS

由于上游 OVN 和 OVS 对 Windows 容器支持存在一些问题，需要使用 Kube-OVN 提供的经过修改的安装包进行安装。

使用以下命令打开 Windows 节点的 `TESTSIGNING` 启动项，执行成功后需要重启系统生效：

```bash
bcdedit /set LOADOPTIONS DISABLE_INTEGRITY_CHECKS
bcdedit /set TESTSIGNING ON
bcdedit /set nointegritychecks ON
```

在 Windows 节点下载 [Windows 安装包](https://github.com/kubeovn/kube-ovn/releases/download/v1.10.0/kube-ovn-win64.zip)并解压安装。

安装完成后确认服务正常运行：
```bash
PS > Get-Service | findstr ovs
Running  ovsdb-server  Open vSwitch DB Service
Running  ovs-vswitchd  Open vSwitch Service
```

## 安装 Kube-OVN

在 Windows 节点下载安装脚本 [install.ps1](https://github.com/kubeovn/kube-ovn/blob/release-1.10/dist/windows/install.ps1)。

补充相关参数并执行：
```bash
.\install.ps1 -KubeConfig C:\k\admin.conf -ApiServer https://192.168.140.180:6443 -ServiceCIDR 10.96.0.0/12
```

默认情况下, Kube-OVN 使用节点 IP 所在的网卡作为隧道接口。
如果需要使用其它网卡，需要在安装前给节点添加指定的 Annotation，如 `ovn.kubernetes.io/tunnel_interface=Ethernet1`。
