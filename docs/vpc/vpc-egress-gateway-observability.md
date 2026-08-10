# VPC Egress Gateway 可观测性

VPC Egress Gateway 可以在每个网关 Pod 中运行一个原生可观测性 sidecar。该 sidecar 可以暴露内部和外部网卡计数器、低基数 conntrack NAT 指标，并将版本化 NAT 流日志写入容器标准输出。这三项功能默认均禁用，不影响网关数据平面就绪状态。

## 使用要求和升级说明

- observer 使用 [restartable init container](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/){: target="_blank" }，因此需要 Kubernetes 1.29 或更高版本，并启用 `SidecarContainers` 特性。控制器会对一个零副本 Deployment 执行服务端 dry-run，并验证 API Server 是否保留 restartable init 策略。如果版本过低或未启用该特性，控制器不会注入 observer，并设置 `ObservabilityConfigured=False`；网关数据平面仍会正常协调。控制器会重试短暂的能力探测错误；无法验证能力时，已存在的 observer 保持最后一个已知良好配置。
- 创建使用 `spec.observability` 的资源前，需要显式升级 `vpc-egress-gateways.kubeovn.io` CRD。Helm 不会自动升级已安装的 CRD。请使用常规 CRD 升级流程，应用与 Kube-OVN 版本匹配的 CRD。
- conntrack 采集需要网关 Pod 网络命名空间中的 `NET_ADMIN`。官方 observer binary 仅带有 `CAP_NET_ADMIN` file capability，生成的容器 security context 仅允许 `NET_ADMIN` 进入 capability bounding set。`allowPrivilegeEscalation` 已启用，使该可信 file capability 在非 root launcher 执行 `exec` 后仍然生效；observer 仍以 UID 和 GID 65534 运行，丢弃其他所有 capability，并使用只读根文件系统。
- Prometheus Operator 是可选依赖。缺少 ServiceMonitor CRD 时，网关仍可正常工作。

## 启用可观测性

以下示例启用两个指标采集器和 JSON 流日志：

```yaml
apiVersion: kubeovn.io/v1
kind: VpcEgressGateway
metadata:
  name: gateway1
  namespace: default
spec:
  vpc: ovn-cluster
  replicas: 2
  externalSubnet: macvlan1
  policies:
    - snat: true
      subnets:
        - ovn-default
  observability:
    resources:
      requests:
        cpu: 20m
        memory: 64Mi
      limits:
        cpu: 200m
        memory: 256Mi
    interfaceMetrics:
      enabled: true
    conntrack:
      metrics:
        enabled: true
      log:
        enabled: true
        events: [start, end]
        rateLimit:
          recordsPerSecond: 100
          burst: 1000
        filters:
          include: []
          exclude: []
    serviceMonitor:
      labels:
        monitoring: platform
      annotations: {}
```

`resources` 为空或省略时，observer 的 request 为 `20m` CPU 和 `64Mi` 内存，limit 为 `200m` CPU 和 `256Mi` 内存。
interface-only 模式会持续测试，以确保稳态常驻内存不超过 `20MiB`；更大的默认 request 为 conntrack cache 和日志队列增长保留了空间。

控制器将运行时配置存储在每个网关的 ConfigMap 中。采集器开关、流日志事件、filter 和 rate limit 可在不替换网关 Pod 的情况下热加载。以下更改会更新 Deployment 并替换 Pod：

- 首次启用可观测性。
- 禁用所有可观测性功能。
- 更改 `observability.resources`。
- 更改网关工作负载镜像。

如果能力探测、ConfigMap 或 Service 更新短暂失败，控制器会报告可观测性 condition，并保留现有 observer 容器、volume 和辅助资源。数据平面协调会继续，不会因为可观测性错误替换使用最后一个已知良好配置的网关 Pod。

如果显式选择的旧工作负载镜像不包含 `/kube-ovn/vpc-egress-gateway-observer`，launcher 会改为执行 `sleep infinity`，因此缺少 binary 不会阻塞数据平面。包含 observer 的自定义镜像必须保留其 `CAP_NET_ADMIN` file capability；否则网卡指标仍可用，但 conntrack 指标和流日志会报告采集器错误。

## 指标

observer 在 TCP 端口 `10666` 上提供 `/metrics` 和 `/healthz`。observer 使用私有 Prometheus registry，不暴露 `go_*`、`process_*` 或 `promhttp_*` 指标。每个指标都包含 `namespace`、`name`、`pod` 和 `node` 身份标签。

对于每个网关，liveness probe 会在容器内执行 observer binary，并通过 loopback 检查 `/healthz`。这使 observer 健康状态不受节点到 Pod 的可达性影响，也使旧工作负载镜像在缺少 observer binary 并使用 `sleep infinity` 回退时能够通过探测。

### 网卡指标

每次 scrape 都会从 `/proc/net/dev` 读取网卡指标。observer 在首次成功 scrape 时通过 Pod `network-status` annotation 解析主网卡和外部 Multus 网卡，并在进程生命周期内缓存这些名称。

| 指标 | 附加标签 | 描述 |
| :--- | :--- | :--- |
| `kube_ovn_vpc_egress_gateway_interface_rx_bytes_total` | `interface`、`type` | 接收字节数。 |
| `kube_ovn_vpc_egress_gateway_interface_tx_bytes_total` | `interface`、`type` | 发送字节数。 |
| `kube_ovn_vpc_egress_gateway_interface_rx_packets_total` | `interface`、`type` | 接收报文数。 |
| `kube_ovn_vpc_egress_gateway_interface_tx_packets_total` | `interface`、`type` | 发送报文数。 |
| `kube_ovn_vpc_egress_gateway_interface_drops_total` | `interface`、`type`、`direction` | 丢弃报文数。 |
| `kube_ovn_vpc_egress_gateway_interface_errors_total` | `interface`、`type`、`direction` | 报文错误数。 |

`type` 标签为 `internal` 或 `external`，`direction` 为 `rx` 或 `tx`。

### Conntrack 指标

Conntrack 指标不使用 IP 地址或端口作为标签，仅对流量进行汇总：

| 指标 | 附加标签 | 描述 |
| :--- | :--- | :--- |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_flows_active` | `address_family`、`protocol`、`nat_type` | 当前 NAT 流数，从 conntrack table dump 初始化并通过事件维护。 |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_flows_started_total` | `address_family`、`protocol`、`nat_type` | observer 订阅后观测到的 NAT 流启动总数。 |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_flows_ended_total` | `address_family`、`protocol`、`nat_type` | 观测到的 NAT 流结束事件总数。 |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_packets_total` | `address_family`、`protocol`、`nat_type`、`direction` | conntrack accounting 可用时观测到的报文数。 |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_bytes_total` | `address_family`、`protocol`、`nat_type`、`direction` | conntrack accounting 可用时观测到的字节数。 |

`address_family` 为 `ipv4` 或 `ipv6`。已知 `protocol` 值为 `tcp`、`udp`、`sctp`、`icmp` 和 `icmpv6`；其他协议号均汇总为 `other`。`nat_type` 为 `snat`、`dnat` 或 `snat_dnat`，`direction` 为 `original` 或 `reply`。

运行指标使用 `kube_ovn_vpc_egress_gateway_observability_*` 前缀。它们报告采集器可用性、配置重新加载结果、conntrack 事件和错误、cache 条目／容量／驱逐、已输出和已丢弃日志记录，以及 conntrack accounting 可用性。一个采集器失败不会导致 `/metrics` 失败，也不会隐藏另一个采集器的数据。

## ServiceMonitor 发现

启用任一指标采集器时，控制器会为每个网关创建一个设置了 `publishNotReadyAddresses: true` 的 headless Service，其数字 `targetPort` 为 `10666`。控制器还会在网关所在命名空间创建 ServiceMonitor。`observability.serviceMonitor` 中的用户 label 和 annotation 会合并到 ServiceMonitor 元数据，但不能覆盖控制器必需的 selector label。

如果 ServiceMonitor CRD 不存在，控制器会设置 `ServiceMonitorReady=False` 并定期重试。CRD 可用后，控制器会自动创建 ServiceMonitor。该 condition 与现有网关 `Ready` condition 相互独立。

## JSON 流日志

流日志以 JSON Lines 形式仅写入 `observability` 容器标准输出，诊断信息写入标准错误。使用以下命令读取记录：

```bash
kubectl logs -n default <gateway-pod> -c observability
```

`v1` schema 输出 `start` 和 `end` 生命周期记录，不记录原始 conntrack update 事件。记录示例如下：

```json
{"schemaVersion":"v1","timestamp":"2026-08-05T03:40:00Z","event":"end","conntrackID":2471802592,"zone":0,"namespace":"default","name":"gateway1","pod":"gateway1-7c9b8f8db7-r9x8m","node":"worker-1","addressFamily":"ipv4","protocol":"tcp","protocolNumber":6,"natType":["snat"],"original":{"sourceIP":"10.16.0.25","sourcePort":42136,"destinationIP":"203.0.113.10","destinationPort":443},"translated":{"sourceIP":"172.17.0.11","sourcePort":42136,"destinationIP":"203.0.113.10","destinationPort":443},"counters":{"originalPackets":8,"originalBytes":624,"replyPackets":7,"replyBytes":591}}
```

对于汇总为 `other` 的协议，`protocolNumber` 保留原始 IP 协议号。`natType` 是稳定排序的数组，可同时包含 `dnat` 和 `snat`。conntrack accounting 不可用时省略 `counters` 对象；observer 从不更改 `nf_conntrack_acct`。

observer 在 dump 现有 conntrack table 前订阅 conntrack 事件。现有 NAT 流会初始化 active-flow 指标和 cache，但不会生成历史 `start` 日志。cache 限制为 65,536 个条目。netlink 事件 channel 和异步日志队列均限制为 4,096 个条目。容器日志 consumer 阻塞或日志队列已满时，系统会丢弃日志记录，且不会阻塞 conntrack 采集。

默认情况下，系统记录所有 NAT 流和两种生命周期事件，每个 Pod 限制为每秒 100 条记录，最大突发记录数为 1,000。这些记录和指标是 best-effort 运行数据，不适用于计费精度的计量。

## 流日志 Filter

每条 include 或 exclude 规则可以匹配地址族、协议、NAT 类型以及原始或转换后 tuple 的字段。同一字段内的值按 OR 组合，同一规则内已配置的字段按 AND 组合，同一列表内的规则按 OR 组合。exclude 规则优先于 include 规则。空 include 列表匹配所有 NAT 流。

端口使用包含边界的结构化范围。以下配置会记录从 `10.16.0.0/16` 到目标端口 80 至 443 的 TCP SNAT 流，但排除转换后目标地址位于 `192.0.2.0/24` 的流：

```yaml
spec:
  observability:
    conntrack:
      log:
        enabled: true
        filters:
          include:
            - protocols: [tcp]
              natTypes: [snat]
              original:
                sourceCIDRs: [10.16.0.0/16]
                destinationPorts:
                  - start: 80
                    end: 443
          exclude:
            - translated:
                destinationCIDRs: [192.0.2.0/24]
```
