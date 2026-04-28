# 使用 IPsec 加密节点间通信

Kube-OVN 自 v1.13.0 起支持基于 OVN/OVS 内置 IPsec 能力对节点间的隧道（Geneve/Vxlan/STT）进行端到端加密。

## 前置条件

- 节点之间允许 UDP 500（IKE）和 UDP 4500（NAT-T）放行。
- 内核启用 `xfrm`/`af_key` 等模块，发行版自带 strongSwan/libreswan 之一即可。

## 加密流程

`kube-ovn-cni` 启动时会发起 CertificateSigningRequest，由 `kube-ovn-controller` 自动 approve 并签发证书；之后 `kube-ovn-cni` 利用该证书写入 IPsec 配置并启动 ipsec 进程。

## 启用 IPsec

将 `kube-ovn-controller` Deployment 与 `kube-ovn-cni` DaemonSet 的启动参数 `--enable-ovn-ipsec=false` 改为 `--enable-ovn-ipsec=true`，或在安装脚本中设置：

```bash
ENABLE_OVN_IPSEC=true
```

## 使用 cert-manager 签发证书（可选）

如果集群中已有 [cert-manager](https://cert-manager.io/)，并希望由其负责 IPsec 证书的发放和轮转，可同时打开 `--cert-manager-ipsec-cert=true`。开启后 kube-ovn-cni 会基于 cert-manager 颁发的证书申请 IPsec 证书，无需走 Kube-OVN 自带的内嵌 CA。

```yaml
args:
- --enable-ovn-ipsec=true
- --cert-manager-ipsec-cert=true
```

## 验证与排查

- 在任意节点的 `kube-ovn-cni` 容器内执行 `ovs-appctl ipsec/show`，可查看与其他节点的 IPsec 隧道、SA、SPI 等信息。
- 通过 `kubectl get csr` 可看到来自 kube-ovn-cni 的 CSR；如果某节点 IPsec 未生效，先确认其 CSR 已被 approve（必要时检查 controller 日志中 `signer.go` 相关条目）。
- 关闭 IPsec 时需要将上述参数改为 `false`，控制器会清理对应的 IPsec 配置；若节点上仍有残留 SA，重启 `kube-ovn-cni` Pod 即可。
