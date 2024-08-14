# NetworkPolicy 日志

NetworkPolicy 为 Kubernetes 提供的网络策略接口，Kube-OVN 通过 OVN 的 ACL 进行了实现。
使用了 NetworkPolicy 后如果出现网络不通的情况，难以判断是网络故障问题还是 NetworkPolicy 规则设置问题导致的网络中断。
Kube-OVN 提供了 NetworkPolicy 日志功能，帮助管理员快速定位 NetworkPolicy Drop 规则是否命中，并记录有哪些非法访问。

> NetworkPolicy 日志功能一旦开启，对每个命中 Drop 规则的数据包都需要打印日志，会带来额外性能开销。
> 在恶意攻击下，短时间大量日志可能会耗尽 CPU。我们建议在生产环境默认关闭日志功能，在需要排查问题时，动态开启日志。

## 开启 NetworkPolicy 日志

在需要开启日志记录的 NetworkPolicy 中增加 annotation `ovn.kubernetes.io/enable_log`，如下所示：

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

接下来可以在对应 Pod 所在主机的 `/var/log/ovn/ovn-controller.log` 中观察到被丢弃数据包的日志：

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

## 其他 NetworkPolicy 日志

默认情况下，设置 "ovn.kubernetes.io/enable_log" annotation 之后，只能打印匹配 Drop ACL 规则的日志，如果想要查看匹配其他 ACL 规则的日志，是不支持的。

从 Kube-OVN v1.13.0 版本开始，新增了一个 annotation "ovn.kubernetes.io/log_acl_actions"，用于支持匹配其他 ACL 规则的日志打印。annotation 的取值，需要设置为 "allow"。

在 NetworkPolicy 中增加 annotation `ovn.kubernetes.io/log_acl_actions`，如下所示：

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

访问测试 Pod，查看对应 Pod 所在主机的 /var/log/ovn/ovn-controller.log， 其中可以看到 Allow ACL 规则的日志

```bash
2024-08-14T09:27:49.590Z|00004|acl_log(ovn_pinctrl0)|INFO|name="np/test.default/ingress/IPv4/0", verdict=allow, severity=info, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=96:7b:b0:2f:a0:1a,dl_dst=a6:e5:1b:c2:1b:f8,nw_src=10.16.0.7,nw_dst=10.16.0.12,nw_tos=0,nw_ecn=0,nw_ttl=64,nw_frag=no,icmp_type=8,icmp_code=0
```

## 关闭 NetworkPolicy 日志

将对应 NetworkPolicy 中的 annotation `ovn.kubernetes.io/enable_log` 设置为 `false` 即可关闭 NetworkPolicy 日志：

```bash
kubectl annotate networkpolicy -n kube-system default-deny-ingress ovn.kubernetes.io/enable_log=false --overwrite
```

## AdminNetworkPolicy 和 BaselineAdminNetworkPolicy 日志

从 v1.13.0 版本开始，Kube-OVN 开始支持 AdminNetworkPolicy 和 BaselineAdminNetworkPolicy 的功能。关于 AdminNetworkPolicy 和 BaselineAdminNetworkPolicy 的介绍，可以查看 [集群网络策略](https://network-policy-api.sigs.k8s.io/)。

针对集群网络策略，同样可以通过设置 "ovn.kubernetes.io/log_acl_actions" annotation 打印匹配 action ACL 规则的日志。annotation 的取值，可以设置为 "allow,drop,pass" 其中一个或多个的组合。

需要注意的是，"ovn.kubernetes.io/enable_log" annotation 仅在打印网络策略日志时候使用。在打印集群网络策略日志时，并不需要设置这个 annotation，只需要设置 "ovn.kubernetes.io/log_acl_actions" annotation 即可。
