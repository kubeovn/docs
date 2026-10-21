# Netfilter（Iptables / Nftables）规则

Kube-OVN 借助宿主机 Linux Netfilter 机制辅助实现默认 VPC 下容器网络（Overlay）的网关出网 NAT、Kube-Proxy 兼容以及 TProxy 透明代理等功能。

Kube-OVN 支持 **Iptables**（传统兼容）与 **Nftables**（现代架构）两种底层后端实现，可通过启动参数 `--gateway-netfilter-mode=auto|iptables|nftables` 进行配置（默认为 `auto` 自动探测并与本地 Kube-Proxy 运行模式保持对齐）。

## Iptables 规则

在 Iptables 后端模式下，Kube-OVN 使用 `ipset` 与 `iptables` 规则协同工作。

### IPSet 集合定义

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

### Iptables 规则定义

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
| filter | OUTPUT | -p udp -m udp --dport 6081 -j MARK --set-xmark 0x0 | 清除流量标记，避免执行 SNAT | [UDP: bad checksum on VXLAN interface](https://github.com/flannel-io/flannel/issues/1279){: target="_blank" } |
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
| nat | OVN-POSTROUTING | -m mark --mark 0x90002/0x90002 -j RETURN | 同上 | 从 OVN-NAT-POLICY 出来后，如果被打上 tag 0x90002/0x90002 不会做 SNAT |
| nat | OVN-NAT-POLICY | -s 10.0.11.0/24 -m comment --comment natPolicySubnet-net1 -j OVN-NAT-PSUBNET-aa98851157c5 | 同上 | 10.0.11.0/24 表示子网 net1 的 CIDR，OVN-NAT-PSUBNET-aa98851157c5 这条链下的规则就对应这个子网的 natOutgoingPolicyRules 配置 |
| nat | OVN-NAT-PSUBNET-xxxxxxxxxxxx | -m set --match-set ovn40natpr-418e79269dc5-src src -m set --match-set ovn40natpr-418e79269dc5-dst dst -j MARK --set-xmark 0x90002/0x90002 | 同上 | 418e79269dc5 表示 natOutgoingPolicyRules 中的一条规则的 ID，可以通过 status.natOutgoingPolicyRules[index].RuleID 查看到，表示 srcIPs 满足 ovn40natpr-418e79269dc5-src，dstIPS 满足 ovn40natpr-418e79269dc5-dst 会打上 tag 0x90002 |
| mangle | OVN-OUTPUT | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j MARK --set-xmark 0x90003/0x90003 | 将 kubelet 的探测流量加上特定标记从而引入到 tproxy | -- |
| mangle | OVN-PREROUTING | -d 10.241.39.2/32 -p tcp -m tcp --dport 80 -j TPROXY --on-port 8102 --on-ip 172.18.0.3 --tproxy-mark 0x90004/0x90004 | 将 kubelet 的探测流量加上特定标记从而引入到 tproxy | -- |

## Nftables 规则

在 Nftables 后端模式下，Kube-OVN 会在内核中创建专属的表空间（IPv4 对应 `table ip kube-ovn`，IPv6 对应 `table ip6 kube-ovn`），所有集合、链与规则均在专属表内原子管理，不污染宿主机系统主表。

### 原生 Set 集合定义

Nftables 模式下，原有的 ipset 均映射为内核原生的命名集合（Set）：

| 集合名称（IPv4 / IPv6） | 元素类型 | 作用与存储内容 |
| :---------------------- | :------- | :------------- |
| subnets | `ipv4_addr` / `ipv6_addr` (interval) | Overlay 子网网段以及 NodeLocal DNS IP 地址 |
| services | `ipv4_addr` / `ipv6_addr` (interval) | Service 网段 |
| subnets-nat | `ipv4_addr` / `ipv6_addr` (interval) | 开启 NatOutgoing 的 Overlay 子网网段 |
| subnets-distributed-gw | `ipv4_addr` / `ipv6_addr` (interval) | 开启分布式网关的 Overlay 子网网段 |
| other-node | `ipv4_addr` / `ipv6_addr` | 其它节点的内部 IP 地址 |
| subnets-nat-policy | `ipv4_addr` / `ipv6_addr` (interval) | 配置了 natOutgoingPolicyRules 的所有子网网段 |
| natpr-\<ruleID\>-src | `ipv4_addr` / `ipv6_addr` (interval) | natOutgoingPolicyRules 中规则对应的源 IP 范围 |
| natpr-\<ruleID\>-dst | `ipv4_addr` / `ipv6_addr` (interval) | natOutgoingPolicyRules 中规则对应的目的 IP 范围 |

### 原生计数器（Counters）

在 Nftables 模式下，废弃了旧版依赖 Iptables Comment 字符串解析的统计方式，改为通过内核原生的命名计数器进行无锁高性能统计：

| 命名格式 | 类型 | 用途 |
| :------- | :--- | :--- |
| cnt-subnet-\<subnetName\>-in | counter | 统计从外部网络访问该子网的入站报文与字节数 |
| cnt-subnet-\<subnetName\>-out | counter | 统计从该子网访问外部网络的出站报文与字节数 |

### Nftables 核心链与规则定义（IPv4）

| 链名称 | 挂载 Hook 与优先级 | 核心规则与匹配表达式 | 用途说明 |
| :----- | :----------------- | :------------------- | :------- |
| input | `hook input priority filter` | `ip saddr @services accept`<br>`ip daddr @services accept`<br>`ip saddr @subnets accept`<br>`ip daddr @subnets accept` | 允许 Kubernetes Service 与 Pod 相关流量通过本地 INPUT |
| forward | `hook forward priority filter` | `ip saddr @services accept`<br>`ip daddr @services accept`<br>`ip saddr @subnets accept`<br>`ip daddr @subnets accept`<br>`ip saddr <CIDR> counter name <counter-out>`<br>`ip daddr <CIDR> counter name <counter-in>` | 放行跨网段流量，并调用命名 counter 进行子网出入站流量统计 |
| output | `hook output priority filter` | `udp dport 6081 meta mark set 0x0` | 清除 Geneve 隧道数据包上的流量标记，避免执行意外 SNAT |
| prerouting | `hook prerouting priority nat` | `iifname "ovn0" ip saddr @subnets ip daddr @services meta mark set 0x4000/0x4000` | 为 Pod 访问 Service 的流量打上伪装标记（关闭内置 LB 场景） |
| postrouting | `hook postrouting priority nat` | `ip saddr @services ip daddr @subnets meta mark 0x4000/0x4000 snat to <NODE_IP>`<br>`meta mark 0x4000/0x4000 masquerade`<br>`ip saddr @subnets ip daddr @subnets masquerade`<br>`ip saddr <CIDR> ip daddr != @subnets snat to <Gateway_IP>`<br>`ip saddr @subnets-nat ip daddr != @subnets masquerade`<br>`ip saddr @subnets-nat-policy ip daddr != @subnets jump nat-policy` | 执行容器网络各场景下的出网伪装、集中式固定 IP 出网 SNAT 以及策略路由出网跳转 |
| nat-policy | 自定义跳转链 | `ip saddr @natpr-<ruleID>-src ip daddr @natpr-<ruleID>-dst meta mark set 0x90001`<br>`ip saddr @natpr-<ruleID>-src ip daddr @natpr-<ruleID>-dst meta mark set 0x90002` | 针对配置了 natOutgoingPolicyRules 的子网出网报文执行精确策略匹配与打标（0x90001 执行 SNAT，0x90002 豁免 SNAT） |
