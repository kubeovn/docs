# NodeLocal DNSCache and kube-ovn adaptation

NodeLocal DNSCache improves cluster DNS performance by running DNS cache as a DaemonSet on cluster nodes. This function can also be adapted to kube-ovn.

## Nodelocal DNSCache deployment

### Deploy k8s nodelocaldnscache

This step refers to k8s official website configuration [nodelocaldnscache](https://kubernetes.io/zh-cn/docs/tasks/administer-cluster/nodelocaldns/).

Deploy with the following script:

```bash
#!bin/bash

localdns=169.254.20.10
domain=cluster.local
kubedns=10.96.0.10

wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml
sed -i "s/__PILLAR__LOCAL__DNS__/$localdns/g; s/__PILLAR__DNS__DOMAIN__/$domain/g; s/,__PILLAR__DNS__SERVER__//g; s/__PILLAR__CLUSTER__DNS__/$kubedns/g" nodelocaldns.yaml

kubectl apply -f nodelocaldns.yaml
```

Modify the kubelet configuration file on each node, modify the clusterDNS field in /var/lib/kubelet/config.yaml to the local dns ip 169.254.20.10, and then restart the kubelet service.

### kube-ovn corresponding DNS configuration

After deploying the nodelocaldnscache component of k8s, kube-ovn needs to make the following modifications:

#### underlay subnet enable u2o switch

If the underlay subnet needs to use the local DNS function, you need to enable the u2o function, that is, configure spec.u2oInterconnection = true in kubectl edit subnet {your subnet}. If it is an overlay subnet, this step is not required.

#### Specify the corresponding local dns ip for kube-ovn-controller

```bash
kubectl patch deployment kube-ovn-controller -n kube-system --type=json -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--node-local-dns-ip=169.254.20.10"}]'
```

#### Rebuild the created pods

The reason for this step is to let the pod regenerate /etc/resolv.conf so that the nameserver points to the local dns ip. If the nameserver of the pod is not rebuilt, it will still use the dns cluster ip of the cluster. At the same time, if the u2o switch is turned on, the pod needs to be rebuilt to regenerate the pod gateway.

## Validator local DNS cache function

After the above configuration is completed, you can find the pod verification as follows. You can see that the pod's dns server points to the local 169.254.20.10 and successfully resolves the domain name:

```bash
# kubectl exec -it pod1 -- nslookup github.com
Server:         169.254.20.10
Address:        169.254.20.10:53


Name:   github.com
Address: 20.205.243.166
```

You can also capture packets at the node and verify as follows. You can see that the dns query message reaches the local dns service through the ovn0 network card, and the dns response message returns in the same way:

```bash
# tcpdump -i any port 53

06:20:00.441889 659246098c56_h P   ifindex 17 00:00:00:73:f1:06 ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1291+ A? baidu.com. (27)
06:20:00.441889 ovn0  In  ifindex 7 00:00:00:50:32:cd ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1291+ A? baidu.com. (27)
06:20:00.441950 659246098c56_h P   ifindex 17 00:00:00:73:f1:06 ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1611+ AAAA? baidu.com. (27)
06:20:00.441950 ovn0  In  ifindex 7 00:00:00:50:32:cd ethertype IPv4 (0x0800), length 75: 10.16.0.2.40230 > 169.254.20.10.53: 1611+ AAAA? baidu.com. (27)
06:20:00.442203 ovn0  Out ifindex 7 00:00:00:52:99:d8 ethertype IPv4 (0x0800), length 145: 169.254.20.10.53 > 10.16.0.2.40230: 1611* 0/1/0 (97)
06:20:00.442219 659246098c56_h Out ifindex 17 00:00:00:ea:b3:5e ethertype IPv4 (0x0800), length 145: 169.254.20.10.53 > 10.16.0.2.40230: 1611* 0/1/0 (97)
06:20:00.442273 ovn0  Out ifindex 7 00:00:00:52:99:d8 ethertype IPv4 (0x0800), length 125: 169.254.20.10.53 > 10.16.0.2.40230: 1291* 2/0/0 A 39.156.66.10, A 110.242.68.66 (77)
06:20:00.442278 659246098c56_h Out ifindex 17 00:00:00:ea:b3:5e ethertype IPv4 (0x0800), length 125: 169.254.20.10.53 > 10.16.0.2.40230: 1291* 2/0/0 A 39.156.66.10, A 110.242.68.66 (77)
```



