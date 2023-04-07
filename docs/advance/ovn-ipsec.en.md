# Encrypt communication between ovn internal nodes using ovn ipsec

## start ipsec

Copy the script from the kube-ovn source code, the path is : dist/image/start-ipsec.sh, execute the command as follows, the script will call ovs-pki to generate and distribute the certificate required for encryption:

```bash
sh start-ipsec.sh
```

After the execution is completed, the nodes will negotiate for a period of time to establish an ipsec tunnel. The experience value is between ten seconds and one minute. You can use the following command to view the ipsec status. ipsec tunnel from 172.18.0.2 to 172.18.0.4.

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

After the establishment is complete, you can capture packets and observe that the packets have been encrypted:

```bash
#tcpdump -i eth0 -nel esp
10:01:40.349896 IP kube-ovn-worker > kube-ovn-control-plane.kind: ESP(spi=0xcc91322a,seq=0x13d0), length 156
10:01:40.350015 IP kube-ovn-control-plane.kind > kube-ovn-worker: ESP(spi=0xc8df4221,seq=0x1d37), length 156
```

After executing the script, you can turn off ipsec by executing the command:

```bash
kubectl ko nbctl set nb_global . ipsec=false
```

Or execute the command to open it again:

```bash
kubectl ko nbctl set nb_global . ipsec=true

This feature is supported from v1.10
