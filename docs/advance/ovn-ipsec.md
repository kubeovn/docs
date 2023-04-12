# 使用 IPsec 加密节点间通信

该功能从 v1.10.11 和 v1.11.4 后开始支持，kernel 版本至少是 3.10.0 以上

## 启动 ipsec

从 kube-ovn 源码拷贝脚本 [ipsec.sh](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/ipsec.sh)，执行命令如下，该脚本会调用 ovs-pki 生成和分配加密需要的证书：

```bash
bash ipsec.sh init
```

执行完毕后，节点之间会协商一段时间建立 ipsec 隧道，经验值是十几秒到一分钟之间，可以通过如下命令来查看 ipsec 状态：

```bash
# sh ipsec.sh status
 Pod {ovs-ovn-d7hdt} ipsec status...
Interface name: ovn-a4718e-0 v1 (CONFIGURED)
  Tunnel Type:    geneve
  Local IP:       172.18.0.2
  Remote IP:      172.18.0.4
  Address Family: IPv4
  SKB mark:       None
  Local cert:     /etc/ipsec.d/certs/8aebd9df-46ef-47b9-85e3-73e9a765296d-cert.pem
  Local name:     8aebd9df-46ef-47b9-85e3-73e9a765296d
  Local key:      /etc/ipsec.d/private/8aebd9df-46ef-47b9-85e3-73e9a765296d-privkey.pem
  Remote cert:    None
  Remote name:    a4718e55-5b85-4f46-90e6-63527d080590
  CA cert:        /etc/ipsec.d/cacerts/cacert.pem
  PSK:            None
  Custom Options: {}
  Ofport:         2
  CFM state:      Disabled
Kernel policies installed:
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
Kernel security associations installed:
  sel src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
  sel src 172.18.0.4/32 dst 172.18.0.2/32 proto udp dport 6081
  sel src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
  sel src 172.18.0.4/32 dst 172.18.0.2/32 proto udp sport 6081
IPsec connections that are active:

 Pod {ovs-ovn-fvbbj} ipsec status...
Interface name: ovn-8aebd9-0 v1 (CONFIGURED)
  Tunnel Type:    geneve
  Local IP:       172.18.0.4
  Remote IP:      172.18.0.2
  Address Family: IPv4
  SKB mark:       None
  Local cert:     /etc/ipsec.d/certs/a4718e55-5b85-4f46-90e6-63527d080590-cert.pem
  Local name:     a4718e55-5b85-4f46-90e6-63527d080590
  Local key:      /etc/ipsec.d/private/a4718e55-5b85-4f46-90e6-63527d080590-privkey.pem
  Remote cert:    None
  Remote name:    8aebd9df-46ef-47b9-85e3-73e9a765296d
  CA cert:        /etc/ipsec.d/cacerts/cacert.pem
  PSK:            None
  Custom Options: {}
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

建立完成后可以抓包观察报文已经被加密：

```bash
# tcpdump -i eth0 -nel esp
10:01:40.349896 IP kube-ovn-worker > kube-ovn-control-plane.kind: ESP(spi=0xcc91322a,seq=0x13d0), length 156
10:01:40.350015 IP kube-ovn-control-plane.kind > kube-ovn-worker: ESP(spi=0xc8df4221,seq=0x1d37), length 156
```

当执行完脚本后，可以通过执行命令关闭 ipsec：

```bash
# bash ipsec.sh stop
```

或者执行命令再次打开：

```bash
# bash ipsec.sh start
```
