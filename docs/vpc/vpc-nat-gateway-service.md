# VPC NAT 网关提供 Service

VPC NAT 网关可以直接使用 nftables 为 Kubernetes Service 提供 DNAT。控制器监听 Service 和 EndpointSlice，在网关上编程后端、VIP、回程路由和 hairpin SNAT。`LoadBalancer` Service 可通过 EIP 访问，VPC 内流量可通过 Service 的 ClusterIP 访问。

该功能默认关闭。

## 开启功能

控制器提供两个相互独立的开关：

| 参数 | 作用 | 默认值 |
| --- | --- | --- |
| `--enable-gw-nftable-lb-svc` | 通过 EIP 为 `LoadBalancer` Service 提供入口地址 | `false` |
| `--enable-gw-nftable-svc-cluster-ip` | 在网关上持有并服务 Service ClusterIP | `false` |

安装脚本变量为 `ENABLE_GW_NFTABLE_LB_SVC` 和 `ENABLE_GW_NFTABLE_SVC_CLUSTER_IP`；Helm v1/v2 分别使用 `func.ENABLE_GW_NFTABLE_LB_SVC`/`features.enableGwNftableLoadbalancerService` 与 `func.ENABLE_GW_NFTABLE_SVC_CLUSTER_IP`/`features.enableGwNftableServiceClusterIp`。

- `--enable-gw-nftable-svc-cluster-ip` 与 `--enable-lb` 互斥，两者不能同时持有 ClusterIP 数据面。
- `--enable-gw-nftable-lb-svc` 与 `--enable-lb-svc` 互斥，两者不能同时持有 `LoadBalancer` Service 入口地址。
- 两个网关开关可以同时开启；也可以让网关处理 EIP、让 OVN LoadBalancer 处理 ClusterIP。
- `--enable-lb-svc` 仍需要 `--enable-lb` 或 ClusterIP 网关开关提供后端数据面。

## 配置 Service

`LoadBalancer` Service 必须指定网关和 EIP；ClusterIP Service 只需指定网关：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  annotations:
    ovn.kubernetes.io/vpc_nat_gw: gw1
    ovn.kubernetes.io/eip: eip1 # LoadBalancer Service 必填
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
```

控制器完成编程后会写入 `status.loadBalancer.ingress`。后端由 EndpointSlice 提供；所有 Ready 后端均参与负载均衡。

`IptablesDnatRule` 的 `type: share` 对象只是控制器维护的记账记录，不能手工创建、修改或删除，也不会直接驱动数据面。可使用以下命令查看状态：

```bash
kubectl get iptables-dnat-rules -l ovn.kubernetes.io/nftable-lb-svc-name=web
kubectl -n kube-system exec <vpc-nat-gw-pod> -- nft list table ip kube-ovn
kubectl -n kube-system exec <vpc-nat-gw-pod> -- ip -4 addr show dev lo label lo:ko-vip
kubectl ko nbctl lr-policy-list <vpc>
```

## 约束和升级

- 同一 EIP、端口和协议只能绑定一个 Service；冲突会被 webhook 拒绝。
- Service 使用的 EIP 必须属于标注的网关；删除 Service 前不能删除仍在使用的 EIP。
- 网关和 EIP 绑定不可修改；需要更换时删除并重新创建 Service。清除网关注解是退出该模式的方式。
- 仅支持 IPv4、TCP/UDP 和 `Cluster` 流量策略；不支持节点本地流量策略、拓扑感知路由或客户端源地址保留。
- `ClientIP` 会话亲和性支持整个 VIP 身份；多网卡后端必须在该 VPC 中存在可用网卡。
- 旧参数 `--enable-nftable-lb-svc` 已替换为上述两个参数，升级前必须更新 Deployment、安装脚本或 Helm values，旧参数没有别名。
