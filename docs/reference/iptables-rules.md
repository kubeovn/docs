# 网关 Netfilter 规则

Kube-OVN 使用网关 Netfilter 后端实现默认 VPC 下容器网络（Overlay）的网关 NAT 功能。
后端可以使用 `iptables` 或 `nftables`，本文同时保留 iptables 后端的规则参考。

## 网关后端选择

`kube-ovn-cni` daemon 支持三种网关 Netfilter 模式：

| 模式 | 行为 |
| :--- | :--- |
| `auto` | 自动检测本地 kube-proxy 模式。`iptables` 和 `ipvs` 使用 iptables 后端，`nftables` 使用 nftables 后端。 |
| `iptables` | 始终使用 Kube-OVN 的 iptables 和 ipset 规则。 |
| `nftables` | 始终使用 Kube-OVN 的 nftables 表和规则。 |

默认模式为 `auto`。冷启动时会轮询 kube-proxy 的 `proxyMode` 接口；如果在检测超时前接口不可用，则读取 `kube-system` 中的 `kube-proxy` ConfigMap。默认接口为 `http://localhost:10249/proxyMode`，默认超时为 30 秒。运行期间连续三次观察到模式变化后才会切换后端，避免一次临时响应触发切换。

运行 `bash install.sh` 前，可以通过环境变量设置模式和检测参数；也可以在 `kube-ovn-cni` DaemonSet 中设置：

```bash
export GATEWAY_NETFILTER_MODE=auto
export KUBE_PROXY_MODE_ENDPOINT=http://localhost:10249/proxyMode
export GATEWAY_NETFILTER_DETECT_TIMEOUT=30s
```

```yaml
args:
- --gateway-netfilter-mode=auto
- --kube-proxy-mode-endpoint=http://localhost:10249/proxyMode
- --gateway-netfilter-detect-timeout=30s
```

使用 Helm 安装时，根据 Chart 版本设置对应的值：

```yaml
# charts/kube-ovn
networking:
  GATEWAY_NETFILTER_MODE: auto
  KUBE_PROXY_MODE_ENDPOINT: http://localhost:10249/proxyMode
  GATEWAY_NETFILTER_DETECT_TIMEOUT: 30s
```

```yaml
# charts/kube-ovn-v2
agent:
  gatewayNetfilterMode: auto
  kubeProxyModeEndpoint: http://localhost:10249/proxyMode
  gatewayNetfilterDetectTimeout: 30s
```

nftables 后端在适用的 IPv4、IPv6 nftables family 中分别管理 Kube-OVN 自有的 `kube-ovn` 表，用于 Service 和 NodePort NAT、子网 NAT、NAT policy、TProxy、filter 和 mangle 规则以及子网流量统计。它不会读取或修改 kube-proxy 私有的 nftables 对象或标记，也不会清理 conntrack 表项。

后端切换时，Kube-OVN 会先准备并同步目标后端，再清理旧后端。切换和卸载时只清理 Kube-OVN 自有的 iptables、ipset 和 nftables 对象。如果清理失败，会保留当前后端并在后续 reconcile 中重试。

## Nftable LoadBalancer Service

控制器参数 `--enable-nftable-lb-svc` 用于启用由 VPC NAT Gateway nftable share-DNAT 实现的 LoadBalancer Service。当前 master 中该参数默认值为 `true`，且需要全局参数 `--enable-lb=true` 才能生效。

对应的 Helm 配置键如下：

```yaml
# charts/kube-ovn
func:
  ENABLE_NFTABLE_LB_SVC: true

# charts/kube-ovn-v2
features:
  enableNftableLoadbalancerService: false
```

v2 chart 仅在 `enableNftableLoadbalancerService` 为 true 时渲染控制器参数。当该值为 false 时会省略参数，而控制器默认值仍为 true；在 chart 提供有效的关闭方式前，如需关闭应显式设置控制器参数。

nftable LoadBalancer Service 进入终止状态时，会立即释放其 `EIP:port:protocol` 标识。后续 Service 可以复用该标识并被编程，无需等待已删除 Service 的 finalizer 完成。

使用的 ipset 如下表所示：

| 名称（IPv4/IPv6） | 类型 | 存储对象 |
| :------------------------------------------------------ | :------- | :----------------------------------------- |
| ovn40services/ovn60services | hash:net | Service 网段 |
| ovn40subnets/ovn60subnets | hash:net | Overlay 子网网段以及 NodeLocal DNS IP 地址 |
| ovn40subnets-nat/ovn60subnets-nat | hash:net | 开启 NatOutgoing 的 Overlay 子网网段 |
| ovn40subnets-distributed-gw/ovn60subnets-distributed-gw | hash:net | 开启分布式网关的 Overlay 子网网段 |
| ovn40other-node/ovn60other-node | hash:net | 其它节点的内部 IP 地址 |
| ovn40local-pod-ip-nat/ovn60local-pod-ip-nat | hash:ip | 已弃用 |
| ovn40subnets-nat-policy | hash:net | 配置了 natOutgoingPolicyRules 的所有子网网段 |
| ovn40natpr-418e79269dc5-dst | hash:net | natOutgoingPolicyRules 中 rule 对应的 dstIPs |
| ovn40natpr-418e79269dc5-src | hash:net | natOutgoingPolicyRules 中 rule 对应的 srcIPs |

使用的 iptables 规则（IPv4）如下表所示：

| 表 | 链 | 规则 | 用途 | 备注 |
| :----- | :-------------- | :---------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- |
| filter | INPUT | -m set --match-set ovn40services src -j ACCEPT | 允许 k8s Service 和 Pod 相关流量通过 | -- |
| filter | INPUT | -m set --match-set ovn40services dst -j ACCEPT | 同上 | -- |
| filter | INPUT | -m set --match-set ovn40subnets src -j ACCEPT | 同上 | -- |
| filter | INPUT | -m set --match-set ovn40subnets dst -j ACCEPT | 同上 | -- |
| filter | FORWARD | -m set --match-set ovn40services src -j ACCEPT | 同上 | -- |
| filter | FORWARD | -m set --match-set ovn40services dst -j ACCEPT | 同上 | -- |
| filter | FORWARD | -m set --match-set ovn40subnets src -j ACCEPT | 同上 | -- |
| filter | FORWARD | -m set --match-set ovn40subnets dst -j ACCEPT | 同上 | -- |
| filter | FORWARD | -s 10.16.0.0/16 -m comment --comment "ovn-subnet-gateway,ovn-default" | 用于计数从 subnet 访问外部网络的报文 | 10.16.0.0/16 为 subnet 的 cidr ，comment 中逗号前面的 ovn-subnet-gateway 用于标识该 iptables 规则用于 subnet 出入网关报文计数，逗号后面 ovn-default 是该 subnet 的名字 |
| filter | FORWARD | -d 10.16.0.0/16 -m comment --comment "ovn-subnet-gateway,ovn-default" | 用于计数从外部网络访问 subnet 的报文 | 同上 |
| filter | OUTPUT | -p udp -m udp --dport 6081 -j MARK --set-xmark 0x0 | 清除流量标记，避免执行 SNAT | [UDP: bad checksum on VXLAN interface](https://github.com/flannel-io/flannel/issues/1279) |
| nat | PREROUTING | -m comment --comment "kube-ovn prerouting rules" -j OVN-PREROUTING | 进入 OVN-PREROUTING 链处理 | -- |
| nat | POSTROUTING | -m comment --comment "kube-ovn postrouting rules" -j OVN-POSTROUTING | 进入 OVN-POSTROUTING 链处理 | -- |
| nat | OVN-PREROUTING | -i ovn0 -m set --match-set ovn40subnets src -m set --match-set ovn40services dst -j MARK --set-xmark 0x4000/0x4000 | 为 Pod 访问 Service 流量添加 masquerade 标记 | 作用于关闭内置 LB 的场景 |
| nat | OVN-PREROUTING | -p tcp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-TCP dst -j MARK --set-xmark 0x80000/0x80000 | 为 ExternalTrafficPolicy 为 Local 的 Service 流量（TCP）添加特定标记 | 仅 kube-proxy 使用 ipvs 模式时存在 |
| nat | OVN-PREROUTING | -p udp -m addrtype --dst-type LOCAL -m set --match-set KUBE-NODE-PORT-LOCAL-UDP dst -j MARK --set-xmark 0x80000/0x80000 | 为 ExternalTrafficPolicy 为 Local 的 Service 流量（UDP）添加特定标记 | 同上 |
| nat | OVN-POSTROUTING | -m set --match-set ovn40services src -m set --match-set ovn40subnets dst -m mark --mark 0x4000/0x4000 -j SNAT --to-source <NODE_IP> | 当节点通过 Service IP 访问 Overlay Pod 时，保持源 IP 为节点 IP。 | 仅 kube-proxy 使用 ipvs 模式时生效 |
| nat | OVN-POSTROUTING | -m mark --mark 0x4000/0x4000 -j MASQUERADE | 为特定标记的流量执行 SNAT | -- |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets src -m set --match-set ovn40subnets dst -j MASQUERADE | 为通过节点的 Pod 之间的 Service 流量执行 SNAT | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -m set --match-set ovn40subnets-distributed-gw dst -j RETURN | 对于 ExternalTrafficPolicy 为 Local 的 Service 流量，若 Endpoint 使用分布式网关，无需执行 SNAT | -- |
| nat | OVN-POSTROUTING | -m mark --mark 0x80000/0x80000 -j MASQUERADE | 对于 ExternalTrafficPolicy 为 Local 的 Service 流量，若 Endpoint 使用集中式网关，执行 SNAT | -- |
| nat | OVN-POSTROUTING | -p tcp -m tcp --tcp-flags SYN NONE -m conntrack --ctstate NEW -j RETURN | Pod IP 对外暴露时，不执行 SNAT | -- |
| nat | OVN-POSTROUTING | -s 10.16.0.0/16 -m set ! --match-set ovn40subnets dst -j SNAT --to-source 192.168.0.101 | Pod 访问集群外网络时，若子网开启 NatOutgoing 且使用指定 IP 的集中式网关，执行 SNAT | 10.16.0.0/16 为子网网段，192.168.0.101 为指定的网关节点 IP |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat src -m set ! --match-set ovn40subnets dst -j MASQUERADE | Pod 访问集群外网络时，若子网开启 NatOutgoing，执行 SNAT | -- |
| nat | OVN-POSTROUTING | -m set --match-set ovn40subnets-nat-policy src -m set ! --match-set ovn40subnets dst -j OVN-NAT-POLICY | Pod 访问集群外网络时，若子网配置了 natOutgoingPolicyRules，符合策略的报文执行 SNAT | 配置了 natOutgoingPolicyRules 子网的出外网报文进入 OVN-NAT-POLICY 链 |
| nat | OVN-POSTROUTING | -m mark --mark 0x90001/0x90001 -j MASQUERADE --random-fully | 同上 | 从 OVN-NAT-POLICY 出来后，如果被打上 tag 0x90001/0x90001 就会做 SNAT |
| nat | OVN-POSTROUTING | -m mark --mark 0x90002/0x90002 -j RETURN | 同上 | 从 OVN-NAT-POLICY 出来后, 如果被打上 tag 0x90002/0x90002 不会做 SNAT |
| nat | OVN-NAT-POLICY | -s 10.0.11.0/24 -m comment --comment natPolicySubnet-net1 -j OVN-NAT-PSUBNET-aa98851157c5 | 同上 | 10.0.11.0/24 表示子网 net1 的 CIDR，  OVN-NAT-PSUBNET-aa98851157c5 这条链下的规则就对应这个子网的 natOutgoingPolicyRules 配置 |
| nat | OVN-NAT-PSUBNET-xxxxxxxxxxxx | -m set --match-set ovn40natpr-418e79269dc5-src src -m set --match-set ovn40natpr-418e79269dc5-dst dst -j MARK --set-xmark 0x90002/0x90002 | 同上 | 418e79269dc5 表示 natOutgoingPolicyRules 中的一条规则的 ID，可以通过 status.natOutgoingPolicyRules[index].RuleID 查看到， 表示 srcIPs 满足 ovn40natpr-418e79269dc5-src， dstIPS 满足 ovn40natpr-418e79269dc5-dst 会打上 tag 0x90002 |
| mangle | OVN-OUTPUT | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j MARK --set-xmark 0x90003/0x90003 | 将 kubelet 的探测流量加上特定标记从而引入到 tproxy | |
| mangle | OVN-PREROUTING | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j TPROXY --on-port 8102 --on-ip 172.18.0.3 --tproxy-mark 0x90004/0x90004 | 将 kubelet 的探测流量加上特定标记从而引入到 tproxy | |
