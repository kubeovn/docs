# 自定义 VPC DNS

由于用户自定义 VPC 和 默认 VPC 网络相互隔离，自定 VPC 内无法访问到部署在默认 VPC 内的 coredns。
如果用户希望在自定义 VPC 内使用 Kubernetes 提供的集群内域名解析能力，可以参考本文档，利用 `vpc-dns` CRD 来实现。

该 CRD 最终会部署一个 coredns，该 Pod 有两个网卡，一个网卡在用户自定义 VPC，另一个网卡在默认 VPC 从而实现网络互通，同时通过[自定义 VPC 内部负载均衡](./vpc-internal-lb.md)提供自定义 VPC 内的一个内部负载均衡。

## 部署 vpc-dns 所依赖的资源

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:vpc-dns
rules:
  - apiGroups:
    - ""
    resources:
    - endpoints
    - services
    - pods
    - namespaces
    verbs:
    - list
    - watch
  - apiGroups:
    - discovery.k8s.io
    resources:
    - endpointslices
    verbs:
    - list
    - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: vpc-dns
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:vpc-dns
subjects:
- kind: ServiceAccount
  name: vpc-dns
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vpc-dns
  namespace: kube-system
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpc-dns-corefile
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
          lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
          pods insecure
          fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        forward . /etc/resolv.conf {
          prefer_udp
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

除了以上资源，该功能还依赖nat-gw-pod镜像进行路由配置。

## 配置附加网卡

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: ovn-nad
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "ovn-nad.default.ovn"
    }'
```

## 修改 ovn-default 子网的 provider

修改 ovn-default 的 provider，为上面 nad 配置的 provider `ovn-nad.default.ovn`

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: ovn-default
spec:
  cidrBlock: 10.16.0.0/16
  default: true
  disableGatewayCheck: false
  disableInterConnection: false
  enableDHCP: false
  enableIPv6RA: false
  excludeIps:
  - 10.16.0.1
  gateway: 10.16.0.1
  gatewayType: distributed
  logicalGateway: false
  natOutgoing: true
  private: false
  protocol: IPv4
  provider: ovn-nad.default.ovn # 只需修改该字段
  vpc: ovn-cluster
```

## 配置 vpc-dns 的 Configmap

在 kube-system 命名空间下创建 configmap，配置 vpc-dns 使用参数，用于后面启动 vpc-dns 功能：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpc-dns-config
  namespace: kube-system
data:
  coredns-vip: 10.96.0.3
  enable-vpc-dns: "true"
  nad-name: ovn-nad
  nad-provider: ovn-nad.default.ovn
```

* `enable-vpc-dns`：是否启用功能，默认 `true`。
* `coredns-image`：dns 部署镜像。默认为集群 coredns 部署版本。
* `coredns-vip`：为 coredns 提供 lb 服务的 vip。
* `coredns-template`：coredns 部署模板所在的 URL。默认获取当前版本 ovn 目录下 `coredns-template.yaml` 默认为 `https://raw.githubusercontent.com/kubeovn/kube-ovn/当前版本/yamls/coredns-template.yaml` 。
* `nad-name`：配置的 `network-attachment-definitions` 资源名称。
* `nad-provider`：使用的 provider 名称。
* `k8s-service-host`：用于 coredns 访问 k8s apiserver 服务的 ip，默认为集群内 apiserver 地址。
* `k8s-service-port`：用于 coredns 访问 k8s apiserver 服务的 port，默认为集群内 apiserver 端口。

## 部署 vpc-dns

配置 vpc-dns yaml：

```yaml
kind: VpcDns
apiVersion: kubeovn.io/v1
metadata:
  name: test-cjh1
spec:
  vpc: cjh-vpc-1
  subnet: cjh-subnet-1
```

* `vpc` ： 用于部署 dns 组件的 vpc 名称。
* `subnet`：用于部署 dns 组件的子名称。

查看部署资源的信息：

```bash
# kubectl get vpc-dns
NAME        ACTIVE   VPC         SUBNET   
test-cjh1   false    cjh-vpc-1   cjh-subnet-1   
test-cjh2   true     cjh-vpc-1   cjh-subnet-2 
```

`ACTIVE` : `true` 部署了自定义 dns 组件，`false` 无部署。

* 限制：一个 vpc 下只会部署一个自定义 dns 组件;
* 当一个 vpc 下配置多个 vpc-dns 资源（即同一个 vpc 不同的 subnet），只有一个 vpc-dns 资源状态 `true`，其他为 `fasle`;
* 当 `true` 的 vpc-dns 被删除掉，会获取其他 `false` 的 vpc-dns 进行部署。

## 验证部署结果

查看 vpc-dns Pod 状态，使用 label `app=vpc-dns`，可以查看所有 vpc-dns pod 状态：

```bash
# kubectl -n kube-system get pods -l app=vpc-dns
NAME                                 READY   STATUS    RESTARTS   AGE
vpc-dns-test-cjh1-7b878d96b4-g5979   1/1     Running   0          28s
vpc-dns-test-cjh1-7b878d96b4-ltmf9   1/1     Running   0          28s
```

查看 slr 状态信息：

```bash
# kubectl -n kube-system get slr
NAME                VIP         PORT(S)                  SERVICE                             AGE
vpc-dns-test-cjh1   10.96.0.3   53/UDP,53/TCP,9153/TCP   kube-system/slr-vpc-dns-test-cjh1   113s
```

进入该 VPC 下的 Pod，测试 dns 解析:

```bash
nslookup kubernetes.default.svc.cluster.local 10.96.0.3
```

vpc下switch所在的子网以及同一vpc下的其他子网下的pod都是可以解析
