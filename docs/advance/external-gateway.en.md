# External Gateway

In some scenarios, all container traffic access to the outside needs to be managed and audited through an external gateway.
Kube-OVN can forward outbound traffic to the corresponding external gateway by configuring the appropriate routes in the subnet.

## Usage

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
  policyRoutingTableID: 1000
  policyRoutingPriority: 1500
```

- `natOutgoing`: needs to be set to `false`.
- `externalEgressGateway`: Set to the address of the external gateway, which needs to be in the same Layer 2 reachable domain as the gateway node.
- `policyRoutingTableID`: The TableID of the local policy routing table used needs to be different for each subnet to avoid conflicts.
- `policyRoutingPriority`: Route priority, in order to avoid subsequent user customization of other routing operations conflict, here you can specify the route priority. If no special needs, you can fill in any value.
