# 卸载

如果需要删除 Kube-OVN 并更换其他网络插件，请按照下列的步骤删除对应的 Kube-OVN 组件以及 OVS 配置，以避免对其他网络插件产生干扰。
也欢迎提 issue 联系我们反馈不使用 Kube-OVN 的原因帮助我们改进。

## 删除在 Kubernetes 中创建的资源

下载下面的脚本，执行脚本删除在 Kubernetes 中创建的资源

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/release-1.9/dist/images/cleanup.sh
bash cleanup.sh
```

## 清理主机上的日志和配置文件

在每台机器上执行下列操作，清理 ovsdb 以及 openvswitch 保存的配置
```bash
rm -rf /var/run/openvswitch
rm -rf /var/run/ovn
rm -rf /etc/origin/openvswitch/
rm -rf /etc/origin/ovn/
rm -rf /etc/cni/net.d/00-kube-ovn.conflist
rm -rf /etc/cni/net.d/01-kube-ovn.conflist
rm -rf /var/log/openvswitch
rm -rf /var/log/ovn
```
## 重启节点

重启机器确保对应的网卡信息，iptable/ipset 规则得以清除，避免对其他网络插件的影响

```bash
reboot
```
