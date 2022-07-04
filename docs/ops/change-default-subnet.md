# 修改子网 CIDR

如果创建的子网 CIDR 冲突或不符合预期，可以通过本文档的步骤进行修改。

> 修改子网 CIDR 后之前创建的 Pod 将无法正常访问网络需要进行重建。
> 建议操作前慎重考虑。本文只针对业务子网 CIDR 更改进行操作，如需
> 更改 Join 子网 CIDR 请参考[更改 Join 子网 CIDR](./change-join-subnet.md)。

## 编辑子网

使用 `kubectl edit` 修改子网 `cidrBlock`，`gateway` 和 `excludeIps`。

```bash
kubectl edit subnet test-subnet
```

## 重建该子网绑定的 Namespace 下所有 Pod

以子网绑定 `test` Namespace 为例：

```bash
for pod in $(kubectl get pod --no-headers -n "$ns" --field-selector spec.restartPolicy=Always -o custom-columns=NAME:.metadata.name,HOST:spec.hostNetwork | awk '{if ($2!="true") print $1}'); do
  kubectl delete pod "$pod" -n test --ignore-not-found
done
```

若只使用了默认子网，可以使用下列命令删除所有非 host 网络模式的 Pod：

```bash
for ns in $(kubectl get ns --no-headers -o custom-columns=NAME:.metadata.name); do
  for pod in $(kubectl get pod --no-headers -n "$ns" --field-selector spec.restartPolicy=Always -o custom-columns=NAME:.metadata.name,HOST:spec.hostNetwork | awk '{if ($2!="true") print $1}'); do
    kubectl delete pod "$pod" -n "$ns" --ignore-not-found
  done
done
```

## 更改默认子网配置

若修改的为默认子网的 CIDR 还需要更改 `kube-ovn-controller` Deployment 的启动参数：

```yaml
args:
- --default-cidr=10.17.0.0/16
- --default-gateway=10.17.0.1
- --default-exclude-ips=10.17.0.1
```
