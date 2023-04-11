# 自定义 VPC EIP QoS

Kube-OVN 支持动态配置自定义 VPC 上 EIP 的出方向和入方向流量速率限制。

## 创建 QoS 策略

使用以下 YAML 配置创建 QoS 策略：

```yaml
apiVersion: kubeovn.io/v1
kind: QoSPolicy
metadata:
  name: qos-example
spec:
  bandwidthLimitRule:
    ingressMax: "1" # Mbps
    egressMax: "1" # Mbps
```

允许限制单个方向，示例如下：

```yaml
apiVersion: kubeovn.io/v1
kind: QoSPolicy
metadata:
  name: qos-example
spec:
  bandwidthLimitRule:
    ingressMax: "1" # Mbps
```

## EIP QoS

创建时指定：

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-random
spec:
  natGwDp: gw1
  qosPolicy: qos-example
```

支持动态添加/修改`.spec.qosPolicy`字段变更 QoS 规则。

## 查看设置 qos 的 EIP

通过`label`查看已经设置对应 qos 的 eip：

````bash
# kubectl get eip  -l ovn.kubernetes.io/qos=qos-example2
NAME    IP             MAC                 NAT   NATGWDP   READY
eip-1   172.18.11.2    00:00:00:C7:5E:99         gw1       true
eip-2   172.18.11.16   00:00:00:E5:38:37         gw2       true
```

## 限制

* 创建 QoS 策略后，不能更改带宽限制规则。如果需要为 EIP 设置新的速率限制规则，则可以将新的 QoS 策略更新到`IptablesEIP.spec.qosPolicy`字段中。
* 只有在未使用时才能删除 QoS 策略。因此，在删除 QoS 策略之前，必须先从任何相关的`IptablesEIP`中删除`IptablesEIP.spec.qosPolicy`字段。

