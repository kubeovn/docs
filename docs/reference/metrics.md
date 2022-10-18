# Kube-OVN 监控指标

本文档列举 Kube-OVN 所提供的监控指标。

## ovn-monitor

OVN 自身状态监控指标：

| 类型    | 指标项                                               | 描述                                                             |
|-------|---------------------------------------------------|----------------------------------------------------------------|
| Gauge | kube_ovn_ovn_status                               | OVN 角色状态， (2) 为 follower； (1) 为 leader, (0) 为异常状态。             |
| Gauge | kube_ovn_failed_req_count                         | OVN 失败请求数量。                                                    |
| Gauge | kube_ovn_log_file_size_bytes                      | OVN 组件日志文件大小。                                                  |
| Gauge | kube_ovn_db_file_size_bytes                       | OVN 组件数据库文件大小。                                                 |
| Gauge | kube_ovn_chassis_info                             | OVN chassis 状态 (1) 运行中，(0) 停止。                                 |
| Gauge | kube_ovn_db_status                                | OVN 数据库状态, (1) 为正常； (0) 为异常。                                   |
| Gauge | kube_ovn_logical_switch_info                      | OVN logical switch 信息，值为 (1)，标签中包含 logical switch 名字。          |
| Gauge | kube_ovn_logical_switch_external_id               | OVN logical switch external_id 信息，值为 (1)，标签中包含 external-id 内容。 |
| Gauge | kube_ovn_logical_switch_port_binding              | OVN logical switch 和 logical switch port 关联信息，值为 (1)，通过标签进行关联。 |
| Gauge | kube_ovn_logical_switch_tunnel_key                | 和 OVN logical switch 关联的 tunnel key 信息。                        |
| Gauge | kube_ovn_logical_switch_ports_num                 | OVN logical switch 上 logical port 的数量。                         |
| Gauge | kube_ovn_logical_switch_port_info                 | OVN logical switch port 信息，值为 (1)，标签中包含具体信息。                   |
| Gauge | kube_ovn_logical_switch_port_tunnel_key           | 和 OVN logical switch port 关联的 tunnel key 信息。                   |
| Gauge | kube_ovn_cluster_enabled                          | (1) OVN 数据库为集群模式； (0) OVN 数据库为非集群模式。                           |
| Gauge | kube_ovn_cluster_role                             | 每个数据库实例的角色，值为 (1)，标签中包含对应角色信息。                                 |
| Gauge | kube_ovn_cluster_status                           | 每个数据库实例的状态，值为 (1)，标签中包含对应状态信息。                                 |
| Gauge | kube_ovn_cluster_term                             | RAFT term 信息。                                                  |
| Gauge | kube_ovn_cluster_leader_self                      | 当前数据库实例是否为 leader (1) 是， (0) 不是。                               |
| Gauge | kube_ovn_cluster_vote_self                        | 当前数据库实例是否选举自己为 leader (1) 是， (0) 不是。                           |
| Gauge | kube_ovn_cluster_election_timer                   | 当前 election timer 值。                                           |
| Gauge | kube_ovn_cluster_log_not_committed                | 未 commit 的 RAFT 日志数量。                                          |
| Gauge | kube_ovn_cluster_log_not_applied                  | 未 apply 的 RAFT 日志数量。                                           |
| Gauge | kube_ovn_cluster_log_index_start                  | 当前 RAFT 日志条目的起始值。                                              |
| Gauge | kube_ovn_cluster_log_index_next                   | RAFT 日志条目的下一个值。                                                |
| Gauge | kube_ovn_cluster_inbound_connections_total        | 当前实例的入向连接数量。                                                   |
| Gauge | kube_ovn_cluster_outbound_connections_total       | 当前实例的出向连接数量。                                                   |
| Gauge | kube_ovn_cluster_inbound_connections_error_total  | 当前实例的入向错误连接数量。                                                 |
| Gauge | kube_ovn_cluster_outbound_connections_error_total | 当前实例的出向错误连接数量。                                                 |

## ovs-monitor

`ovsdb` 和 `vswitchd` 自身状态监控指标：

| 类型    | 指标项                     | 描述                                        |
|-------|-------------------------|-------------------------------------------|
| Gauge | ovs_status              | OVS 健康状态， (1) 为正常，(0) 为异常。                |
| Gauge | ovs_info                | OVS 基础信息，值为 (1)，标签中包含对应信息。                |
| Gauge | failed_req_count        | OVS 失败请求数量。                               |
| Gauge | log_file_size           | OVS 组件日志文件大小。                             |
| Gauge | db_file_size            | OVS 组件数据库文件大小。                            |
| Gauge | datapath                | Datapath 基础信息，值为 (1)，标签中包含对应信息。           |
| Gauge | dp_total                | 当前 OVS 中 datapath 数量。                     |
| Gauge | dp_if                   | Datapath 接口基础信息，值为 (1)，标签中包含对应信息。         |
| Gauge | dp_if_total             | 当前 datapath 中 port 数量。                    |
| Gauge | dp_flows_total          | Datapath 中 flow 数量。                       |
| Gauge | dp_flows_lookup_hit     | Datapath 中命中当前 flow 数据包数量。                |
| Gauge | dp_flows_lookup_missed  | Datapath 中未命中当前 flow 数据包数量。               |
| Gauge | dp_flows_lookup_lost    | Datapath 中需要发送给 userspace 处理的数据包数量。       |
| Gauge | dp_masks_hit            | Datapath 中命中当前 mask 数据包数量。                |
| Gauge | dp_masks_total          | Datapath 中 mask 的数量。                      |
| Gauge | dp_masks_hit_ratio      | Datapath 中 数据包命中 mask 的比率。                |
| Gauge | interface               | OVS 接口基础信息，值为 (1)，标签中包含对应信息。              |
| Gauge | interface_admin_state   | 接口管理状态信息 (0) 为 down, (1) 为 up, (2) 为其他状态。 |
| Gauge | interface_link_state    | 接口链路状态信息 (0) 为 down, (1) 为 up, (2) 为其他状态。 |
| Gauge | interface_mac_in_use    | OVS Interface 使用的 MAC 地址                  |
| Gauge | interface_mtu           | OVS Interface 使用的 MTU。                    |
| Gauge | interface_of_port       | OVS Interface 关联的 OpenFlow Port ID。       |
| Gauge | interface_if_index      | OVS Interface 关联的 Index。                  |
| Gauge | interface_tx_packets    | OVS Interface 发送包数量。                      |
| Gauge | interface_tx_bytes      | OVS Interface 发送包大小。                      |
| Gauge | interface_rx_packets    | OVS Interface 接收包数量。                      |
| Gauge | interface_rx_bytes      | OVS Interface 接收包大小。                      |
| Gauge | interface_rx_crc_err    | OVS Interface 接收包校验和错误数量。                 |
| Gauge | interface_rx_dropped    | OVS Interface 接收包丢弃数量。                    |
| Gauge | interface_rx_errors     | OVS Interface 接收包错误数量。                    |
| Gauge | interface_rx_frame_err  | OVS Interface 接收帧错误数量。                    |
| Gauge | interface_rx_missed_err | OVS Interface 接收包 miss 数量。                |
| Gauge | interface_rx_over_err   | OVS Interface 接收包 overrun 数量。             |
| Gauge | interface_tx_dropped    | OVS Interface 发送包丢弃数量。                    |
| Gauge | interface_tx_errors     | OVS Interface 发送包错误数量。                    |
| Gauge | interface_collisions    | OVS interface 冲突数量。                       |

## kube-ovn-pinger

网络质量相关监控指标：

| 类型        | 指标项                              | 描述                                               |
|-----------|----------------------------------|--------------------------------------------------|
| Gauge     | pinger_ovs_up                    | 节点 OVS 运行。                                       |
| Gauge     | pinger_ovs_down                  | 节点 OVS 停止。                                       |
| Gauge     | pinger_ovn_controller_up         | 节点 ovn-controller 运行。                            |
| Gauge     | pinger_ovn_controller_down       | 节点 ovn-controller 停止。                            |
| Gauge     | pinger_inconsistent_port_binding | OVN-SB 里 portbinding 数量和主机 OVS interface 不一致的数量。 |
| Gauge     | pinger_apiserver_healthy         | kube-ovn-pinger 可以联通 apiserver。                  |
| Gauge     | pinger_apiserver_unhealthy       | kube-ovn-pinger 无法联通 apiserver。                  |
| Histogram | pinger_apiserver_latency_ms      | kube-ovn-pinger 访问 apiserver 延迟。                 |
| Gauge     | pinger_internal_dns_healthy      | kube-ovn-pinger 可以解析内部域名。                        |
| Gauge     | pinger_internal_dns_unhealthy    | kube-ovn-pinger 无法解析内部域名。                        |
| Histogram | pinger_internal_dns_latency_ms   | kube-ovn-pinger 解析内部域名延迟。                        |
| Gauge     | pinger_external_dns_health       | kube-ovn-pinger 可以解析外部域名。                        |
| Gauge     | pinger_external_dns_unhealthy    | kube-ovn-pinger 无法解析外部域名。                        |
| Histogram | pinger_external_dns_latency_ms   | kube-ovn-pinger 解析外部域名延迟。                        |
| Histogram | pinger_pod_ping_latency_ms       | kube-ovn-pinger ping Pod 延迟。                     |
| Gauge     | pinger_pod_ping_lost_total       | kube-ovn-pinger ping Pod 丢包数量。                   |
| Gauge     | pinger_pod_ping_count_total      | kube-ovn-pinger ping Pod 数量。                     |
| Histogram | pinger_node_ping_latency_ms      | kube-ovn-pinger ping Node 延迟。                    |
| Gauge     | pinger_node_ping_lost_total      | kube-ovn-pinger ping Node 丢包。                    |
| Gauge     | pinger_node_ping_count_total     | kube-ovn-pinger ping Node 数量。                    |
| Histogram | pinger_external_ping_latency_ms  | kube-ovn-pinger ping 外部地址 延迟。                    |
| Gauge     | pinger_external_lost_total       | kube-ovn-pinger ping 外部丢包数量。                     |

## kube-ovn-controller

`kube-ovn-controller` 相关监控指标：

| 类型        | 指标项                                     | 描述                    |
|-----------|-----------------------------------------|-----------------------|
| Histogram | rest_client_request_latency_seconds     | 请求 apiserver 延迟。      |
| Counter   | rest_client_requests_total              | 请求 apiserver 数量。      |
| Counter   | lists_total                             | API list 请求数量。        |
| Summary   | list_duration_seconds                   | API list 请求延迟。        |
| Summary   | items_per_list                          | API list 返回结果数量。      |
| Counter   | watches_total                           | API watch 请求数量。       |
| Counter   | short_watches_total                     | 短时间 API watch 请求数量。   |
| Summary   | watch_duration_seconds                  | API watch 持续时间。       |
| Summary   | items_per_watch                         | API watch 返回结果数量。     |
| Gauge     | last_resource_version                   | 最新的 resource version。 |
| Histogram | ovs_client_request_latency_milliseconds | 请求 OVN 组件延迟。          |
| Gauge     | subnet_available_ip_count               | 子网可用 IP 数量。           |
| Gauge     | subnet_used_ip_count                    | 子网已用 IP 数量。           |

## kube-ovn-cni

`kube-ovn-cni` 相关监控指标：

| 类型        | 指标项                                     | 描述                    |
|-----------|-----------------------------------------|-----------------------|
| Histogram | cni_op_latency_seconds                  | CNI 操作延迟。             |
| Counter   | cni_wait_address_seconds_total          | CNI 等待地址就绪时间。         |
| Counter   | cni_wait_connectivity_seconds_total     | CNI 等待连接就绪时间。         |
| Counter   | cni_wait_route_seconds_total            | CNI 等待路由就绪时间。         |
| Histogram | rest_client_request_latency_seconds     | 请求 apiserver 延迟。      |
| Counter   | rest_client_requests_total              | 请求 apiserver 数量。      |
| Counter   | lists_total                             | API list 请求数量。        |
| Summary   | list_duration_seconds                   | API list 请求延迟。        |
| Summary   | items_per_list                          | API list 返回结果数量。      |
| Counter   | watches_total                           | API watch 请求数量。       |
| Counter   | short_watches_total                     | 短时间 API watch 请求数量。   |
| Summary   | watch_duration_seconds                  | API watch 持续时间。       |
| Summary   | items_per_watch                         | API watch 返回结果数量。     |
| Gauge     | last_resource_version                   | 最新的 resource version。 |
| Histogram | ovs_client_request_latency_milliseconds | 请求 OVN 组件延迟。          |
