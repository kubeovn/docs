# Kube-OVN 监控指标

本文档列举 Kube-OVN 所提供的监控指标。

## ovn-monitor

OVN 自身状态监控指标：

|类型|指标项|描述|
|---|---|---|
|Gauge|kube_ovn_ovn_status|OVN 角色状态， (2) 为 follower； (1) 为 leader, (0) 为异常状态。|
|Gauge|kube_ovn_failed_req_count|OVN 失败请求数量。|
|Gauge|kube_ovn_log_file_size_bytes|OVN 组件日志文件大小。|
|Gauge|kube_ovn_db_file_size_bytes|OVN 组件数据库文件大小。|
|Gauge|kube_ovn_chassis_info|OVN chassis 状态 (1) 运行中，(0) 停止。|
|Gauge|kube_ovn_db_status|OVN 数据库状态, (1) 为正常； (0) 为异常。|
|Gauge|kube_ovn_logical_switch_info|OVN logical switch 信息，值为 (1)，标签中包含 logical switch 名字。|
|Gauge|kube_ovn_logical_switch_external_id|OVN logical switch external_id 信息，值为 (1)，标签中包含 external-id 内容。|
|Gauge|kube_ovn_logical_switch_port_binding|OVN logical switch 和 logical switch port 关联信息，值为 (1)，通过标签进行关联。|
|Gauge|kube_ovn_logical_switch_tunnel_key|和 OVN logical switch 关联的 tunnel key 信息。|
|Gauge|kube_ovn_logical_switch_ports_num|OVN logical switch 上 logical port 的数量。|
|Gauge|kube_ovn_logical_switch_port_info|OVN logical switch port 信息，值为 (1)，标签中包含具体信息。|
|Gauge|kube_ovn_logical_switch_port_tunnel_key|和 OVN logical switch port 关联的 tunnel key 信息。|
|Gauge|kube_ovn_cluster_enabled|(1) OVN 数据库为集群模式； (0) OVN 数据库为非集群模式。|
|Gauge|kube_ovn_cluster_role|每个数据库实例的角色，值为 (1)，标签中包含对应角色信息。|
|Gauge|kube_ovn_cluster_status|每个数据库实例的状态，值为 (1)，标签中包含对应状态信息。|
|Gauge|kube_ovn_cluster_term|RAFT term 信息。|
|Gauge|kube_ovn_cluster_leader_self|当前数据库实例是否为 leader (1) 是， (0) 不是。|
|Gauge|kube_ovn_cluster_vote_self|当前数据库实例是否选举自己为 leader (1) 是， (0) 不是。|
|Gauge|kube_ovn_cluster_election_timer|当前 election timer 值。|
|Gauge|kube_ovn_cluster_log_not_committed|未 commit 的 RAFT 日志数量。|
|Gauge|kube_ovn_cluster_log_not_applied|未 apply 的 RAFT 日志数量。|
|Gauge|kube_ovn_cluster_log_index_start|当前 RAFT 日志条目的起始值。|
|Gauge|kube_ovn_cluster_log_index_next|RAFT 日志条目的下一个值。|
|Gauge|kube_ovn_cluster_inbound_connections_total|当前实例的入向连接数量。|
|Gauge|kube_ovn_cluster_outbound_connections_total|当前实例的出向连接数量。|
|Gauge|kube_ovn_cluster_inbound_connections_error_total|当前实例的入向错误连接数量。|
|Gauge|kube_ovn_cluster_outbound_connections_error_total|当前实例的出向错误连接数量。|
|Gauge|kube_ovn_ovn_status_content|OVN 异常状态时的具体原因内容，值为 (1)，标签中包含 role 和 reason。|
|Gauge|kube_ovn_cluster_peer_inbound_connections_info|Raft 集群中对端节点的入向连接状态信息，值为 (1)，标签中包含 role、server_id、address 和 status。|
|Gauge|kube_ovn_cluster_peer_outbound_connections_info|Raft 集群中对端节点的出向连接状态信息，值为 (1)，标签中包含 role、server_id、address 和 status。|
|Gauge|kube_ovn_cluster_peer_count|Raft 集群中已识别的 Peer 节点总数量。|
|Gauge|kube_ovn_cluster_peer_next_index|Raft 集群中各 Peer 节点的 next_index。|
|Gauge|kube_ovn_cluster_peer_match_index|Raft 集群中各 Peer 节点的 match_index。|
|Gauge|kube_ovn_cluster_next_index|当前数据库节点维护的全局 next_index。|
|Gauge|kube_ovn_cluster_match_index|当前数据库节点维护的全局 match_index。|

## ovs-monitor

`ovsdb` 和 `vswitchd` 自身状态监控指标：

|类型|指标项|描述|
|---|---|---|
|Gauge|ovs_status|OVS 健康状态， (1) 为正常，(0) 为异常。|
|Gauge|ovs_info|OVS 基础信息，值为 (1)，标签中包含对应信息。|
|Gauge|failed_req_count|OVS 失败请求数量。|
|Gauge|log_file_size_bytes|OVS 组件日志文件大小（字节）。|
|Gauge|db_file_size_bytes|OVS 组件数据库文件大小（字节）。|
|Gauge|datapath|Datapath 基础信息，值为 (1)，标签中包含对应信息。|
|Gauge|dp_total|当前 OVS 中 datapath 数量。|
|Gauge|dp_if|Datapath 接口基础信息，值为 (1)，标签中包含对应信息。|
|Gauge|dp_if_total|当前 datapath 中 port 数量。|
|Gauge|dp_flows_total|Datapath 中 flow 数量。|
|Gauge|dp_flows_lookup_hit|Datapath 中命中当前 flow 数据包数量。|
|Gauge|dp_flows_lookup_missed|Datapath 中未命中当前 flow 数据包数量。|
|Gauge|dp_flows_lookup_lost|Datapath 中需要发送给 userspace 处理的数据包数量。|
|Gauge|dp_masks_hit|Datapath 中命中当前 mask 数据包数量。|
|Gauge|dp_masks_total|Datapath 中 mask 的数量。|
|Gauge|dp_masks_hit_ratio|Datapath 中 数据包命中 mask 的比率。|
|Gauge|interface|OVS 接口基础信息，值为 (1)，标签中包含对应信息。|
|Gauge|interface_admin_state|接口管理状态信息 (0) 为 down, (1) 为 up, (2) 为其他状态。|
|Gauge|interface_link_state|接口链路状态信息 (0) 为 down, (1) 为 up, (2) 为其他状态。|
|Gauge|interface_mac_in_use|OVS Interface 使用的 MAC 地址|
|Gauge|interface_mtu|OVS Interface 使用的 MTU。|
|Gauge|interface_of_port|OVS Interface 关联的 OpenFlow Port ID。|
|Gauge|interface_if_index|OVS Interface 关联的 Index。|
|Gauge|interface_tx_packets|OVS Interface 发送包数量。|
|Gauge|interface_tx_bytes|OVS Interface 发送包大小。|
|Gauge|interface_rx_packets|OVS Interface 接收包数量。|
|Gauge|interface_rx_bytes|OVS Interface 接收包大小。|
|Gauge|interface_rx_crc_err|OVS Interface 接收包校验和错误数量。|
|Gauge|interface_rx_dropped|OVS Interface 接收包丢弃数量。|
|Gauge|interface_rx_errors|OVS Interface 接收包错误数量。|
|Gauge|interface_rx_frame_err|OVS Interface 接收帧错误数量。|
|Gauge|interface_rx_missed_err|OVS Interface 接收包 miss 数量。|
|Gauge|interface_rx_over_err|OVS Interface 接收包 overrun 数量。|
|Gauge|interface_tx_dropped|OVS Interface 发送包丢弃数量。|
|Gauge|interface_tx_errors|OVS Interface 发送包错误数量。|
|Gauge|interface_collisions|OVS interface 冲突数量。|
|Gauge|interface_rx_multicast_packets|OVS Interface 接收的多播数据包数量。|

## kube-ovn-pinger

网络质量相关监控指标：

|类型|指标项|描述|
|---|---|---|
|Gauge|pinger_ovs_up|节点 OVS 运行。|
|Gauge|pinger_ovs_down|节点 OVS 停止。|
|Gauge|pinger_ovn_controller_up|节点 ovn-controller 运行。|
|Gauge|pinger_ovn_controller_down|节点 ovn-controller 停止。|
|Gauge|pinger_inconsistent_port_binding|OVN-SB 里 portbinding 数量和主机 OVS interface 不一致的数量。|
|Gauge|pinger_apiserver_healthy|kube-ovn-pinger 可以联通 apiserver。|
|Gauge|pinger_apiserver_unhealthy|kube-ovn-pinger 无法联通 apiserver。|
|Histogram|pinger_apiserver_latency_ms|kube-ovn-pinger 访问 apiserver 延迟。|
|Gauge|pinger_internal_dns_healthy|kube-ovn-pinger 可以解析内部域名。|
|Gauge|pinger_internal_dns_unhealthy|kube-ovn-pinger 无法解析内部域名。|
|Histogram|pinger_internal_dns_latency_ms|kube-ovn-pinger 解析内部域名延迟。|
|Gauge|pinger_external_dns_healthy|kube-ovn-pinger 可以解析外部域名。|
|Gauge|pinger_external_dns_unhealthy|kube-ovn-pinger 无法解析外部域名。|
|Histogram|pinger_external_dns_latency_ms|kube-ovn-pinger 解析外部域名延迟。|
|Histogram|pinger_pod_ping_latency_ms|kube-ovn-pinger ping Pod 延迟。|
|Counter|pinger_pod_ping_lost_total|kube-ovn-pinger ping Pod 丢包数量。|
|Counter|pinger_pod_ping_count_total|kube-ovn-pinger ping Pod 数量。|
|Histogram|pinger_node_ping_latency_ms|kube-ovn-pinger ping Node 延迟。|
|Counter|pinger_node_ping_lost_total|kube-ovn-pinger ping Node 丢包。|
|Counter|pinger_node_ping_count_total|kube-ovn-pinger ping Node 数量。|
|Histogram|pinger_external_ping_latency_ms|kube-ovn-pinger ping 外部地址 延迟。|
|Counter|pinger_external_ping_lost_total|kube-ovn-pinger ping 外部丢包数量。|

## kube-ovn-controller

`kube-ovn-controller` 相关监控指标：

|类型|指标项|描述|
|---|---|---|
|Histogram|rest_client_request_latency_seconds|请求 apiserver 延迟。|
|Counter|rest_client_requests_total|请求 apiserver 数量。|
|Counter|lists_total|API list 请求数量。|
|Summary|list_duration_seconds|API list 请求延迟。|
|Summary|items_per_list|API list 返回结果数量。|
|Counter|watches_total|API watch 请求数量。|
|Counter|short_watches_total|短时间 API watch 请求数量。|
|Summary|watch_duration_seconds|API watch 持续时间。|
|Summary|items_per_watch|API watch 返回结果数量。|
|Gauge|last_resource_version|最新的 resource version。|
|Histogram|ovs_client_request_latency_milliseconds|请求 OVN 组件延迟。|
|Gauge|subnet_available_ip_count|子网可用 IP 数量。|
|Gauge|subnet_used_ip_count|子网已用 IP 数量。|
|Gauge|centralized_subnet_info|集中式网关子网的路由与网关节点信息，值为 (1)，标签中包含 subnet_name、enable_ecmp、gateway_node、active_gateway、match、nexthops。|
|Gauge|subnet_ipam_info|子网 IPAM 地址管理状态统计，值为 (1)，标签中包含 subnet_name、cidr、free、reserved、available、using。|
|Gauge|subnet_ip_assign_info|子网中各 IP 地址分配绑定到 Pod 的具体信息，值为 (1)，标签中包含 subnet_name、ip、pod_name。|

## kube-ovn-cni

`kube-ovn-cni` 相关监控指标：

|类型|指标项|描述|
|---|---|---|
|Histogram|cni_op_latency_seconds|CNI 操作延迟。|
|Counter|cni_wait_address_seconds_total|CNI 等待地址就绪时间。|
|Counter|cni_wait_connectivity_seconds_total|CNI 等待连接就绪时间。|
|Counter|cni_wait_route_seconds_total|CNI 等待路由就绪时间。|
|Histogram|rest_client_request_latency_seconds|请求 apiserver 延迟。|
|Counter|rest_client_requests_total|请求 apiserver 数量。|
|Counter|lists_total|API list 请求数量。|
|Summary|list_duration_seconds|API list 请求延迟。|
|Summary|items_per_list|API list 返回结果数量。|
|Counter|watches_total|API watch 请求数量。|
|Counter|short_watches_total|短时间 API watch 请求数量。|
|Summary|watch_duration_seconds|API watch 持续时间。|
|Summary|items_per_watch|API watch 返回结果数量。|
|Gauge|last_resource_version|最新的 resource version。|
|Histogram|ovs_client_request_latency_milliseconds|请求 OVN 组件延迟。|
|Counter|ovn_subnet_gateway_packet_bytes|OVN 子网网关处理的流量字节数，标签中包含 hostname、subnet_name、cidr、direction、protocol。|
|Counter|ovn_subnet_gateway_packets|OVN 子网网关处理的数据包数量，标签中包含 hostname、subnet_name、cidr、direction、protocol。|
|Gauge|ip_local_port_range|主机内核参数 `/proc/sys/net/ipv4/ip_local_port_range` 取值，用于检测是否与 Kubernetes NodePort 范围冲突。|
|Gauge|checksum_err_count|主机 `/proc/net/snmp` 中的 `InCsumErrors` 校验和错误计数，大于 0 说明存在网络丢包或校验和异常。|
|Gauge|dns_search_domain|主机 `/etc/resolv.conf` 中的 search domain 数量及附加域信息。|
|Gauge|tcp_tw_recycle|主机内核参数 `/proc/sys/net/ipv4/tcp_tw_recycle` 取值，推荐值为 0。|
|Gauge|tcp_mtu_probing|主机内核参数 `/proc/sys/net/ipv4/tcp_mtu_probing` 取值，推荐值为 1。|
|Gauge|nf_conntrack_tcp_be_liberal|主机内核参数 `/proc/sys/net/netfilter/nf_conntrack_tcp_be_liberal` 取值，推荐值为 1。|
|Gauge|bridge_nf_call_iptables|主机内核参数 `/proc/sys/net/bridge/bridge-nf-call-iptables` 取值（Overlay 推荐 1，Underlay 推荐 0）。|
|Gauge|tcp_mem|主机内核参数 `/proc/sys/net/ipv4/tcp_mem` 内存阈值（min, pressure, max）。|
|Gauge|max_size|主机 IPv6 路由表最大容量限制 `/proc/sys/net/ipv6/route/max_size`，推荐至少 16384。|

## kube-ovn-speaker

`kube-ovn-speaker` 相关监控指标（BGP Speaker 与 BFD）：

|类型|指标项|描述|
|---|---|---|
|Gauge|kube_ovn_speaker_bgp_peer_up|与对端节点的 BGP 会话是否建立，(1) 为已建立（Established），(0) 为未建立。|
|Gauge|kube_ovn_speaker_bgp_peer_session_state|与对端节点的 BGP 状态机状态（0=unspecified, 1=idle, 2=connect, 3=active, 4=opensent, 5=openconfirm, 6=established）。|
|Gauge|kube_ovn_speaker_bgp_peer_flap_count|与对端节点的 BGP 会话发生震荡（flap）的累计次数。|
|Gauge|kube_ovn_speaker_bgp_peer_out_queue|当前等待发送给该 BGP Peer 的消息排队数量。|
|Gauge|kube_ovn_speaker_bgp_peer_received_messages|从该 BGP Peer 接收到的各类 BGP 协议消息累计数量，按 type 标签区分。|
|Gauge|kube_ovn_speaker_bgp_peer_sent_messages|向该 BGP Peer 发送的各类 BGP 协议消息累计数量，按 type 标签区分。|
|Gauge|kube_ovn_speaker_bfd_server_received_packets|BFD 服务端接收到的 BFD 报文累计总数。|
|Gauge|kube_ovn_speaker_bfd_server_received_drop|BFD 服务端丢弃的 BFD 报文累计总数。|
|Gauge|kube_ovn_speaker_bfd_server_received_error|BFD 服务端接收到的错误 BFD 报文累计总数。|
|Gauge|kube_ovn_speaker_bfd_server_invalid_packet|BFD 服务端收到的非法或格式无效 BFD 报文累计总数。|
|Gauge|kube_ovn_speaker_bfd_server_unknown_peer|BFD 服务端收到来自未识别 Peer 的 BFD 报文累计总数。|
|Gauge|kube_ovn_speaker_bfd_peer_up|与该对端节点的 BFD 会话是否处于 UP 状态，(1) 为正常，(0) 为异常。|
|Gauge|kube_ovn_speaker_bfd_peer_session_state|本地与该 Peer 的 BFD 会话状态（0=unspecified, 1=up, 2=down, 3=admin_down, 4=init）。|
|Gauge|kube_ovn_speaker_bfd_peer_remote_session_state|远端对该 Peer 报告的 BFD 会话状态（0=unspecified, 1=up, 2=down, 3=admin_down, 4=init）。|
|Gauge|kube_ovn_speaker_bfd_peer_failure_transitions|该 Peer 的 BFD 会话转入故障状态的累计切换次数。|
|Gauge|kube_ovn_speaker_bfd_peer_transmitted_packets|与该 Peer 建立的 BFD 异步会话中已发送的 BFD 报文累计总数。|
|Gauge|kube_ovn_speaker_bfd_peer_received_packets|与该 Peer 建立的 BFD 异步会话中已接收的 BFD 报文累计总数。|

## vpc-egress-gateway-observer

VPC 出口网关（`VpcEgressGateway`）原生可观测性采集指标：

|类型|指标项|描述|
|---|---|---|
|Gauge|kube_ovn_vpc_egress_gateway_observability_collector_up|网关 Observer 内部各 Collector 组件是否正常运行，(1) 为正常，(0) 为异常。|
|Counter|kube_ovn_vpc_egress_gateway_observability_config_reload_total|Observer 动态重载配置文件的累计尝试次数，按 result 标签统计。|
|Counter|kube_ovn_vpc_egress_gateway_observability_conntrack_events_total|Observer 监听并处理的 conntrack 连接跟踪事件累计总数，按 event 标签区分。|
|Counter|kube_ovn_vpc_egress_gateway_observability_errors_total|Observer 采集器运行过程中遭遇的内部错误总数。|
|Gauge|kube_ovn_vpc_egress_gateway_observability_conntrack_cache_entries|当前本地 conntrack 流缓存中的活动连接条目数。|
|Gauge|kube_ovn_vpc_egress_gateway_observability_conntrack_cache_capacity|本地 conntrack 流缓存的最大容量上限。|
|Counter|kube_ovn_vpc_egress_gateway_observability_conntrack_cache_evictions_total|因缓存满或超时导致的 conntrack 缓存项驱逐淘汰累计总数。|
|Counter|kube_ovn_vpc_egress_gateway_observability_log_records_total|成功输出到标准输出的 JSON 格式 NAT 流日志记录累计条数。|
|Counter|kube_ovn_vpc_egress_gateway_observability_log_drops_total|因限速或通道满等原因丢弃的流日志记录累计条数。|
|Gauge|kube_ovn_vpc_egress_gateway_observability_conntrack_accounting_available|内核是否支持并启用了 conntrack 流量与数据包字节记账功能，(1) 为支持，(0) 为不支持。|
|Counter|kube_ovn_vpc_egress_gateway_interface_rx_bytes_total|网关网络接口接收到的累计流量字节数，标签中包含 interface、type。|
|Counter|kube_ovn_vpc_egress_gateway_interface_tx_bytes_total|网关网络接口发送出的累计流量字节数，标签中包含 interface、type。|
|Counter|kube_ovn_vpc_egress_gateway_interface_rx_packets_total|网关网络接口接收到的累计数据包数量。|
|Counter|kube_ovn_vpc_egress_gateway_interface_tx_packets_total|网关网络接口发送出的累计数据包数量。|
|Counter|kube_ovn_vpc_egress_gateway_interface_drops_total|网关网络接口丢弃的数据包累计总数，按 direction 标签统计。|
|Counter|kube_ovn_vpc_egress_gateway_interface_errors_total|网关网络接口发生错误的数据包累计总数，按 direction 标签统计。|
|Gauge|kube_ovn_vpc_egress_gateway_conntrack_nat_flows_active|网关当前处于活跃状态的 NAT 连接跟踪流总数，标签中包含 address_family、protocol、nat_type。|
|Counter|kube_ovn_vpc_egress_gateway_conntrack_nat_flows_started_total|网关累计新建启动的 NAT 连接跟踪流总数。|
|Counter|kube_ovn_vpc_egress_gateway_conntrack_nat_flows_ended_total|网关累计结束关闭的 NAT 连接跟踪流总数。|
|Counter|kube_ovn_vpc_egress_gateway_conntrack_nat_packets_total|启用内核记账时，NAT 连接跟踪流所统计的累计数据包数量。|
|Counter|kube_ovn_vpc_egress_gateway_conntrack_nat_bytes_total|启用内核记账时，NAT 连接跟踪流所统计的累计流量字节数。|
