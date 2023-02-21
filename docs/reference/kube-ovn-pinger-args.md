# Kube-OVN-Pinger 参数参考

基于 Kube-OVN v1.12.0 版本，整理了 Kube-ovn-pinger 支持的参数，列出参数定义各字段的取值类型，含义和默认值，以供参考

## 参数描述

| 属性名称 | 类型 | 描述 | 默认值 |
| --- | --- | --- | --- |
| port | Int | metrics 端口 | 8080 |
| kubeconfig | String | 具有认证信息的 kubeconfig 文件路径， 如果未设置，使用 inCluster 令牌。 | "" |
| ds-namespace | String | kube-ovn-pinger 守护进程命名空间 | "kube-system" |
| ds-name | String | kube-ovn-pinger 守护进程名字 | "kube-ovn-pinger" |
| interval | Int | 连续 ping 之间的间隔秒数 | 5 |
| mode | String | 服务器或工作模式 | "server" |
| exit-code | Int | 失败时退出代码 | 0 |
| internal-dns | String | 从 pod 内解析内部 dns | "kubernetes.default" |
| external-dns | String | 从 pod 内解析外部 dns | "" |
| external-address | String | 检查与外部地址的 ping 连通 | "114.114.114.114" |
| network-mode | String | 当前集群使用的 cni 插件 | "kube-ovn" |
| enable-metrics | Bool | 是否支持 metrics 查询 | true |
| ovs.timeout | Int | 对 OVS 的 JSON-RPC 请求超时。 | 2 |
| system.run.dir | String | OVS 默认运行目录。 | "/var/run/openvswitch" |
| database.vswitch.name | String | OVS 数据库的名称。 | "Open_vSwitch" |
| database.vswitch.socket.remote | String | JSON-RPC unix 套接字到 OVS 数据库。 | "unix:/var/run/openvswitch/db.sock" |
| database.vswitch.file.data.path | String | OVS 数据库文件。 | "/etc/openvswitch/conf.db" |
| database.vswitch.file.log.path | String | OVS 数据库日志文件。 | "/var/log/openvswitch/ovsdb-server.log" |
| database.vswitch.file.pid.path | String | OVS 数据库进程 ID 文件。 | "/var/run/openvswitch/ovsdb-server.pid" |
| database.vswitch.file.system.id.path | String | OVS 系统标识文件。 | "/etc/openvswitch/system-id.conf" |
| service.vswitchd.file.log.path | String | OVS vswitchd 守护进程日志文件。 | "/var/log/openvswitch/ovs-vswitchd.log" |
| service.vswitchd.file.pid.path | String | OVS vswitchd 守护进程进程 ID 文件。 | "/var/run/openvswitch/ovs-vswitchd.pid" |
| service.ovncontroller.file.log.path | String | OVN 控制器守护进程日志文件。 | "/var/log/ovn/ovn-controller.log" |
| service.ovncontroller.file.pid.path | String | OVN 控制器守护进程进程 ID 文件。 | "/var/run/ovn/ovn-controller.pid" |
