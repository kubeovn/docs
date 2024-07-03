# BGP 支持

Kube-OVN 支持将 Pod 或 Subnet 的 IP 地址通过 BGP 协议向外部进行路由广播，从而使得 Pod IP 可以直接对外暴露。
如果需要使用该功能，需要在特定节点安装 `kube-ovn-speaker` 并对需要对外暴露的 Pod 或 Subnet 增加对应的 annotation。

Kube-OVN 还支持通过相同的注释广播 ClusterIP 类型 Service 的 IP 地址。

## 安装 kube-ovn-speaker

`kube-ovn-speaker` 内使用 [GoBGP](https://osrg.github.io/gobgp/) 对外发布路由信息，并将访问暴露地址的下一跳路由指向自身。

由于部署 `kube-ovn-speaker` 的节点需要承担回程流量，因此需要选择特定节点进行部署：

```bash
kubectl label nodes speaker-node-1 ovn.kubernetes.io/bgp=true
kubectl label nodes speaker-node-2 ovn.kubernetes.io/bgp=true
```

> 当存在多个 kube-ovn-speaker 实例时，每个实例都会对外发布路由，上游路由器需要支持多路径 ECMP。

下载对应 yaml:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/yamls/speaker.yaml
```

修改 yaml 内相应配置：

```yaml
--neighbor-address=10.32.32.1
--neighbor-as=65030
--cluster-as=65000
```

- `neighbor-address`: BGP Peer 的地址，通常为路由器网关地址。
- `neighbor-as`: BGP Peer 的 AS 号。
- `cluster-as`: 容器网络的 AS 号。

部署 yaml:

```bash
kubectl apply -f speaker.yaml
```

## 发布 Pod/Subnet 路由

如需使用 BGP 对外发布路由，首先需要将对应 Subnet 的 `natOutgoing` 设置为 `false`，使得 Pod IP 可以直接进入底层网络。

增加 annotation 对外发布：

```bash
kubectl annotate pod sample ovn.kubernetes.io/bgp=true
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp=true
```

删除 annotation 取消发布：

```bash
kubectl annotate pod sample ovn.kubernetes.io/bgp-
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp-
```

## 发布 `ClusterIP` 类型 Service 路由

要将 Service 的 ClusterIP 公布给外部，需要将 `kube-ovn-speaker` 选项 `--announce-cluster-ip` 设置为 `true`。 有关更多详细信息，请参阅 BGP 高级选项。

增加 annotation 对外发布：

```bash
kubectl annotate service sample ovn.kubernetes.io/bgp=true
```

删除 annotation 取消发布：

```bash
kubectl annotate service sample ovn.kubernetes.io/bgp-
```

## 发布策略

`kube-ovn-speaker` 支持两种发布路由的策略:

- **Cluster**: 在这个策略下要求每个 speaker 都会对外发布 Pod IPs/Subnet CIDRs，无论当前节点是否有具有特定 IP 或属于该节点上的子网 CIDR 的 Pod。换句话说，流量可能从任何 speaker 节点进入，然后在集群内部路由到实际的 Pod。在这种配置中可能会使用额外的跳数。这是 Pod 和 Subnet 的默认发布策略。
- **Local**: 在这个策略下，Pod IPs 的路由只会从 Pod 所在的节点被发布。这意味着相比 Cluster 策略外部流量会直接到到 Pod 所在节点，跳数会更少。

> 注意: 为了使用 `Local` 发布策略，你需要在每个节点都运行 `kube-ovn-speaker`。如果 Pod 所在的节点没有 speaker 运行，路由将无法对外发布。

默认的发布策略为 `Cluster`，可以通过 Pod/Subnet 的 annotation `ovn.kubernetes.io/bgp` 来进行更改：

- `ovn.kubernetes.io/bgp=cluster` 或 `ovn.kubernetes.io/bgp=yes` 将会使用 `Cluster` 策略。
- `ovn.kubernetes.io/bgp=local` 将会使用 `Local` 策略。

> 注意：由于 Service 的流量最终是由 `kube-proxy` 进行处理，`ClusterIP` 类型 Service 对外发布路由只支持 `Cluster` 策略。

## BGP 高级选项

`kube-ovn-speaker` 支持更多 BGP 参数进行高级配置，用户可根据自己网络环境进行调整：

- `announce-cluster-ip`: 是否对外发布 Service 路由，默认为 `false`。
- `auth-password`: BGP peer 的访问密码。
- `holdtime`: BGP 邻居间的心跳探测时间，超过改时间没有消息的邻居将会被移除，默认为 90 秒。
- `graceful-restart`: 是否启用 BGP Graceful Restart。
- `graceful-restart-time`: BGP Graceful restart time 可参考 RFC4724 3。
- `graceful-restart-deferral-time`: BGP Graceful restart deferral time 可参考 RFC4724 4.1。
- `passivemode`: Speaker 运行在 passive 模式，不主动连接 peer。
- `ebgp-multihop`: ebgp ttl 默认值为 1。
