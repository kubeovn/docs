# Encrypt inter-node communication using IPsec

This function is supported after v1.10.11 and v1.11.4, the kernel version is at least 3.10.0 or above, and UDP ports 500 and 4500 are available.

## Start IPsec

Copy the script from the Kube-OVN source code [ipsec.sh](https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/images/ipsec.sh), execute the command as follows, the script will call ovs-pki to generate and distribute the certificate required for encryption:

```bash
bash ipsec.sh init
```

After the execution is completed, the nodes will negotiate for a period of time to establish an IPsec tunnel. The experience value is between ten seconds and one minute.You can check the IPsec status with the following command:

```bash
# bash ipsec.sh status
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

After the establishment is complete, you can capture packets and observe that the packets have been encrypted:

```bash
# tcpdump -i eth0 -nel esp
10:01:40.349896 IP kube-ovn-worker > kube-ovn-control-plane.kind: ESP(spi=0xcc91322a,seq=0x13d0), length 156
10:01:40.350015 IP kube-ovn-control-plane.kind > kube-ovn-worker: ESP(spi=0xc8df4221,seq=0x1d37), length 156
```

After executing the script, you can turn off IPsec by executing the command:

```bash
# bash ipsec.sh stop
```

Or execute the command to open it again:

```bash
# bash ipsec.sh start
```
