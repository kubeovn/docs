# 使用 ovn ipsec 加密 ovn 内部节点之间的通信

## 启动 ipsec

从 kube-ovn 源码拷贝脚本，路径是： dist/image/start-ipsec.sh，执行命令如下，该脚本会调用 ovs-pki 生成和分配加密需要的证书：

```bash
sh start-ipsec.sh
```

执行完毕后，节点之间会协商一段时间建立 ipsec 隧道，经验值是十几秒到一分钟之间，可以通过如下命令来查看 ipsec 状态，如下表示在节点 IP 为 172.18.0.2 的 节点上建立了从 172.18.0.2 到 172.18.0.4 的 ipsec 隧道。

```bash
# kubectl exec -it ovs-ovn-9x8jq -n kube-system -- ovs-appctl -t ovs-monitor-ipsec tunnels/show
Interface name: ovn-9aa51f-0 v1 (CONFIGURED)
  Tunnel Type:    geneve
  Local IP:       172.18.0.2
  Remote IP:      172.18.0.4
  Address Family: IPv4
  SKB mark:       None
  Local cert:     /etc/ipsec.d/certs/6b8c6eec-eddc-4c02-a12d-c958690f6cd3-cert.pem
  Local name:     6b8c6eec-eddc-4c02-a12d-c958690f6cd3
  Local key:      /etc/ipsec.d/private/6b8c6eec-eddc-4c02-a12d-c958690f6cd3-privkey.pem
  Remote cert:    None
  Remote name:    9aa51f22-8ae4-49a1-8937-b0741f5c6bbc
  CA cert:        /etc/ipsec.d/cacerts/cacert.pem
  PSK:            None
  Ofport:         1
  CFM state:      Disabled
Kernel policies installed:
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
  src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
Kernel security associations installed:
  sel src 172.18.0.2/32 dst 172.18.0.4/32 proto udp dport 6081
  sel src 172.18.0.4/32 dst 172.18.0.2/32 proto udp sport 6081
  sel src 172.18.0.2/32 dst 172.18.0.4/32 proto udp sport 6081
  sel src 172.18.0.4/32 dst 172.18.0.2/32 proto udp dport 6081
```

建立完成后可以抓包观察报文已经被加密：

```bash
# tcpdump -i eth0 -nel esp
10:01:40.349896 IP kube-ovn-worker > kube-ovn-control-plane.kind: ESP(spi=0xcc91322a,seq=0x13d0), length 156
10:01:40.350015 IP kube-ovn-control-plane.kind > kube-ovn-worker: ESP(spi=0xc8df4221,seq=0x1d37), length 156
```

当执行完脚本后，可以通过执行命令关闭 ipsec：

```bash
# kubectl ko nbctl set nb_global . ipsec=false
```

或者执行命令再次打开：

```bash
# kubectl ko nbctl set nb_global . ipsec=true
```

该功能从 v1.10 开始支持。
