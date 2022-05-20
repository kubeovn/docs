Kube-OVN 默认会根据 Pod 所在 Namespace 所属的子网中分配 IP 和 Mac。如果用户需要指定 IP/Mac 可以在创建 Pod 时通过 annotation 来定义所需的 IP/Mac。

# 固定 IP 和 Mac 的示例

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-ip
  namespace: ls1
  annotations:
    ovn.kubernetes.io/ip_address: 10.16.0.15
    ovn.kubernetes.io/mac_address: 00:00:00:53:6B:B6
spec:
  containers:
  - name: static-ip
    image: nginx:alpine
```

在使用 annotation 定义 Pod IP/Mac 时需要注意以下几点：
1. 所使用的 IP/Mac 不能和已有的 IP/Mac 冲突
2. IP 必须在所属子网的 CIDR 内
3. 可以只指定 IP 或 Mac
