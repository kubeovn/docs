# 外部网关设置

在一些场景下，对所有容器访问外部的流量需要通过一个外部的网关进行统一的管理和审计。
Kube-OVN 可以通过在子网中进行相应的路由配置，将出网流量转发至对应的外部网关。

## 使用方式

```yaml
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: external
spec:
  cidrBlock: 172.31.0.0/16
  gatewayType: centralized
  natOutgoing: false
  externalEgressGateway: 192.168.0.1
  policyRoutingPriority: 
  policyRoutingTableID: 
```

- `natOutgoing`: 需要设置为 `false`。
- `externalEgressGateway`：设置为外部网关的地址，需要和网关节点在同一个二层可达域。
- `policyRoutingPriority`，`policyRoutingTableID`：使用的本地策略路由表的优先级和 TableID 注意不要和已有表项冲突。
