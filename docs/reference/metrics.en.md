# Metrics

This document lists all the monitoring metrics provided by Kube-OVN.

## ovn-monitor

OVN status metrics:

| Type | Metric | Description |
| ------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Gauge | kube_ovn_ovn_status | OVN Health Status. The values are: (2) for standby or follower, (1) for active or leader, (0) for unhealthy. |
| Gauge | kube_ovn_failed_req_count | The number of failed requests to OVN stack. |
| Gauge | kube_ovn_log_file_size_bytes | The size of a log file associated with an OVN component. |
| Gauge | kube_ovn_db_file_size_bytes | The size of a database file associated with an OVN component. |
| Gauge | kube_ovn_chassis_info | Whether the OVN chassis is up (1) or down (0), together with additional information about the chassis. |
| Gauge | kube_ovn_db_status | The status of OVN NB/SB DB, (1) for healthy, (0) for unhealthy. |
| Gauge | kube_ovn_logical_switch_info | The information about OVN logical switch. This metric is always up (1). |
| Gauge | kube_ovn_logical_switch_external_id | Provides the external IDs and values associated with OVN logical switches. This metric is always up (1). |
| Gauge | kube_ovn_logical_switch_port_binding | Provides the association between a logical switch and a logical switch port. This metric is always up (1). |
| Gauge | kube_ovn_logical_switch_tunnel_key | The value of the tunnel key associated with the logical switch. |
| Gauge | kube_ovn_logical_switch_ports_num | The number of logical switch ports connected to the OVN logical switch. |
| Gauge | kube_ovn_logical_switch_port_info | The information about OVN logical switch port. This metric is always up (1). |
| Gauge | kube_ovn_logical_switch_port_tunnel_key | The value of the tunnel key associated with the logical switch port. |
| Gauge | kube_ovn_cluster_enabled | Is OVN clustering enabled (1) or not (0). |
| Gauge | kube_ovn_cluster_role | A metric with a constant '1' value labeled by server role. |
| Gauge | kube_ovn_cluster_status | A metric with a constant '1' value labeled by server status. |
| Gauge | kube_ovn_cluster_term | The current raft term known by this server. |
| Gauge | kube_ovn_cluster_leader_self | Is this server consider itself a leader (1) or not (0). |
| Gauge | kube_ovn_cluster_vote_self | Is this server voted itself as a leader (1) or not (0). |
| Gauge | kube_ovn_cluster_election_timer | The current election timer value. |
| Gauge | kube_ovn_cluster_log_not_committed | The number of log entries not yet committed by this server. |
| Gauge | kube_ovn_cluster_log_not_applied | The number of log entries not yet applied by this server. |
| Gauge | kube_ovn_cluster_log_index_start | The log entry index start value associated with this server. |
| Gauge | kube_ovn_cluster_log_index_next | The log entry index next value associated with this server. |
| Gauge | kube_ovn_cluster_inbound_connections_total | The total number of inbound connections to the server. |
| Gauge | kube_ovn_cluster_outbound_connections_total | The total number of outbound connections from the server. |
| Gauge | kube_ovn_cluster_inbound_connections_error_total | The total number of failed inbound connections to the server. |
| Gauge | kube_ovn_cluster_outbound_connections_error_total | The total number of failed outbound connections from the server. |
| Gauge | kube_ovn_ovn_status_content | Specific error message and reason when OVN is unhealthy, always set to 1, labeled by role and reason. |
| Gauge | kube_ovn_cluster_peer_inbound_connections_info | Inbound connection status for a Raft peer, always set to 1, labeled by role, server_id, address, and status. |
| Gauge | kube_ovn_cluster_peer_outbound_connections_info | Outbound connection status for a Raft peer, always set to 1, labeled by role, server_id, address, and status. |
| Gauge | kube_ovn_cluster_peer_count | The total number of recognized peers in the Raft cluster. |
| Gauge | kube_ovn_cluster_peer_next_index | Next index for each peer in the Raft cluster. |
| Gauge | kube_ovn_cluster_peer_match_index | Match index for each peer in the Raft cluster. |
| Gauge | kube_ovn_cluster_next_index | Global next index maintained by the current DB server. |
| Gauge | kube_ovn_cluster_match_index | Global match index maintained by the current DB server. |

## ovs-monitor

`ovsdb` and `vswitchd` status metrics:

| Type | Metric | Description |
| ------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Gauge | ovs_status | OVS Health Status. The values are: health(1), unhealthy(0). |
| Gauge | ovs_info | This metric provides basic information about OVS. It is always set to 1. |
| Gauge | failed_req_count | The number of failed requests to OVS stack. |
| Gauge | log_file_size_bytes | The size (in bytes) of a log file associated with an OVS component. |
| Gauge | db_file_size_bytes | The size (in bytes) of a database file associated with an OVS component. |
| Gauge | datapath | Represents an existing datapath. This metric is always 1. |
| Gauge | dp_total | Represents total number of datapaths on the system. |
| Gauge | dp_if | Represents an existing datapath interface. This metric is always 1. |
| Gauge | dp_if_total | Represents the number of ports connected to the datapath. |
| Gauge | dp_flows_total | The number of flows in a datapath. |
| Gauge | dp_flows_lookup_hit | The number of incoming packets in a datapath matching existing flows in the datapath. |
| Gauge | dp_flows_lookup_missed | The number of incoming packets in a datapath not matching any existing flow in the datapath. |
| Gauge | dp_flows_lookup_lost | The number of incoming packets in a datapath destined for userspace process but subsequently dropped before reaching userspace. |
| Gauge | dp_masks_hit | The total number of masks visited for matching incoming packets. |
| Gauge | dp_masks_total | The number of masks in a datapath. |
| Gauge | dp_masks_hit_ratio | The average number of masks visited per packet. It is the ratio between hit and total number of packets processed by a datapath. |
| Gauge | interface | Represents OVS interface. This is the primary metric for all other interface metrics. This metric is always 1. |
| Gauge | interface_admin_state | The administrative state of the physical network link of OVS interface. The values are: down(0), up(1), other(2). |
| Gauge | interface_link_state | The state of the physical network link of OVS interface. The values are: down(0), up(1), other(2). |
| Gauge | interface_mac_in_use | The MAC address in use by OVS interface. |
| Gauge | interface_mtu | The currently configured MTU for OVS interface. |
| Gauge | interface_of_port | Represents the OpenFlow port ID associated with OVS interface. |
| Gauge | interface_if_index | Represents the interface index associated with OVS interface. |
| Gauge | interface_tx_packets | Represents the number of transmitted packets by OVS interface. |
| Gauge | interface_tx_bytes | Represents the number of transmitted bytes by OVS interface. |
| Gauge | interface_rx_packets | Represents the number of received packets by OVS interface. |
| Gauge | interface_rx_bytes | Represents the number of received bytes by OVS interface. |
| Gauge | interface_rx_crc_err | Represents the number of CRC errors for the packets received by OVS interface. |
| Gauge | interface_rx_dropped | Represents the number of input packets dropped by OVS interface. |
| Gauge | interface_rx_errors | Represents the total number of packets with errors received by OVS interface. |
| Gauge | interface_rx_frame_err | Represents the number of frame alignment errors on the packets received by OVS interface. |
| Gauge | interface_rx_missed_err | Represents the number of packets with RX missed received by OVS interface. |
| Gauge | interface_rx_over_err | Represents the number of packets with RX overrun received by OVS interface. |
| Gauge | interface_tx_dropped | Represents the number of output packets dropped by OVS interface. |
| Gauge | interface_tx_errors | Represents the total number of transmit errors by OVS interface. |
| Gauge | interface_collisions | Represents the number of collisions on OVS interface. |
| Gauge | interface_rx_multicast_packets | Represents the number of multicast packets received by OVS interface. |

## kube-ovn-pinger

Network quality related metrics:

| Type | Metric | Description |
| ----------- | ---------------------------------- | ------------------------------------------------------------- |
| Gauge | pinger_ovs_up | If the ovs on the node is up |
| Gauge | pinger_ovs_down | If the ovs on the node is down |
| Gauge | pinger_ovn_controller_up | If the ovn_controller on the node is up |
| Gauge | pinger_ovn_controller_down | If the ovn_controller on the node is down |
| Gauge | pinger_inconsistent_port_binding | The number of mismatch port bindings between ovs and ovn-sb |
| Gauge | pinger_apiserver_healthy | If the apiserver request is healthy on this node |
| Gauge | pinger_apiserver_unhealthy | If the apiserver request is unhealthy on this node |
| Histogram | pinger_apiserver_latency_ms | The latency ms histogram the node request apiserver |
| Gauge | pinger_internal_dns_healthy | If the internal dns request is healthy on this node |
| Gauge | pinger_internal_dns_unhealthy | If the internal dns request is unhealthy on this node |
| Histogram | pinger_internal_dns_latency_ms | The latency ms histogram the node request internal dns |
| Gauge | pinger_external_dns_healthy | If the external dns request is healthy on this node |
| Gauge | pinger_external_dns_unhealthy | If the external dns request is unhealthy on this node |
| Histogram | pinger_external_dns_latency_ms | The latency ms histogram the node request external dns |
| Histogram | pinger_pod_ping_latency_ms | The latency ms histogram for pod peer ping |
| Counter | pinger_pod_ping_lost_total | The lost count for pod peer ping |
| Counter | pinger_pod_ping_count_total | The total count for pod peer ping |
| Histogram | pinger_node_ping_latency_ms | The latency ms histogram for pod ping node |
| Counter | pinger_node_ping_lost_total | The lost count for pod ping node |
| Counter | pinger_node_ping_count_total | The total count for pod ping node |
| Histogram | pinger_external_ping_latency_ms | The latency ms histogram for pod ping external address |
| Counter | pinger_external_ping_lost_total | The lost count for pod ping external address |

## kube-ovn-controller

`kube-ovn-controller` status metrics:

| Type | Metric | Description |
| ----------- | ----------------------------------------- | ----------------------------------------------------------------------- |
| Histogram | rest_client_request_latency_seconds | Request latency in seconds. Broken down by verb and URL |
| Counter | rest_client_requests_total | Number of HTTP requests, partitioned by status code, method, and host |
| Counter | lists_total | Total number of API lists done by the reflectors |
| Summary | list_duration_seconds | How long an API list takes to return and decode for the reflectors |
| Summary | items_per_list | How many items an API list returns to the reflectors |
| Counter | watches_total | Total number of API watches done by the reflectors |
| Counter | short_watches_total | Total number of short API watches done by the reflectors |
| Summary | watch_duration_seconds | How long an API watch takes to return and decode for the reflectors |
| Summary | items_per_watch | How many items an API watch returns to the reflectors |
| Gauge | last_resource_version | Last resource version seen for the reflectors |
| Histogram | ovs_client_request_latency_milliseconds | The latency histogram for ovs request |
| Gauge | subnet_available_ip_count | The available num of ip address in subnet |
| Gauge | subnet_used_ip_count | The used num of ip address in subnet |
| Gauge | centralized_subnet_info | Provides information for centralized subnet, always set to 1, labeled by subnet_name, enable_ecmp, gateway_node, active_gateway, match, and nexthops |
| Gauge | subnet_ipam_info | Provides information for subnet IP address management, always set to 1, labeled by subnet_name, cidr, free, reserved, available, and using |
| Gauge | subnet_ip_assign_info | Provides information for subnet IP addresses assigned to pods, always set to 1, labeled by subnet_name, ip, and pod_name |
| Gauge | acl_sampling_controller_available | Whether the controller ACL sampling path is enabled and its latest operation succeeded (1 for normal, 0 for unhealthy) |
| Counter | acl_sampling_controller_failures_total | The number of controller ACL sampling failures partitioned by operation |

## kube-ovn-cni

`kube-ovn-cni` status metrics:

| Type | Metric | Description |
| ----------- | ----------------------------------------- | ----------------------------------------------------------------------- |
| Histogram | cni_op_latency_seconds | The latency seconds for cni operations |
| Counter | cni_wait_address_seconds_total | Latency that cni wait controller to assign an address |
| Counter | cni_wait_connectivity_seconds_total | Latency that cni wait address ready in overlay network |
| Counter | cni_wait_route_seconds_total | Latency that cni wait controller to add routed annotation to pod |
| Histogram | rest_client_request_latency_seconds | Request latency in seconds. Broken down by verb and URL |
| Counter | rest_client_requests_total | Number of HTTP requests, partitioned by status code, method, and host |
| Counter | lists_total | Total number of API lists done by the reflectors |
| Summary | list_duration_seconds | How long an API list takes to return and decode for the reflectors |
| Summary | items_per_list | How many items an API list returns to the reflectors |
| Counter | watches_total | Total number of API watches done by the reflectors |
| Counter | short_watches_total | Total number of short API watches done by the reflectors |
| Summary | watch_duration_seconds | How long an API watch takes to return and decode for the reflectors |
| Summary | items_per_watch | How many items an API watch returns to the reflectors |
| Gauge | last_resource_version | Last resource version seen for the reflectors |
| Histogram | ovs_client_request_latency_milliseconds | The latency histogram for ovs request |
| Counter | ovn_subnet_gateway_packet_bytes | The OVN subnet gateway packet bytes, labeled by hostname, subnet_name, cidr, direction, and protocol |
| Counter | ovn_subnet_gateway_packets | The OVN subnet gateway packet count, labeled by hostname, subnet_name, cidr, direction, and protocol |
| Gauge | ip_local_port_range | Value of system parameter `/proc/sys/net/ipv4/ip_local_port_range`, which should not conflict with the NodePort range |
| Gauge | checksum_err_count | Value of InCsumErrors from `/proc/net/snmp`; checksum has errors when value is greater than 0 |
| Gauge | dns_search_domain | Search domain count and additional domains in `/etc/resolv.conf` |
| Gauge | tcp_tw_recycle | Value of system parameter `/proc/sys/net/ipv4/tcp_tw_recycle`, recommended value is 0 |
| Gauge | tcp_mtu_probing | Value of system parameter `/proc/sys/net/ipv4/tcp_mtu_probing`, recommended value is 1 |
| Gauge | nf_conntrack_tcp_be_liberal | Value of system parameter `/proc/sys/net/netfilter/nf_conntrack_tcp_be_liberal`, recommended value is 1 |
| Gauge | bridge_nf_call_iptables | Value of system parameter `/proc/sys/net/bridge/bridge-nf-call-iptables`, recommended value is 1 for overlay and 0 for underlay |
| Gauge | tcp_mem | Value of system parameter `/proc/sys/net/ipv4/tcp_mem`, minimum, pressure, and maximum memory thresholds |
| Gauge | max_size | Value of system parameter `/proc/sys/net/ipv6/route/max_size`, recommended value is at least 16384 |
| Gauge | acl_sampling_node_available | Whether local ACL sampling delivery is available on the node (1 for available, 0 for unavailable) |
| Counter | acl_sampling_node_failures_total | Total number of local ACL sampling reconciliation failures on the node |
| Gauge | kube_ovn_gateway_netfilter_backend | Current gateway netfilter backend, labeled by backend (`iptables` or `nftables`); active backend is set to 1 |
| Counter | kube_ovn_gateway_netfilter_detect_failures_total | Number of kube-proxy mode detection failures |
| Counter | kube_ovn_gateway_netfilter_switch_failures_total | Number of gateway netfilter backend switch failures |
| Counter | kube_ovn_gateway_nft_transactions_total | Number of Kube-OVN nftables transactions |
| Counter | kube_ovn_gateway_nft_transaction_failures_total | Number of failed Kube-OVN nftables transactions |
| Histogram | kube_ovn_gateway_nft_transaction_duration_seconds | Duration of Kube-OVN nftables transactions in seconds |
| Counter | kube_ovn_gateway_nft_repairs_total | Number of Kube-OVN nftables drift repairs |

## kube-ovn-speaker

`kube-ovn-speaker` status metrics (BGP Speaker and BFD):

| Type | Metric | Description |
| ----------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Gauge | kube_ovn_speaker_bgp_peer_up | Whether the BGP session with the peer is established (1) or not (0) |
| Gauge | kube_ovn_speaker_bgp_peer_session_state | BGP session FSM state of the peer (0=unspecified, 1=idle, 2=connect, 3=active, 4=opensent, 5=openconfirm, 6=established) |
| Gauge | kube_ovn_speaker_bgp_peer_flap_count | Number of times the BGP session with the peer has flapped |
| Gauge | kube_ovn_speaker_bgp_peer_out_queue | Number of BGP messages queued to be sent to the peer |
| Gauge | kube_ovn_speaker_bgp_peer_received_messages | Cumulative number of BGP messages received from the peer, labeled by type |
| Gauge | kube_ovn_speaker_bgp_peer_sent_messages | Cumulative number of BGP messages sent to the peer, labeled by type |
| Gauge | kube_ovn_speaker_bfd_server_received_packets | Cumulative number of BFD packets received by the server |
| Gauge | kube_ovn_speaker_bfd_server_received_drop | Cumulative number of BFD packets dropped by the server |
| Gauge | kube_ovn_speaker_bfd_server_received_error | Cumulative number of BFD packets received with errors by the server |
| Gauge | kube_ovn_speaker_bfd_server_invalid_packet | Cumulative number of invalid BFD packets received by the server |
| Gauge | kube_ovn_speaker_bfd_server_unknown_peer | Cumulative number of BFD packets received from unknown peers |
| Gauge | kube_ovn_speaker_bfd_peer_up | Whether the BFD session with the peer is UP (1) or not (0) |
| Gauge | kube_ovn_speaker_bfd_peer_session_state | Local BFD session state of the peer (0=unspecified, 1=up, 2=down, 3=admin_down, 4=init) |
| Gauge | kube_ovn_speaker_bfd_peer_remote_session_state | Remote BFD session state of the peer (0=unspecified, 1=up, 2=down, 3=admin_down, 4=init) |
| Gauge | kube_ovn_speaker_bfd_peer_failure_transitions | Cumulative number of BFD session failure transitions for the peer |
| Gauge | kube_ovn_speaker_bfd_peer_transmitted_packets | Cumulative number of BFD packets transmitted to the peer in the BFD session |
| Gauge | kube_ovn_speaker_bfd_peer_received_packets | Cumulative number of BFD packets received from the peer in the BFD session |

## vpc-egress-gateway-observer

VPC Egress Gateway (`VpcEgressGateway`) observability metrics:

| Type | Metric | Description |
| ----------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Gauge | kube_ovn_vpc_egress_gateway_observability_collector_up | Whether an observer collector is operating successfully (1 for healthy, 0 for unhealthy) |
| Counter | kube_ovn_vpc_egress_gateway_observability_config_reload_total | Observer configuration reload attempts, labeled by result |
| Counter | kube_ovn_vpc_egress_gateway_observability_conntrack_events_total | Conntrack events processed by the observer, labeled by event |
| Counter | kube_ovn_vpc_egress_gateway_observability_errors_total | Observer collector errors, labeled by collector and operation |
| Gauge | kube_ovn_vpc_egress_gateway_observability_conntrack_cache_entries | Current entries in the conntrack flow cache |
| Gauge | kube_ovn_vpc_egress_gateway_observability_conntrack_cache_capacity | Maximum conntrack flow cache entries |
| Counter | kube_ovn_vpc_egress_gateway_observability_conntrack_cache_evictions_total | Conntrack cache evictions |
| Counter | kube_ovn_vpc_egress_gateway_observability_log_records_total | Flow log records written to stdout |
| Counter | kube_ovn_vpc_egress_gateway_observability_log_drops_total | Flow log records dropped due to rate limiting or channel congestion |
| Gauge | kube_ovn_vpc_egress_gateway_observability_conntrack_accounting_available | Whether conntrack accounting counters are available in kernel (1 for available, 0 for unavailable) |
| Counter | kube_ovn_vpc_egress_gateway_interface_rx_bytes_total | Bytes received by a gateway interface, labeled by interface and type |
| Counter | kube_ovn_vpc_egress_gateway_interface_tx_bytes_total | Bytes transmitted by a gateway interface, labeled by interface and type |
| Counter | kube_ovn_vpc_egress_gateway_interface_rx_packets_total | Packets received by a gateway interface, labeled by interface and type |
| Counter | kube_ovn_vpc_egress_gateway_interface_tx_packets_total | Packets transmitted by a gateway interface, labeled by interface and type |
| Counter | kube_ovn_vpc_egress_gateway_interface_drops_total | Packets dropped by a gateway interface, labeled by direction |
| Counter | kube_ovn_vpc_egress_gateway_interface_errors_total | Packet errors observed by a gateway interface, labeled by direction |
| Gauge | kube_ovn_vpc_egress_gateway_conntrack_nat_flows_active | Active NAT conntrack flows, labeled by address_family, protocol, and nat_type |
| Counter | kube_ovn_vpc_egress_gateway_conntrack_nat_flows_started_total | NAT conntrack flows started |
| Counter | kube_ovn_vpc_egress_gateway_conntrack_nat_flows_ended_total | NAT conntrack flows ended |
| Counter | kube_ovn_vpc_egress_gateway_conntrack_nat_packets_total | Packets observed in NAT conntrack flows when accounting is available |
| Counter | kube_ovn_vpc_egress_gateway_conntrack_nat_bytes_total | Bytes observed in NAT conntrack flows when accounting is available |
