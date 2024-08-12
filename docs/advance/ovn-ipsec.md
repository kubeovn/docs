# 使用 IPsec 加密节点间通信

该功能从 v1.13.0 后支持，同时需要保证主机 UDP 500 和 4500 端口可用。

## 加密流程

kube-ovn-cni 负责将证书申请，会创建一个 certificatesigningrequest 给 kube-ovn-controller，kube-ovn-controller 会自动 approve 证书申请，然后 kube-ovn-cni 会根据证书生成 ipsec 配置文件，最后启动 ipsec 进程。

## 配置 IPsec

将 kube-ovn-controller 和 kube-ovn-cni 中的 args `--enable-ovn-ipsec=false` 修改为 `--enable-ovn-ipsec=true`。
