# 修改 Join 子网 CIDR


若发现创建的 Join 子网 CIDR 冲突或不符合预期，可以通过本文档进行修改。

> 修改 Join 子网 CIDR 后之前创建的 Pod 将无法正常访问外部网络，需要等重建完成,
> 建议前操作时慎重考虑。

## 删除 Join 子网

```bash
kubectl patch subnet join --type='json' -p '[{"op": "replace", "path": "/metadata/finalizers", "value": []}]'
kubectl delete subnet join
```

## 清理相关分配信息

```bash
kubectl annotate node ovn.kubernetes.io/allocated=false --all --overwrite
```

## 修改 Join 子网相关信息

修改 `kube-ovn-controller` 内 Join 子网相关信息：

```bash
kubectl edit deployment -n kube-system kube-ovn-controller
```

修改下列参数

```yaml
args:
- --node-switch-cidr=100.51.0.0/16
```

重启 `kube-ovn-controller` 重建 `join` 子网：

```bash
kubectl delete pod -n kube-system -lapp=kube-ovn-controller
```

查看新的 Join 子网信息：

```bash
# kubectl get subnet
NAME          PROVIDER   VPC           PROTOCOL   CIDR            PRIVATE   NAT     DEFAULT   GATEWAYTYPE   V4USED   V4AVAILABLE   V6USED   V6AVAILABLE   EXCLUDEIPS
join          ovn        ovn-cluster   IPv4       100.51.0.0/16   false     false   false     distributed   2        65531         0        0             ["100.51.0.1"]
ovn-default   ovn        ovn-cluster   IPv4       10.17.0.0/16    false     true    true      distributed   5        65528         0        0             ["10.17.0.1"]
```

## 重新配置 ovn0 网卡地址

每个节点的 `ovn0` 网卡信息需要重新更新，可通过重启 `kube-ovn-cni` 来完成：

```bash
kubectl delete pod -n kube-system -l app=kube-ovn-cni
```

