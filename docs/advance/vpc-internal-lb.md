# 自定义 VPC 内部负载均衡

Kubernetes 提供的 Service 可以用作集群内的负载均衡， 但是在自定义 VPC 模式下，
使用 Service 作为内部负载均衡存在如下几个问题：

1. Service IP 范围为集群资源，所有自定义 VPC 共享，无法重叠。
2. 用户无法按照自己意愿设置内部负载均衡的 IP 地址。

为了解决上述问题，Kube-OVN 在 1.11 引入 `SwitchLBRule` CRD，用户可以设置自定义 VPC 内的内部负载均衡规则。

`SwitchLBRule` 样例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: SwitchLBRule
metadata:
  name:  cjh-slr-nginx
spec:
  vip: 1.1.1.1
  sessionAffinity: ClientIP
  namespace: default
  selector:
    - app:nginx
  ports:
  - name: dns
    port: 8888
    targetPort: 80
    protocol: TCP
```

- `selector`, `sessionAffinity` 和 `port` 使用方式同 Kubernetes Service。
- `vip`：自定义负载均衡的 IP 地址。
- `namespace`：`selector` 所选择 Pod 所在命名空间。

Kube-OVN 会根据 `SwitchLBRule` 定义选择的 Pod 得出 Pod 所在 VPC 并设置对应的 L2 LB。
