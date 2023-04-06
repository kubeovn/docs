# 使用 ovn ipsec 加密 ovn 内部节点之间的通信

## 配置证书和密钥

OVN chassis 使用 CA 签名证书对等机箱进行身份验证，以构建 IPsec 隧道，本文档使用 ovs 的工具 ovs-pki 生成单独的证书和密钥

### 启动 ipsec 服务

对 daemonset ovs-ovn 的 pod 执行如下操作：

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- service openvswitch-ipsec start
kubectl exec -it ovs-ovn-pp566 -n kube-system -- service openvswitch-ipsec start

kubectl exec -it ovs-ovn-4v7ql -n kube-system -- service ipsec start
kubectl exec -it ovs-ovn-4v7ql -n kube-system -- service ipsec start
```

### 初始化 CA 

找到任意一个 daemonset ovs-ovn 的 pod 作为 CA，在 pod 里面执行

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- ovs-pki init
```

### 生成密钥和证书请求

在每个 daemonset ovs-ovn 下执行如下命令，找到 system-id ：

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- ovs-vsctl get Open_vSwitch . external_ids
kubectl exec -it ovs-ovn-4v7ql -n kube-system -- ovs-vsctl get Open_vSwitch . external_ids
```

然后执行如下命令，生成认证请求和密钥两个文件，并将文件放进相应目录：

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- ovs-pki req -u 1a7353d2-8735-4f7a-a19e-30ed7bb351d8
kubectl exec -it ovs-ovn-pp566 -n kube-system -- mv 1a7353d2-8735-4f7a-a19e-30ed7bb351d8-privkey.pem /etc/ipsec.d/private/
kubectl exec -it ovs-ovn-pp566 -n kube-system -- mv 1a7353d2-8735-4f7a-a19e-30ed7bb351d8-req.pem /etc/ipsec.d/reqs/

kubectl exec -it ovs-ovn-4v7ql -n kube-system -- ovs-pki req -u 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6
kubectl exec -it ovs-ovn-4v7ql -n kube-system -- mv 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-privkey.pem /etc/ipsec.d/private/
kubectl exec -it ovs-ovn-4v7ql -n kube-system -- mv 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-req.pem /etc/ipsec.d/reqs/
```


### 生成公钥证书

将各个节点上生成的认证请求文件（后缀是 req.pem 的文件）复制到 CA 节点的 /kube-ovn 目录下，然后执行签署操作生成证书，然后再把证书 copy 回原节点

非 CA 节点命令如下：
```bash
kubectl cp ovs-ovn-4v7ql:/etc/ipsec.d/reqs/63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-req.pem 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-req.pem -n kube-system
kubectl cp 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-req.pem ovs-ovn-pp566:/kube-ovn/ -n kube-system

kubectl exec -it ovs-ovn-pp566 -n kube-system -- ovs-pki sign -b 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6 switch

kubectl cp ovs-ovn-pp566:/kube-ovn/63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-cert.pem 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-cert.pem -n kube-system
kubectl cp 63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-cert.pem ovs-ovn-4v7ql:/etc/ipsec.d/certs/ -n kube-system

```

CA 节点的证书在本地生成，不需要跨节点复制，命令如下:

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- ovs-pki sign -b /etc/ipsec.d/reqs/1a7353d2-8735-4f7a-a19e-30ed7bb351d8 switch
kubectl exec -it ovs-ovn-pp566 -n kube-system -- mv /etc/ipsec.d/reqs/1a7353d2-8735-4f7a-a19e-30ed7bb351d8-cert.pem /etc/ipsec.d/certs/

```

### 获取 CA 证书

对于非 CA 节点命令如下：

```bash
kubectl cp ovs-ovn-pp566:/var/lib/openvswitch/pki/switchca/cacert.pem cacert.pem -n kube-system
kubectl cp cacert.pem ovs-ovn-4v7ql:/etc/ipsec.d/cacerts/ -n kube-system
```

对于 CA 节点命令如下：

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- cp /var/lib/openvswitch/pki/switchca/cacert.pem /etc/ipsec.d/cacerts/
```

### 配置到 ovs 数据库

执行命令：

```bash
kubectl exec -it ovs-ovn-pp566 -n kube-system -- ovs-vsctl set Open_vSwitch . \
        other_config:certificate=/etc/ipsec.d/certs/1a7353d2-8735-4f7a-a19e-30ed7bb351d8-cert.pem \
        other_config:private_key=/etc/ipsec.d/private/1a7353d2-8735-4f7a-a19e-30ed7bb351d8-privkey.pem \
        other_config:ca_cert=/etc/ipsec.d/cacerts/cacert.pem
        
kubectl exec -it ovs-ovn-4v7ql -n kube-system -- ovs-vsctl set Open_vSwitch . \
        other_config:certificate=/etc/ipsec.d/certs/63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-cert.pem \
        other_config:private_key=/etc/ipsec.d/private/63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-privkey.pem \
        other_config:ca_cert=/etc/ipsec.d/cacerts/cacert.pem

```


### 开启 ovn ipsec 开关

```bash
kubectl ko nbctl set nb_global . ipsec=true
```
可以通过如下命令看到节点间的 ipsec 隧道建立起来

```bash
[root@localhost kube-ovn]# kubectl exec -it ovs-ovn-4v7ql -n kube-system -- ovs-appctl -t ovs-monitor-ipsec tunnels/show
Interface name: ovn-1a7353-0 v1 (CONFIGURED)
  Tunnel Type:    geneve
  Local IP:       172.18.0.4
  Remote IP:      172.18.0.2
  Address Family: IPv4
  SKB mark:       None
  Local cert:     /etc/ipsec.d/certs/63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-cert.pem
  Local name:     63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6
  Local key:      /etc/ipsec.d/private/63ed48d9-bd48-41f2-94d5-10fa3aa7a7f6-privkey.pem
  Remote cert:    None
  Remote name:    1a7353d2-8735-4f7a-a19e-30ed7bb351d8
  CA cert:        /etc/ipsec.d/cacerts/cacert.pem
  PSK:            None
  Ofport:         1
  CFM state:      Disabled
Kernel policies installed:
  src 172.18.0.4/32 dst 172.18.0.2/32 proto udp dport 6081
  src 172.18.0.4/32 dst 172.18.0.2/32 proto udp dport 6081
  src 172.18.0.4/32 dst 172.18.0.2/32 proto udp sport 6081
  src 172.18.0.4/32 dst 172.18.0.2/32 proto udp sport 6081
Kernel security associations installed:
  sel src 172.18.0.4/32 dst 172.18.0.2/32 proto udp dport 6081
  sel src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
  sel src 172.18.0.4/32 dst 172.18.0.2/32 proto udp sport 6081
  sel src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
IPsec connections that are active:

```

如果出现 ipsec 失败可以尝试重启ipsec服务
```
service ipsec restart
```




