# 使用 IPsec 加密节点间通信

Kube-OVN 可以使用 OVN/OVS 内置的 IPsec 能力加密节点间的 Geneve、VXLAN 和
STT 隧道。当前 IPsec 运行时由 `kube-ovn-cni` Pod 中的独立 `ipsec` 容器
负责，CNI 容器不再签发证书、启动 IKE/strongSwan、监听 CA Secret 或清理主机
XFRM 状态。

## 前置条件

- 节点之间允许 UDP 500（IKE）和 UDP 4500（NAT-T）。
- 节点内核启用 `xfrm`、`af_key` 等模块，并提供 OVN/OVS IPsec 所需的
  strongSwan 或 libreswan 运行时。
- Kube-OVN 使用的镜像包含匹配当前 OVN/OVS 的 IPsec agent。agent 会在启动时
  检查镜像中的输出保护能力，未应用对应 OVS monitor 补丁的镜像会拒绝启动。

## 证书与首次启用顺序

首次启用时必须保持 IPsec 关闭，先让普通 Pod 网络可用，再准备证书签发链路：

1. 使用 `ENABLE_OVN_IPSEC=false`（或对应 Helm 值）安装或升级 Kube-OVN。
2. 部署 cert-manager 及其 CA injector（如果使用外部签发后端），创建专用的
   ClusterIssuer，并等待 cert-manager 组件和 ClusterIssuer 为 `Ready`。
3. 确认 controller 和 CNI DaemonSet 已就绪，且普通 Pod 网络可以访问
   Kubernetes API。无需为 cert-manager 设置 `hostNetwork`。
4. 再将 controller 和 CNI 的 IPsec 开关设为 `true`，并等待 rollout 完成。

Kube-OVN 自带 signer 时不需要 cert-manager，但仍应先在关闭状态完成普通网络
和 controller 的准备。节点始终通过 Kubernetes CSR 请求身份；controller 会
校验绑定 Pod、Node UID、chassis 和请求的 CN/SAN 后签发或转交给 cert-manager。
CNI ServiceAccount 没有创建 CertificateRequest 的权限，只有 controller 可以
把已授权的 CSR 转发给指定的 ClusterIssuer。

## 启用 IPsec

安装脚本可以使用：

```bash
ENABLE_OVN_IPSEC=true
```

使用 Helm 时，v1 chart 使用 `ENABLE_OVN_IPSEC`，v2 chart 使用
`features.enableOvnIpsec`。如果通过 cert-manager 签发，还需启用
`--cert-manager-ipsec-cert=true`（v1）或 chart 中的 `ipsec.certManager.enabled`
并设置专用 issuer 名称。证书有效期、请求超时、优先级和资源限制位于 chart 的
`ipsec` 配置段。

启用后，CNI Pod 会渲染一个同镜像的 `ipsec` 容器，运行
`/kube-ovn/kube-ovn-ipsec`。该容器拥有 IPsec 密钥目录，并获得运行 IPsec 所需
的 `NET_ADMIN`、`NET_BIND_SERVICE` 和 `SYS_NICE`；CNI 容器显式丢弃
`SYS_NICE`，不因启用 IPsec 而获得额外调度或密钥权限。Pod 的 host network、
host PID 和 ServiceAccount 仍是共享边界，`ipsec` 容器不是独立的 Kubernetes
身份。

首次启用由 controller 协调：它冻结 DaemonSet UID、Pod 模板、信任 bundle 和
目标 Node UID，先等待所有节点完成身份准备并确认本地 agent 就绪，再依次安装
保护、启动运行时，最后切换 OVN 的全局 IPsec 开关。节点不能仅凭 Pod Ready 或
未签名的 Node annotation 通过这道屏障。CNI DaemonSet 使用
`maxSurge: 0`、`maxUnavailable: 1`，以便一次只替换一个节点并保持已有保护。

## 运行时与续期

IPsec agent 持久化待处理私钥、CSR 绑定和当前身份 generation。完整的密钥、证书
和信任 generation 会在一次 OVSDB 更新中激活，其他 `other_config` 条目保持不变。
证书续期时间在叶子证书生命周期的 40% 到 60% 之间抖动，避免所有节点同时续期；
已有有效身份时，失败的续期不会覆盖它。agent 监督 IKE 和 monitor 前台进程，
运行时故障采用 1 到 30 秒退避。

状态和就绪检查只公开 Node UID、chassis、generation 以及证书/信任摘要，不包含
PEM、私钥或 SA key。`readyz` 需要当前证书未过期、进程健康、内核保护已读回，
以及当前信任摘要已由本地 monitor 确认；这表示配置刷新完成，不表示每一条旧 SA
都已重新建立。IPsec 就绪失败会让 Pod 整体 NotReady，但不会重启 CNI 容器。

验证节点状态：

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=kube-ovn-cni
kubectl get csr
kubectl get clusterissuer
kubectl exec -n kube-system <kube-ovn-cni-pod> -c ipsec -- \
  ovs-appctl ipsec/show
```

## 禁用和有限清理

禁用不是简单地把 Pod 中的 `ipsec` 容器删除。先将 controller 和 CNI 的 IPsec
开关改为 `false`，controller 会持久化 `Disabling` challenge，并同步读取 NB/SB
确认两个数据库开关都已关闭。随后 chart 和安装脚本把 `ipsec` 容器替换为一次性
`ipsec-cleanup` init container：

- 没有历史 IPsec 状态时立即成功退出；不会启动 IKE/monitor、读取 CA、签发证书
  或导入旧身份。
- 只在初始化期间以 root 运行，使用 `NET_ADMIN` 和 `NET_BIND_SERVICE`，不使用
  `SYS_NICE`；没有 `restartPolicy`、probe 或常驻清理进程。
- 逐节点检查本地 tunnel、所属连接和 SA 是否已 drain，并验证当前 Node UID、
  Pod UID、CSR、模板和 controller challenge。发现缺失证据、外部 owner 或未完成
  drain 时保留保护并让该节点稍后重试。
- 只有在本节点的保护、lease 和身份引用均通过 live 检查后，才撤销本节点自己的
  output lease 与保护 guard，写入签名的 released receipt 后退出。不会删除外部
  owner 的 SA、policy 或接口。

controller 逐一验证所有冻结节点的 receipt 后才记录 `Disabled`，支持
`maxUnavailable: 1` 的串行 rollout。已成功完成的 init 结果只在同一个活动 Pod、
模板和 Release epoch 内复用；运行中或失败的 init 不能满足 Release barrier。
controller 不创建额外 DaemonSet，也不需要新增 Kubernetes 权限。任何本地清理
失败都会保留节点保护，直到下一次受控重试。

## 故障排查与权限边界

- `kubectl get csr` 中的 IPsec CSR 应属于当前 `kube-ovn-cni` Pod 和 Node UID；
  不要用请求名称单独判断身份。
- 使用 cert-manager 时，ClusterIssuer 应专用于 Kube-OVN IPsec。controller 会
  校验 issuer、namespace、请求者 ServiceAccount、用途、有效期和返回证书链；
  泛化的 cert-manager 自动 approver 不能绕过该路径。
- controller 的 Secret、CSR 和 cert-manager 权限限制在其配置的 namespace；
  CNI 不应获得创建 CertificateRequest 的权限。
- 运行 `ovs-appctl ipsec/show` 或 agent 的 `readyz` 失败时，先检查证书摘要、
  monitor readback、内核 guard 以及 UDP 500/4500 连通性，再检查 OVN/OVS 日志。
- 不要手工删除 XFRM SA、IPsec 密钥目录或 `ovn-ipsec-coordination` ConfigMap；
  这些对象由 controller 和 agent 的受保护流程共同管理。
