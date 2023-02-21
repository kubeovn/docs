# Kube-OVN-Pinger args Reference

Based on the Kube-OVN v1.12.0 version, We have compiled the parameters supported by Kube-ovn-pinger, and listed the value types, meanings, and default values of each field defined by the parameters for reference

## Args Describeption

| Arg Name | Type | Description | Default Value |
| --- | --- | --- | --- |
| port | Int | metrics port | 8080 |
| kubeconfig | String | Path to kubeconfig file with authorization and master location information. If not set use the inCluster token. | "" |
| ds-namespace | String | kube-ovn-pinger daemonset namespace | "kube-system" |
| ds-name | String | kube-ovn-pinger daemonset name | "kube-ovn-pinger" |
| interval | Int | interval seconds between consecutive pings | 5 |
| mode | String | server or job Mode | "server" |
| exit-code | Int | exit code when failure happens | 0 |
| internal-dns | String | check dns from pod | "kubernetes.default" |
| external-dns | String | check external dns resolve from pod | "" |
| external-address | String | check ping connection to an external address | "114.114.114.114" |
| network-mode | String | The cni plugin current cluster used | "kube-ovn" |
| enable-metrics | Bool | Whether to support metrics query | true |
| ovs.timeout | Int | Timeout on JSON-RPC requests to OVS. | 2 |
| system.run.dir | String | OVS default run directory. | "/var/run/openvswitch" |
| database.vswitch.name | String | The name of OVS db. | "Open_vSwitch" |
| database.vswitch.socket.remote | String | JSON-RPC unix socket to OVS db. | "unix:/var/run/openvswitch/db.sock" |
| database.vswitch.file.data.path | String | OVS db file. | "/etc/openvswitch/conf.db" |
| database.vswitch.file.log.path | String | OVS db log file. | "/var/log/openvswitch/ovsdb-server.log" |
| database.vswitch.file.pid.path | String | OVS db process id file. | "/var/run/openvswitch/ovsdb-server.pid" |
| database.vswitch.file.system.id.path | String | OVS system id file. | "/etc/openvswitch/system-id.conf" |
| service.vswitchd.file.log.path | String | OVS vswitchd daemon log file. | "/var/log/openvswitch/ovs-vswitchd.log" |
| service.vswitchd.file.pid.path | String | OVS vswitchd daemon process id file. | "/var/run/openvswitch/ovs-vswitchd.pid" |
| service.ovncontroller.file.log.path | String | OVN controller daemon log file. | "/var/log/ovn/ovn-controller.log" |
| service.ovncontroller.file.pid.path | String | OVN controller daemon process id file. | "/var/run/ovn/ovn-controller.pid" |
