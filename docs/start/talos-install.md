# Talos 安装

[Talos Linux](https://github.com/siderolabs/talos) 是为 Kubernetes 构建的现代 Linux 发行版。

## 通过 Helm Chart 部署 Kube-OVN

您可以通过以下命令在 Talos Linux 集群上部署 Kube-OVN：

```shell
helm install kube-ovn kubeovn/kube-ovn --wait \
    -n kube-system \
    --version {{ variables.version }} \
    --set OVN_DIR=/var/lib/ovn \
    --set OPENVSWITCH_DIR=/var/lib/openvswitch \
    --set DISABLE_MODULES_MANAGEMENT=true \
    --set cni_conf.MOUNT_LOCAL_BIN_DIR=false
```

如果您希望使用 Underlay 作为默认网络，可以通过 Helm 命令传入相关的 Chart 参数。示例如下：

```shell
helm install kubeovn kubeovn/kube-ovn --wait \
    -n kube-system \
    --version {{ variables.version }} \
    --set OVN_DIR=/var/lib/ovn \
    --set OPENVSWITCH_DIR=/var/lib/openvswitch \
    --set DISABLE_MODULES_MANAGEMENT=true \
    --set cni_conf.MOUNT_LOCAL_BIN_DIR=false \
    --set networking.NETWORK_TYPE=vlan \
    --set networking.vlan.VLAN_INTERFACE_NAME=enp0s5f1 \
    --set networking.vlan.VLAN_ID=0 \
    --set networking.NET_STACK=ipv4 \
    --set-json networking.EXCLUDE_IPS='"172.99.99.11..172.99.99.99"' \
    --set-json ipv4.POD_CIDR='"172.99.99.0/24"' \
    --set-json ipv4.POD_GATEWAY='"172.99.99.1"'
```

!!! note
    VLAN、Bond、Bridge 等类型的虚拟网卡不可用作 Underlay 网络的节点网卡。Underlay 使用的物理网卡需要在 Talos 配置中将其设置为 `ignore=true`。示例如下：
    ```yaml
    machine:
      network:
        interfaces:
          - interface: enp0s5f1
            ignore: true
    ```
