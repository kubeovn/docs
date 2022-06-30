# BGP Support

Kube-OVN 支持将 Pod 或 Subnet 的 IP 地址通过 BGP 协议向外部进行路由广播，从而使得 Pod IP 可以直接对外暴露。
如果需要使用该功能，需要在特定节点安装 `kube-ovn-speaker` 并对需要对外暴露的 Pod 或 Subnet 增加对应的 annotation。

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
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/release-1.10/yamls/speaker.yaml
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
kubectl annotate pod perf-ovn-xzvd4 ovn.kubernetes.io/bgp-
kubectl annotate subnet ovn-default ovn.kubernetes.io/bgp-
```

## BGP 高级选项

`kube-ovn-speaker` 支持更多 BGP 参数进行高级配置，用户可根据自己网络环境进行调整：

- `announce-cluster-ip`: 是否对外发布 Service 路由，默认为 `false`。
- `auth-password`: BGP peer 的访问密码。
- `holdtime`: BGP 邻居间的心跳探测时间，超过改时间没有消息的邻居将会被移除，默认为 90 秒。
- `graceful-restart`: 是否启用 BGP Graceful Restart。
- `graceful-restart-time`: BGP Graceful restart time 可参考 RFC4724 3。
- `graceful-restart-deferral-time`: BGP Graceful restart deferral time 可参考 RFC4724 4.1。
