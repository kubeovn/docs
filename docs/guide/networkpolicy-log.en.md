# NetworkPolicy Logging

NetworkPolicy is a interface provided by Kubernetes and implemented by Kube-OVN through OVN's ACLs.
With NetworkPolicy, if the networks are down, it is difficult to determine whether it is caused by a network failure or a NetworkPolicy rule problem.
Kube-OVN provides NetworkPolicy logging to help administrators quickly locate whether a NetworkPolicy drop rule has been hit,
and to record the illegal accesses.

> Once NetworkPolicy logging is turned on, logs need to be printed for every packet that hits a Drop rule, which introduces additional performance overhead.
> Under a malicious attack, a large number of logs in a short period of time may exhaust the CPU.
> We recommend turning off logging by default in production environments and dynamically turning it on when you need to troubleshoot problems.

## Enable NetworkPolicy Logging

Add the annotation `ovn.kubernetes.io/enable_log` to the NetworkPolicy where logging needs to be enabled, as follows:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: kube-system
  annotations:
    ovn.kubernetes.io/enable_log: "true"
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

Next, you can observe the log of dropped packets in `/var/log/ovn/ovn-controller.log` on the host of the corresponding Pod:

```bash
# tail -f /var/log/ovn/ovn-controller.log
2022-07-20T05:55:03.229Z|00394|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.10,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=54343,tp_dst=53
2022-07-20T05:55:06.229Z|00395|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.9,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=44187,tp_dst=53
2022-07-20T05:55:08.230Z|00396|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.10,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=54274,tp_dst=53
2022-07-20T05:55:11.231Z|00397|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.9,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=32778,tp_dst=53
2022-07-20T05:55:11.231Z|00398|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.9,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=34188,tp_dst=53
2022-07-20T05:55:13.231Z|00399|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.10,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=43290,tp_dst=53
2022-07-20T05:55:22.096Z|00400|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=00:00:00:6c:42:91,dl_dst=00:00:00:a5:d7:63,nw_src=10.16.0.9,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0
2022-07-20T05:55:22.097Z|00401|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=00:00:00:6c:42:91,dl_dst=00:00:00:a5:d7:63,nw_src=10.16.0.9,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0
2022-07-20T05:55:22.098Z|00402|acl_log(ovn_pinctrl0)|INFO|name="<unnamed>", verdict=drop, severity=warning, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=00:00:00:6c:42:91,dl_dst=00:00:00:a5:d7:63,nw_src=10.16.0.9,nw_dst=10.16.0.10,nw_tos=0,nw_ecn=0,nw_ttl=64,icmp_type=8,icmp_code=0
```

## Other NetworkPolicy Logging

By default, after setting the "ovn.kubernetes.io/enable_log" annotation, only logs matching the drop ACL rule can be printed. If you want to view logs matching other ACL rules, it is not supported.

Starting from Kube-OVN v1.13.0, a new annotation "ovn.kubernetes.io/log_acl_actions" is added to support logging that matches other ACL rules. The value of the annotation needs to be set to "allow".

Add annotation `ovn.kubernetes.io/log_acl_actions` to NetworkPolicy, as shown below:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: kube-system
  annotations:
    ovn.kubernetes.io/enable_log: "true"
    ovn.kubernetes.io/log_acl_actions: "allow"
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

Access the test pod and check /var/log/ovn/ovn-controller.log of the host where the corresponding Pod is located. You can see the Allow ACL Rule log

```bash
2024-08-14T09:27:49.590Z|00004|acl_log(ovn_pinctrl0)|INFO|name="np/test.default/ingress/IPv4/0", verdict=allow, severity=info, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=96:7b:b 0:2f:a0:1a,dl_dst=a6:e5:1b:c2:1b:f8,nw_src=10.16.0.7,nw_dst=10.16.0.12,nw_tos=0,nw_ecn=0,nw_ttl=64,nw_frag=no,icmp_type=8,icmp_code=0
```

## Disable NetworkPolicy Logging

Set annotation `ovn.kubernetes.io/enable_log` in the corresponding NetworkPolicy to `false` to disable NetworkPolicy logging:

```bash
kubectl annotate networkpolicy -n kube-system default-deny-ingress ovn.kubernetes.io/enable_log=false --overwrite
```

## AdminNetworkPolicy and BaselineAdminNetworkPolicy Logging

Starting from v1.13.0, Kube-OVN supports the AdminNetworkPolicy and BaselineAdminNetworkPolicy functions. For an introduction to AdminNetworkPolicy and BaselineAdminNetworkPolicy, see [AdminNetworkPolicy](https://network-policy-api.sigs.k8s.io/).

For cluster network policies, you can also print logs that match ACL action rules by setting the "ovn.kubernetes.io/log_acl_actions" annotation. The annotation's value can be a combination of one or more of "allow,drop,pass".

Note that the "ovn.kubernetes.io/enable_log" annotation is only used when printing network policy logs. When printing cluster network policy logs, you do not need to set this annotation. You only need to set the "ovn.kubernetes.io/log_acl_actions" annotation.
