# 托管 OVN Central

托管控制平面（HCP）模式会为工作负载集群运行独立的、由 PVC 持久化的
`ovn-central` StatefulSet。这样 OVN northbound 和 southbound 数据库可以位于
工作负载集群之外，并通过 HCP 配置暴露访问地址。

两种 Chart 布局都支持 HCP 模式：

- classic chart：`ovn-central.hcp.*`
- v2 chart：`central.hcp.*`

## 配置

安装 Chart 前先创建 HCP namespace。Helm release 可以继续安装在 Kube-OVN 的
常规 namespace 中，HCP 资源会渲染到 `hcp.namespace` 指定的 namespace。

```bash
kubectl create namespace hcp
```

下面是 classic chart 示例。启用 HCP 时必须设置 `nbAddress` 和 `sbAddress`。
每个地址都要包含连接协议和端口，并且必须能被工作负载集群访问。

```yaml
namespace: kube-system

ovn-central:
  hcp:
    enabled: true
    namespace: hcp
    replicas: 3
    nbAddress: tcp:ovn-nb.example.com:6641
    sbAddress: tcp:ovn-sb.example.com:6642
    service:
      type: NodePort
      nbNodePort: 30641
      sbNodePort: 30642
    storage:
      size: 5Gi
      storageClassName: ""
```

v2 chart 在 `central.hcp` 下使用相同的配置：

```yaml
central:
  hcp:
    enabled: true
    namespace: hcp
    replicas: 3
    nbAddress: tcp:ovn-nb.example.com:6641
    sbAddress: tcp:ovn-sb.example.com:6642
    service:
      type: NodePort
      nbNodePort: 30641
      sbNodePort: 30642
    storage:
      size: 5Gi
      storageClassName: ""
```

namespace 创建后，使用 values 文件安装 Chart：

```bash
helm upgrade --install kube-ovn ./charts/kube-ovn -n kube-system -f hcp-values.yaml
```

安装 v2 chart 时，将 `./charts/kube-ovn` 替换为 v2 chart 路径。

## 资源和调度

启用 HCP 后，Chart 会在 `hcp.namespace` 中创建以下资源：

- 一个 `ovn-central` StatefulSet，副本数由 `hcp.replicas` 设置，默认值为 3。
- 每个 StatefulSet Pod 一个由 PVC 提供的 `ovn-data` 卷。默认请求容量为 5Gi，
  访问模式为 `ReadWriteOnce`；集群没有合适的默认 StorageClass 时设置
  `storageClassName`。
- 一个无头 `ovn-central` Service，为内部 Raft 流量提供 6643 和 6644 端口。
- `ovn-nb` 和 `ovn-sb` Service，为客户端流量提供 6641 和 6642 端口。

每个 HCP Pod 都配置了基于 `kubernetes.io/hostname` 的强制 Pod 反亲和，因此
调度器不会把两个 `ovn-central` Pod 放在同一节点上。Pod 同时容忍 `NoSchedule`、
`NoExecute` 和 `CriticalAddonsOnly` 污点，并由 Chart 限制在 Linux 节点上。classic
chart 还支持 `ovn-central.nodeSelector`。v2 chart 支持用户配置的
`central.nodeAffinity` 规则；HCP 模式不会附加常规的 master 节点亲和性，因此应
使用这些值选择 StatefulSet 应运行的节点。

## Service 暴露

HCP 的 `service.type` 默认为 `NodePort`，NB 默认 NodePort 为 30641，SB 默认
NodePort 为 30642。集群提供外部负载均衡器时，可以将 `service.type` 设置为
`LoadBalancer`。当类型为 `NodePort` 或 `LoadBalancer` 时，`nbNodePort` 和
`sbNodePort` 会用于 NB/SB Service。

只有 NB 和 SB Service 用于工作负载集群连接。无头 `ovn-central` Service 用于
StatefulSet 内部 Raft 流量，`ovn-northd` 保持为集群内使用的 ClusterIP Service。
确保每个工作负载集群都能将 `nbAddress` 和 `sbAddress` 中的主机及端口解析到已暴露
的 NB/SB Service。

## 使用边界

HCP 模式只改变 `ovn-central` 的部署和暴露方式，不会把工作负载集群的 agent 或
CRD 安装到其他集群。在工作负载集群中使用 data-plane 配置安装 Kube-OVN 组件，
并将 OVN NB/SB 端点指向 HCP 的 `nbAddress` 和 `sbAddress`。

HCP namespace、存储类、节点放置以及可从外部访问的 NB/SB 地址都属于运维前置条件。
创建网络资源前，应确认三个副本都能绑定各自 PVC，且工作负载集群节点可以访问两个
Service 端口。
