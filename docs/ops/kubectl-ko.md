# kubectl-ko 插件

`kubectl-ko` 是用于操作和诊断 Kube-OVN 的 Go 编写的 kubectl 插件。它通过
Kubernetes API 获取资源，并将需要节点权限的操作转发给独立的
`kubectl-ko-node-agent` DaemonSet。节点 agent 不是 `kube-ovn-cni`、`ovs`、
`ovs-ovn` 或 `ovn-central` 容器，也不依赖这些容器中的 shell、OVN/OVS 工具或
`tcpdump`。本地无需安装 Bash、OVN/OVS、tar 或额外调用 kubectl 子进程；仅以
`kubectl ko` 形式调用插件时需要本地 `kubectl`。

## 安装

Kube-OVN 镜像和 CNI 安装脚本会将插件安装到已有的
`/usr/local/bin/kubectl-ko` 路径。集群外的工作站可从匹配 Kube-OVN 版本的
GitHub Release 下载 `kubectl-ko-<os>-<arch>.tar.gz`（Linux/macOS）或
`kubectl-ko-windows-<arch>.zip`，同时下载 `kubectl-ko-checksums.txt` 校验
SHA256，再将插件放入 `PATH`。工作站必须使用对应操作系统和架构的文件；节点
侧的 OVN/OVS 操作仍然只能在 Linux 节点执行。Linux、macOS、Windows 均提供
amd64 和 arm64 版本，不能把 Linux Pod 中的二进制复制到其他系统的工作站。

Windows 使用与架构匹配的 ZIP 文件，以 `Get-FileHash` 校验 SHA256，再用
`Expand-Archive` 解压。将 `kubectl-ko.exe` 放在与 `kubectl.exe` 一样可通过
`PATH` 发现的目录，或直接在 PowerShell 中执行：

```powershell
Get-FileHash .\kubectl-ko-windows-arm64.zip -Algorithm SHA256
Expand-Archive .\kubectl-ko-windows-arm64.zip .\kubectl-ko-windows-arm64
.\kubectl-ko-windows-arm64\kubectl-ko.exe version
.\kubectl-ko-windows-arm64\kubectl-ko.exe --context staging exec nbctl -- show
```

x64 Windows 应改用 amd64 文件。二进制 stdout 重定向（例如
`kubectl ko capture --pod web -- -w -`）
请使用 PowerShell 7.4 或更高版本，或 `cmd.exe`；旧版 PowerShell 可能破坏
pcap 字节流。Windows 工作站无需 WSL。

需要访问节点的命令依赖 `kubectl-ko-node-agent` DaemonSet。使用 Helm Chart
安装 Kube-OVN 后等待该 DaemonSet 就绪，再运行节点诊断。插件通过 Kubernetes
`pods/exec` 启动 agent helper，agent 使用自身挂载的节点 socket 和网络命名空间
完成操作，不会进入 Kube-OVN 组件容器。
集群安装脚本会在 agent DaemonSet 就绪后从其 `agent` 容器复制插件，不从 CNI
或 OVS/OVN 组件 Pod 复制。两个 Helm Chart 都部署独立 agent，并通过
`global.registry.imagePullSecrets` 拉取私有镜像；旧版 Chart 的 `full`、
`controlPlaneOnly` 和 `dataPlaneOnly` 模式都包含 agent。v2 Chart 使用全局
镜像及拉取策略，并按 `ovsOvn.ovnDirectory`、`logging.directory`、
`cni.configDirectory` 挂载宿主机数据。agent 只调度到 Linux 节点。

从源码构建可运行 `make build-kubectl-ko`，生成 `dist/images/kubectl-ko`
和仅适用于 Linux 的 `dist/images/kubectl-ko-node-agent`。此模块使用 Go
`replace`，发布版本宜使用 Release 二进制，不宜直接运行 `go install ...@version`。
Windows 本机构建可用 `go build -o kubectl-ko.exe ./cmd/kubectl-ko`；交叉构建
可用 `GOOS=windows GOARCH=amd64 make build-kubectl-ko`，ARM 工作站将架构
改为 `arm64`。

插件版本可在不访问集群的情况下查看：

```console
kubectl ko version
kubectl plugin list
```

`kubectl plugin list` 也可发现遮蔽新版插件的旧二进制副本。

## 命令结构与能力

Go CLI 的旧命令名和位置参数不再是别名，需按以下命令树迁移。

```text
kubectl ko
  exec
    (POD | TYPE/NAME) [-c CONTAINER] [flags] -- COMMAND [args...]
    -l SELECTOR -- COMMAND [args...]
    nbctl | sbctl | ic-nbctl | ic-sbctl -- [TOOL_ARGS...]
    vsctl | ofctl | dpctl | appctl --node NODE -- [TOOL_ARGS...]
  db
    health
    nb
      status | backup | kick SERVER_ID | restore
    sb
      status | backup | kick SERVER_ID
  trace --pod POD|--node NODE --dst-ip IP [OPTIONS]
  capture (--pod POD | --vm VM | --vmi VMI) -- [TCPDUMP_ARGS...]
  network inspect --pod POD [--output table|json]
  diagnose
    cluster | node NODE | subnet SUBNET
    connectivity --target PROTOCOL://IP:PORT [--target ...]
    environment
  logs [OPTIONS]
  restart
  perf run [OPTIONS] | recovery --yes
  acl decode COOKIE | listen --node NODE
  version | completion bash|zsh|fish|powershell
```

| 命令 | 作用与副作用 |
| --- | --- |
| `exec POD -- COMMAND`、`exec deploy/NAME -- COMMAND`、`exec svc/NAME -- COMMAND` | 按 Pod 名称或 workload selector 确定一个 Running Pod，通过 Kubernetes `pods/exec` 执行命令。支持 `po`、`deploy`、`svc`、`ds`、`sts`、`rs`、`rc` 和 `job` 等类型。Workload 选择具有确定顺序，不会一次执行到多个 Pod。 |
| `exec -l SELECTOR -- COMMAND` | 按 Kubernetes label selector 选择一个 Running Pod，不能与资源引用同时使用。 |
| `exec nbctl`、`exec sbctl`、`exec ic-nbctl`、`exec ic-sbctl` | 分别寻找 OVN 或 interconnection 数据库 leader，通过 agent 挂载的节点 socket 执行客户端命令；写入和多命令事务仍可用。 |
| `exec vsctl/ofctl/dpctl/appctl --node NODE` | 通过指定节点的 agent 执行 OVS 工具；远端命令可能改变运行状态。 |
| `db nb/sb status`、`db health` | 前者显示所选 leader 的 RAFT 集群和存储状态；后者检查所有 Running central 容器的 NB/SB 存储，不依赖健康 leader，存储异常会导致失败。 |
| `db nb/sb backup` | 转换并下载独立数据库，校验数据库名和 SHA256，写入 JSON 来源信息；不覆盖已有文件，清理远端临时备份。 |
| `db nb/sb kick SERVER_ID` | 移除过期 RAFT 成员。`--dry-run` 仅打印 leader Pod 和具体命令，无需 agent；实际执行经 leader 节点的 agent。 |
| `db nb restore` | 用明确指定的 bootstrap 节点上已有的 NB 数据库重建 central NB/SB 集群，不导入任意本地备份，也不支持仅恢复 SB。操作会停止 central、保留原始文件和 RAFT header、重建并验证存储，然后重启 OVS；详细条件见下文。 |
| `trace` | 解析 Pod/节点地址、MAC 和逻辑端口后执行 OVN、OVS trace。支持 IPv4/IPv6、ICMP/TCP/UDP、IPv4 ARP、hostNetwork、Underlay/U2O 和 VM 端口；`--engine ovn` 只执行 OVN trace。 |
| `capture` | 在 Pod 或 KubeVirt launcher 网络命名空间抓包；`--pod`、`--vm`、`--vmi` 三选一，`-w -` 将 pcap 流写到本地 stdout。 |
| `network inspect` | 显示 Pod 网络命名空间、接口索引、类型、MAC、MTU、状态、地址和统计信息。存在 veth 时显示主机侧对端；`macvlan`/`ipvlan` 显示主机父接口；`--output=json` 提供机器可读输出。 |
| `diagnose cluster`、`diagnose node NODE` | 检查集群配置、组件 rollout 和 leader。默认创建唯一的临时 NodePort Service，通过独立临时 Pod 在原 pinger 网络命名空间主动探测；node 模式限制到指定节点。 |
| `diagnose subnet SUBNET` | 创建隔离的临时 DaemonSet 和 NodePort Service，从子网 Pod 检查相互间 TCP/UDP、节点 ICMP 和 NodePort 连通性，无需可选的 CNI 节点 TCP/UDP listener。 |
| `diagnose connectivity` | 在现有 pinger 网络命名空间的独立临时 Pod 中检查指定 TCP/UDP IP endpoint，不创建 NodePort Service 或子网 DaemonSet。 |
| `diagnose environment` | 通过 Kubernetes API 发现所有 Linux 节点，使用各节点独立 agent 检查环境，包括没有 CNI Pod 的节点。 |
| `logs` | 并行收集组件文件、容器日志与 Linux 节点状态，限制单项大小并在 manifest 中记录部分失败。`netstat.log` 保存原始 `/proc/net/{tcp,tcp6,udp,udp6,unix}` 表，不解析进程 PID/名称。 |
| `restart` | 按依赖顺序重启并等待 central、OVS、controller、CNI、pinger 和 monitor。 |
| `perf run` | 创建隔离的探测 Pod/Service，测量 Pod、主机、Service 和组播性能；临时修改 OVN LB 与组播成员并清理所属变更，不删除 central leader。 |
| `perf recovery --yes` | 依次删除 NB、SB 和 northd leader Pod 并测量恢复，不运行流量基准测试。 |
| `acl decode COOKIE`、`acl listen --node NODE` | 解码 sample cookie，或从指定节点流式接收并解码采样 cookie，直到取消为止。 |
| `version`、`help`、`completion` | 无需访问集群即可查看本地版本、帮助和 shell 补全。 |

## 配置与参数边界

标准 Kubernetes 连接参数可放在子命令前后，但须位于远端参数分隔符 `--`
之前。kubeconfig 加载器支持 `--kubeconfig`、`KUBECONFIG`、context、TLS、
认证插件和 impersonation。Workload `exec` 的命名空间由 `-n/--namespace`、
kubeconfig 命名空间、`default` 依次确定；`TYPE/NAME` 中的斜杠分隔资源类型
和名称，不是命名空间。`capture`、`trace` 等接收 Pod、VM 或 VMI 名称的命令
可使用 `namespace/name` 覆盖命名空间。Kube-OVN 部署命名空间另由
`--kube-ovn-namespace`、`KUBE_OVN_NS`、`kube-system` 依次确定。

| 范围 | 参数与默认值 |
| --- | --- |
| 全局 | `--timeout=0` 限制整个调用，零值允许长时间流；`--discovery-timeout=10s` 限制目标选择。Kubernetes `--request-timeout` 不会截断已建立的 exec 流。 |
| Kubernetes exec | 接受 `POD` 或 `TYPE/NAME`、`-c/--container`、`-l/--selector`、`-i/--stdin`、`-t/--tty`、`-q/--quiet` 和 `--pod-running-timeout=1m`。命令必须位于 `--` 后。 |
| 节点工具与抓包 | OVS 工具需要 `--node`；抓包需要且只能选择 `--pod`、`--vm` 或 `--vmi`。远端参数必须位于 `--` 后。 |
| 网络检查 | `network inspect` 需要 `--pod`；默认 `--output=table`，自动化可用 `--output=json`。 |
| Trace | `--pod` 与 `--node` 二选一，必须指定 `--dst-ip`；默认 `--protocol=icmp`、`--engine=all`，可选 `--dst-mac`。TCP/UDP 需要 `--dst-port=1..65535`；IPv4 ARP 使用 `--arp-op=request` 或 `--arp-op=reply`。 |
| 数据库备份与恢复 | 备份可指定 `--output FILE`，否则生成唯一的数据库专属文件名。恢复必须指定 `--source-node NODE`，并指定 `--yes` 或 `--dry-run`。 |
| 诊断 | cluster/node/subnet 可用 `--read-only` 跳过主动探测和临时资源。配置/探测模式可用 `--skip-kube-proxy`，默认取自 `WITHOUT_KUBE_PROXY=true`。subnet 的 `--tcp-port`、`--udp-port` 依次取自 `TCP_CONN_CHECK_PORT`、`UDP_CONN_CHECK_PORT`，再默认到 8100、8101；显式参数优先。connectivity 至少需要一个 `--target tcp://IP:PORT` 或 `udp://IP:PORT`，IPv6 地址须加方括号。 |
| 日志 | `--component=all`，可选 `all`、`kube-ovn`、`ovn`、`ovs`、`linux`；`--output-dir=kubectl-ko-log`、`--concurrency=4`、`--item-timeout=30s`、单项 `--max-bytes=268435456`，可选 `--strict`。 |
| 性能 | `perf run` 默认 `--image=docker.io/kubeovn/test:v1.13.0`、`--duration=5s`、`--bandwidth=1G`。时长按单项测量，须为 1 秒至 5 分钟的整数秒；私有网络可指定内部镜像。中断 leader 是独立的 `perf recovery --yes` 操作。 |

临时 NodePort 探测会请求 `PreferDualStack`，只检查 Service 实际分配的地址族。
单栈集群只用其现有地址族，双栈集群检查两种地址族；若节点缺少已分配地址族的
地址，命令会报告错误。

```console
kubectl ko exec -n app pod/web -- date
kubectl ko exec nbctl --context staging -- --format=json show
kubectl ko exec nbctl -- -- ls-add example -- lsp-add example example-port
kubectl ko trace --pod app/web --dst-ip 10.0.0.8 --protocol tcp --dst-port 443
kubectl ko trace --node worker-a --dst-ip 2001:db8::8 --engine ovn
kubectl ko network inspect --pod app/web --output json
kubectl ko diagnose subnet ovn-default --tcp-port 8100 --udp-port 8101
kubectl ko diagnose connectivity --target tcp://10.0.0.8:8100 --target 'udp://[2001:db8::8]:8101'
kubectl ko db nb backup --output northbound.backup
kubectl ko logs --component ovn --output-dir ./support --strict
kubectl ko perf run --image registry.example/test:v1.13.0 --duration 2s
```

## Workload exec

`exec` 的第一个参数可以是 Pod 名称或 Kubernetes workload 引用。workload
引用通过 selector 选择一个 Running Pod，不会在一次调用中执行到多个 Pod。
`-l/--selector` 是另一种选择方式，不能和资源引用同时使用。
裸 Pod 名称使用 `-n/--namespace` 指定的命名空间；未指定时使用 kubeconfig
命名空间，再退回 `default`。
多个就绪 leader 会明确失败，而不会随意选择一个。

支持的 Kubernetes 风格参数包括 `-c/--container`、`-i/--stdin`、
`-t/--tty`、`-q/--quiet`、`--pod-running-timeout` 和 `-n/--namespace`。
命令与远端参数之间必须使用 `--` 分隔。插件只移除一次该分隔符，之后的
`--help`、`--timeout`、`-n`、`-c` 以及引号都原样传给远端工具：

```console
kubectl ko exec deploy/web -- date
kubectl ko exec -n app pod/web -- date
kubectl ko exec svc/web -c app -- sh -c 'echo ready'
kubectl ko exec -n app -l app=web -- curl http://localhost:8080/healthz
kubectl ko exec nbctl -- --format=json show
kubectl ko exec vsctl --node worker-a -- --timeout=5 show
```

`exec nbctl --help` 显示插件本地帮助，`exec nbctl -- --help` 才会显示远端
`ovn-nbctl` 帮助。省略分隔符时插件会拒绝请求，不猜测远端参数边界。
分隔符只移除一次；其后的另一个 `--`、空格、引号和看似本地选项的参数都原样
属于远端命令。失败保留非零退出码，二进制流不会经过 TTY 转换。

## Pod、VM 和 VMI 抓包

`capture` 必须且只能指定一个目标：`--pod`、`--vm` 或 `--vmi`。支持的抓包
参数包括 `-D`（列出接口）、`-i`、`-c`、`-s`、`-nn` 和 `-w -`。使用
`-w -` 时 pcap 写入本地 stdout，诊断信息写入 stderr：

```console
kubectl ko capture --namespace app --pod web -- -w - > capture.pcap
kubectl ko capture --vm app/database -- -w - > vm.pcap
kubectl ko capture --namespace app --vmi database -- -c 10
```

节点 agent 在目标网络命名空间中直接使用 Linux `AF_PACKET` socket 和
`setns(2)`，不会启动 `tcpdump`、`nsenter` 或 shell。当前只有 Ethernet 接口
支持 pcap 输出；不支持的过滤表达式会在打开远端请求前失败。

### KubeVirt 迁移期间的选择规则

- `--vm` 会校验 VMI 由指定 VM 控制；`--vmi` 也支持没有 VM 控制器的独立 VMI。
- 插件依据 VMI controller UID、节点和运行状态选择当前 launcher Pod。
- 迁移进行中一直使用源 launcher；迁移成功后才选择目标 launcher。失败的迁移仍使用源 launcher。
- launcher 必须处于 Running 且没有删除时间戳。缺失或存在多个候选 launcher，或请求开始前 VMI/Pod 状态发生变化时，命令会明确失败；状态稳定后重试，或直接使用 `--pod` 指定 launcher。
- 已建立的抓包会一直留在开始时选定的网络命名空间，不会随着后续迁移切换。

调用者需要读取 VMI、列出 launcher Pod；使用 `--vm` 时还需读取 VM。
`network inspect` 会先从 OVSDB 解析 Pod 网络命名空间；若无 OVS 接口，会以
Pod UID 从宿主机进程 cgroup 查找。它从 Pod 和宿主机接口读取链路详情与
RX/TX 统计；主机网络 Pod 使用宿主机命名空间。文本和 JSON 均保留 64 位
计数器，包括零值和驱动特有字段；缺少 `stats64` 时可读取旧版 `stats`。

## 诊断、日志与数据库恢复

connectivity 的 UDP 探测会发送 `health check` 数据报，并等待响应。目标必须是
能回应的健康检查或 echo 服务；它不是 DNS 查询，也不是通用 UDP 端口扫描。
subnet 探测使用自身提供的匹配 listener。

cluster/node/subnet 默认检查内部连通性，不要求访问公共 Internet。需要外部
ICMP 探测时可重复传入 `--external-address IP`，例如：

```console
kubectl ko diagnose cluster --external-address 1.1.1.1 --external-address 2606:4700:4700::1111
```

明确指定的地址不可达，或探测 Pod 缺少匹配的 IP 地址族，都会使命令失败。
探测资源采用唯一名称和运行标识，清理时核对保存的 UID；清理失败会报告剩余
对象，不会掩盖原始错误。cluster/node/connectivity 会使用与原 pinger 相同的
镜像、service account、工具挂载和网络命名空间，但在独立的短期 Pod 中运行，
并在执行前复查 pinger UID 与 Ready 状态。探测 Pod 需要 host PID 和
`SYS_ADMIN` 进入该网络命名空间；节点 agent 不挂载 service-account token。
subnet 探测 DaemonSet 若未就绪，会在清理前限时收集所属最多八个 Pod 的状态
和部分容器日志，保留原始就绪错误。临时 Pod 也挂载私有日志目录。

`logs` 保留 `kubectl-ko-log/<node>/{kube-ovn,ovn,openvswitch,linux}` 目录布局；
同节点 central 文件存放在 `ovn/central-<pod>` 下。`manifest.json` 记录每项
结果与失败；默认允许部分失败，`--strict` 才让任何失败项导致命令失败。
连续按组件收集时，已收集文件会保留。归档不会写出目标根目录；Unix 上解压
文件使用私有权限。Windows 请使用受用户 ACL 保护的目标目录，Unix 权限位
不能设置 Windows ACL。数据库备份目标必须支持硬链接（例如 NTFS），以便
原子发布且不覆盖现有文件。

Linux 状态与环境检查通过 Kubernetes API 独立发现非终止中的 Linux 节点，
不依赖 CNI Pod。agent 缺失、未就绪或重复均作为发现失败；其他节点仍继续
收集或检查。XFRM 状态使用 `nokeys` 收集。IPsec 日志收集按 CNI Pod UID
定位运行中的 charon 进程，通过 agent 的 strongSwan 客户端读取控制 socket；
收集当前 `ipsec.conf`、证书元数据和状态，不在 CNI 容器内执行工具或导出密钥。
来源 Pod 缺失/歧义、IPsec 未开启或 daemon 不可用会记为该项失败，其余 Linux
状态仍可收集。数据库与网络诊断产物应按敏感本地文件处理。

`db nb restore` 是从指定节点上已有的 NB 数据库重建集群，不能导入任意本地
备份，也不支持只恢复 SB。必须显式指定 `--source-node`，该节点须是
`NODE_IPS` 的第一个成员，即镜像启动脚本的 bootstrap 节点。仅支持使用
字面量 `NODE_IPS` 成员列表、central hostPath 可写的标准 central Deployment。
若 OVS 未挂载数据库目录，命令会用临时 hostNetwork helper 挂载同一 hostPath；
若已有 OVS 数据库挂载，其 hostPath 必须与 central 一致。helper 使用 central
镜像和 security context，按 UID 清理。

先运行 `--dry-run`，确认条件后再用 `--yes` 执行。helper 和数据库文件检查会在
停止 central 前完成；所有 central Pod 停止后才修改文件。原文件和 RAFT header
保留在每个成员节点的独立目录，本地私有 JSON 记录最近恢复阶段。错误会停止
流程，并报告记录路径、远端目录和原副本数；命令不会猜测部分完成的恢复是否可
自动回滚。保留这些文件供人工决定后续恢复或回退。远端备份位于
`/etc/ovn/.kubectl-ko-recovery-<id>`，避免 central 启动时的文件权限 glob
破坏目录遍历权限。

`perf run` 在 Service 测量前最多等待 30 秒，直到临时 OVN LB 同步至所有
chassis，确保 qperf 动态数据端口可用；同步失败时停止测量并清理所属 LB。
`restart`、原始 OVN/OVS 命令、数据库恢复以及显式的 `perf recovery --yes`
都可能改变运行中的集群状态。

## 节点 agent 与权限

每个节点操作都通过 Kubernetes `pods/exec` 在独立 agent helper 中执行。请求
使用版本化 gRPC 流，多个并发请求使用独立流，不会重启 agent。agent 只挂载
执行所需的节点 socket、网络命名空间和日志路径，不挂载 service-account token，
也不会在 `kube-ovn-cni`、`ovs-ovn` 或 `ovn-central` 容器中执行命令。
短期探测 Pod 可通过普通 Kubernetes 流执行自身进程。workload exec 优先使用
WebSocket，仅在受支持的握手失败情形回退 SPDY。节点 helper 请求完成后会关闭
stdin 并等待外层 exec 进程退出；远端失败退出码会传播，不会自动重放写入命令。
取消 agent 请求时会终止其 Linux 进程组及子进程，并返回退出码 130；主动
脱离到其他 session 的进程不在该进程组内。无效参数在创建客户端前报错。

使用插件的账号需要读取目标资源；节点操作还需要访问 agent 的 `pods/exec`。
数据库恢复、组件重启和性能恢复操作需要额外的 workload 修改权限。请按组织的
最小权限策略授予这些权限。
资源发现需要 get/list，agent 调用需要 `pods/exec`，日志需要 pods/log，
探测需要 create/delete，rollout 和恢复需要 workload patch/scale。
`pods/exec` 权限也能执行写入命令，不能视为数据库只读权限。
用户端和 Kube-OVN 版本应匹配；远端镜像中可用的工具决定实际能力。

## 旧命令迁移

Go CLI 保留诊断能力，但旧 Bash 命令名称和位置参数不是别名。CI 和支持信息
收集脚本也要迁移到 `logs --component COMPONENT --output-dir DIR`：

| 旧形式 | 新形式 |
| --- | --- |
| `nbctl ARGS`、`sbctl ARGS` | `exec nbctl -- ARGS`、`exec sbctl -- ARGS` |
| `icnbctl ARGS`、`icsbctl ARGS` | `exec ic-nbctl -- ARGS`、`exec ic-sbctl -- ARGS` |
| `vsctl/ofctl/dpctl/appctl NODE ARGS` | `exec TOOL --node NODE -- ARGS` |
| `nb/sb status`、`nb/sb backup`、`nb/sb kick ID` | `db nb/sb status`、`db nb/sb backup`、`db nb/sb kick ID` |
| `nb dbstatus`、`sb dbstatus` | `db health` |
| `nb restore` | 先运行 `db nb restore --source-node NODE --dry-run`，确认后使用 `--yes`。 |
| `trace POD IP [MAC] PROTOCOL [PORT/OP]` | `trace --pod POD --dst-ip IP [--dst-mac MAC] --protocol PROTOCOL [--dst-port PORT/--arp-op OP]` |
| `trace node//NODE ...` | `trace --node NODE ...` |
| `ovn-trace ...` | `trace --engine ovn ...` |
| `tcpdump POD ARGS` | `capture --pod POD -- ARGS` |
| `diagnose [all]` | `diagnose cluster` |
| `diagnose node NODE`、`diagnose subnet SUBNET` | 命令形式不变，现为有独立帮助及参数校验的子命令。 |
| `diagnose IPPorts tcp-IP-PORT,udp-IP-PORT` | `diagnose connectivity --target tcp://IP:PORT --target udp://IP:PORT` |
| `env-check` | `diagnose environment` |
| `log COMPONENT --output DIR` | `logs --component COMPONENT --output-dir DIR` |
| `reload` | `restart` |
| `perf IMAGE --duration 5` | `perf run --image IMAGE --duration 5s` |
| 隐式删除 leader 或 `perf --include-disruption` | 单独运行 `perf recovery --yes`。 |
| `acl-sample decode/listen ...` | `acl decode/listen ...` |

生产镜像不再依赖 `tcpdump`、`ncat`/`netcat` 和 `net-tools`。使用
`kubectl ko capture` 抓包，使用 `kubectl ko diagnose connectivity` 检查
TCP/UDP endpoint，使用 `network inspect`、`trace`、`logs` 和 `perf` 获取结构化
诊断信息。需要交互式调试工具时使用 DEBUG 镜像；DEBUG 镜像仍可提供 `gdb`、
`valgrind` 和抓包工具。

上面的替代关系适用于生产镜像；需要完整的工具边界和权限说明时，以当前版本
的 `kubectl ko` 命令帮助和 Helm values 为准。
旧 Bash 可执行文件不再随镜像发布或安装；旧语法仅在旧版本 E2E fixture 中保留。
