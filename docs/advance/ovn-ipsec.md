# 使用 ovn ipsec 加密 ovn 内部节点之间的通信

## 配置证书和密钥

OVN chassis 使用 CA 签名证书对等机箱进行身份验证，以构建 IPsec 隧道，本文档使用 ovs 的工具 ovs-pki 生成单独的证书和密钥

### 启动 ipsec 服务

对 daemonset ovs-ovn 的 pod 执行如下操作：

```bash
kubectl exec -it $(kubectl get pod -l app=ovs -n kube-system -o jsonpath='{.items[*].metadata.name}') -n kube-system -- service openvswitch-ipsec start
kubectl exec -it $(kubectl get pod -l app=ovs -n kube-system -o jsonpath='{.items[*].metadata.name}') -n kube-system -- service ipsec start
```

### 初始化 CA 

找到任意一个 daemonset ovs-ovn 的 pod ，在 pod 里面执行

```bash
kubectl exec -it ovs-ovn-test1 -n kube-system -- ovs-pki init
```

### 生成密钥和证书请求

在每个 daemonset ovs-ovn 下执行

```bash
kubectl exec -it ovs-ovn-testx -n kube-system -- ovs-vsctl list Open_vSwitch
```


