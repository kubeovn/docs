# Custom VPC EIP QoS

Kube-OVN supports dynamically configuring the egress and ingress traffic rate limits for custom VPC EIPs.

## Creating a QoS Policy

Use the following YAML configuration to create a QoS policy:

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

You can limit a single direction, as shown below:

```yaml
apiVersion: kubeovn.io/v1
kind: QoSPolicy
metadata:
  name: qos-example
spec:
  bandwidthLimitRule:
    ingressMax: "1" # Mbps
```

## Enabling EIP QoS

Specify the following when creating:

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-random
spec:
  natGwDp: gw1
  qosPolicy: qos-example
```

You can dynamically add/modify the `.spec.qosPolicy` field to change the QoS rules.

## Viewing EIPs with QoS Settings

View EIPs that have QoS set using the label:

```bash
# kubectl get eip  -l ovn.kubernetes.io/qos=qos-example2
NAME    IP             MAC                 NAT   NATGWDP   READY
eip-1   172.18.11.2    00:00:00:C7:5E:99         gw1       true
eip-2   172.18.11.16   00:00:00:E5:38:37         gw2       true
```

## Limitations

* After creating a QoS policy, you cannot change the bandwidth limit rules. If you need to set new rate limit rules for an EIP, you can update the new QoS policy to the `IptablesEIP.spec.qosPolicy` field.
* QoS policies can only be deleted when they are not in use. Therefore, before deleting a QoS policy, you must first remove the `IptablesEIP.spec.qosPolicy` field from any relevant `IptablesEIP`.
