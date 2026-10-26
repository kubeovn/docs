# kubectl-ko 插件

`kubectl-ko` 是用于操作和诊断 Kube-OVN 的 Go 编写的 kubectl 插件。它通过
Kubernetes API 获取资源，并将需要节点权限的操作转发给独立的
`kubectl-ko-node-agent` DaemonSet。节点 agent 不是 `kube-ovn-cni`、`ovs`、
`ovs-ovn` 或 `ovn-central` 容器，也不依赖这些容器中的 shell、OVN/OVS 工具或
`tcpdump`。

## 安装

Kube-OVN 镜像和 CNI 安装脚本会将插件安装到已有的
`/usr/local/bin/kubectl-ko` 路径。集群外的工作站可从匹配 Kube-OVN 版本的
GitHub Release 下载 `kubectl-ko-<os>-<arch>.tar.gz`（Linux/macOS）或
`kubectl-ko-windows-<arch>.zip`，同时下载 `kubectl-ko-checksums.txt` 校验
SHA256，再将插件放入 `PATH`。工作站必须使用对应操作系统和架构的文件；节点
侧的 OVN/OVS 操作仍然只能在 Linux 节点执行。

需要访问节点的命令依赖 `kubectl-ko-node-agent` DaemonSet。使用 Helm Chart
安装 Kube-OVN 后等待该 DaemonSet 就绪，再运行节点诊断。插件通过 Kubernetes
`pods/exec` 启动 agent helper，agent 使用自身挂载的节点 socket 和网络命名空间
完成操作，不会进入 Kube-OVN 组件容器。

插件版本可在不访问集群的情况下查看：

```console
kubectl ko version
kubectl plugin list
```

## 命令结构

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

| 命令 | 作用 |
| --- | --- |
| `exec POD -- COMMAND`、`exec deploy/NAME -- COMMAND`、`exec svc/NAME -- COMMAND` | 使用 Kubernetes selector 找到一个 Running Pod，再通过 `pods/exec` 执行命令。支持 `po`、`deploy`、`svc`、`ds`、`sts`、`rs`、`rc` 和 `job` 别名。 |
| `exec -l SELECTOR -- COMMAND` | 通过 label selector 选择一个 Running Pod，不能和资源引用同时使用。 |
| `exec nbctl`、`exec sbctl`、`exec ic-nbctl`、`exec ic-sbctl` | 通过 agent 找到对应 OVN 数据库或 interconnection leader，在节点 socket 上执行客户端命令。 |
| `exec vsctl/ofctl/dpctl/appctl --node NODE` | 通过 agent 在指定节点执行 OVS 工具。写入类命令可能改变运行中的状态。 |
| `db health`、`db nb/sb status`、`db nb/sb backup`、`db nb kick`、`db nb restore` | 检查、备份、恢复或维护 OVN Northbound/Southbound 数据库。 |
| `trace` | 解析 Pod 或节点地址、MAC 和逻辑端口，执行 OVN/OVS trace；支持 IPv4、IPv6、ARP、TCP、UDP、Underlay、U2O 和 VM 端口。 |
| `capture` | 在 Pod 或 KubeVirt launcher 的网络命名空间抓包，支持 `--pod`、`--vm` 或 `--vmi` 三选一。 |
| `network inspect` | 查看 Pod 网络命名空间中的接口、地址、MTU、状态、统计信息以及主机侧 veth 对端。 |
| `diagnose` | 检查集群、节点、子网、指定 TCP/UDP endpoint 或 Linux 节点环境。 |
| `logs`、`restart`、`perf`、`acl` | 收集组件和节点日志、按依赖顺序重启组件、运行性能/恢复测试、解码或监听 ACL sampling。 |

## Workload exec

`exec` 的第一个参数可以是 Pod 名称或 Kubernetes workload 引用。workload
引用通过 selector 选择一个 Running Pod，不会在一次调用中执行到多个 Pod。
`-l/--selector` 是另一种选择方式，不能和资源引用同时使用。

支持的 Kubernetes 风格参数包括 `-c/--container`、`-i/--stdin`、
`-t/--tty`、`-q/--quiet`、`--pod-running-timeout` 和 `-n/--namespace`。
命令与远端参数之间必须使用 `--` 分隔。插件只移除一次该分隔符，之后的
`--help`、`--timeout`、`-n`、`-c` 以及引号都原样传给远端工具：

```console
kubectl ko exec deploy/web -- date
kubectl ko exec svc/web -c app -- sh -c 'echo ready'
kubectl ko exec -n app -l app=web -- curl http://localhost:8080/healthz
kubectl ko exec nbctl -- --format=json show
kubectl ko exec vsctl --node worker-a -- --timeout=5 show
```

`exec nbctl --help` 显示插件本地帮助，`exec nbctl -- --help` 才会显示远端
`ovn-nbctl` 帮助。省略分隔符时插件会拒绝请求，不猜测远端参数边界。

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

## 节点 agent 与权限

每个节点操作都通过 Kubernetes `pods/exec` 在独立 agent helper 中执行。请求
使用版本化 gRPC 流，多个并发请求使用独立流，不会重启 agent。agent 只挂载
执行所需的节点 socket、网络命名空间和日志路径，不挂载 service-account token，
也不会在 `kube-ovn-cni`、`ovs-ovn` 或 `ovn-central` 容器中执行命令。

使用插件的账号需要读取目标资源；节点操作还需要访问 agent 的 `pods/exec`。
数据库恢复、组件重启和性能恢复操作需要额外的 workload 修改权限。请按组织的
最小权限策略授予这些权限。

## 旧命令迁移

Go CLI 保留诊断能力，但旧 Bash 命令名称和位置参数不是别名：

| 旧形式 | 新形式 |
| --- | --- |
| `kubectl ko nbctl ARGS` | `kubectl ko exec nbctl -- ARGS` |
| `kubectl ko sbctl ARGS` | `kubectl ko exec sbctl -- ARGS` |
| `kubectl ko icnbctl ARGS` | `kubectl ko exec ic-nbctl -- ARGS` |
| `kubectl ko icsbctl ARGS` | `kubectl ko exec ic-sbctl -- ARGS` |
| `kubectl ko vsctl NODE ARGS` | `kubectl ko exec vsctl --node NODE -- ARGS` |
| `kubectl ko ofctl/dpctl/appctl NODE ARGS` | `kubectl ko exec TOOL --node NODE -- ARGS` |
| `kubectl ko tcpdump POD ARGS` | `kubectl ko capture --pod POD -- ARGS` |
| `kubectl ko trace ...` | `kubectl ko trace --pod POD or --node NODE --dst-ip IP ...` |
| `kubectl ko reload` | `kubectl ko restart` |
| `kubectl ko log ...` | `kubectl ko logs ...` |

生产镜像不再依赖 `tcpdump`、`ncat`/`netcat` 和 `net-tools`。使用
`kubectl ko capture` 抓包，使用 `kubectl ko diagnose connectivity` 检查
TCP/UDP endpoint，使用 `network inspect`、`trace`、`logs` 和 `perf` 获取结构化
诊断信息。需要交互式调试工具时使用 DEBUG 镜像；DEBUG 镜像仍可提供 `gdb`、
`valgrind` 和抓包工具。

上面的替代关系适用于生产镜像；需要完整的工具边界和权限说明时，以当前版本
的 `kubectl ko` 命令帮助和 Helm values 为准。
