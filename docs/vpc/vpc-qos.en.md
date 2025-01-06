# VPC QoS

Kube-OVN supports using QoSPolicy CRD to limit the traffic rate of custom VPC.

## EIP QoS

Limit the speed of EIP to 1Mbps and the priority to 1, and `shared=false` here means that this QoSPolicy can only be used for this EIP and support dynamically modifying QoSPolicy to change QoS rules.

The QoSPolicy configuration is as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: QoSPolicy
metadata:
  name: qos-eip-example
spec:
  shared: false
  bindingType: EIP
  bandwidthLimitRules:
  - name: eip-ingress
    rateMax: "1" # Mbps
    burstMax: "1" # Mbps
    priority: 1
    direction: ingress
  - name: eip-egress
    rateMax: "1" # Mbps
    burstMax: "1" # Mbps
    priority: 1
    direction: egress
```

The IptablesEIP configuration is as follows:

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-1
spec:
  natGwDp: gw1
  qosPolicy: qos-eip-example
```

The value of `.spec.qosPolicy` supports being specified during creation and also supports modification after creation.

## View EIPs with QoS enabled

View the corresponding EIPs that have been set up using `label`:

```bash
# kubectl get eip  -l ovn.kubernetes.io/qos=qos-eip-example
NAME    IP             MAC                 NAT   NATGWDP   READY
eip-1   172.18.11.24   00:00:00:34:41:0B   fip   gw1       true
```

## QoS for VPC NATGW net1 NIC

Limit the speed of the net1 NIC on VPC NATGW to 10Mbps and set the priority to 3. Here `shared=true`, which means that this QoSPolicy can be used by multiple resources at the same time, and does not allow the modification of the contents of the QoSPolicy in this scenario.

The QoSPolicy configuration is as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: QoSPolicy
metadata:
  name: qos-natgw-example
spec:
  shared: true
  bindingType: NATGW
  bandwidthLimitRules:
  - name: net1-ingress
    interface: net1
    rateMax: "10" # Mbps
    burstMax: "10" # Mbps
    priority: 3
    direction: ingress
  - name: net1-egress
    interface: net1
    rateMax: "10" # Mbps
    burstMax: "10" # Mbps
    priority: 3
    direction: egress
```

The VpcNatGateway configuration is as follows:

```yaml
kind: VpcNatGateway
apiVersion: kubeovn.io/v1
metadata:
  name: gw1
spec:
  vpc: test-vpc-1
  subnet: net1
  lanIp: 10.0.1.254
  qosPolicy: qos-natgw-example
  selector:
    - "kubernetes.io/hostname: kube-ovn-worker"
    - "kubernetes.io/os: linux"
```

The value of `.spec.qosPolicy` supports both creation and subsequent modification.

## QoS for specific traffic on net1 NIC

Limit the specific traffic on net1 NIC to 5Mbps and set the priority to 2. Here `shared=true`, which means that this QoSPolicy can be used by multiple resources at the same time, and does not allow the modification of the contents of the QoSPolicy in this scenario.

The QoSPolicy configuration is as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: QoSPolicy
metadata:
  name: qos-natgw-example
spec:
  shared: true
  bindingType: NATGW
  bandwidthLimitRules:
  - name: net1-extip-ingress
    interface: net1
    rateMax: "5" # Mbps
    burstMax: "5" # Mbps
    priority: 2
    direction: ingress
    matchType: ip
    matchValue: src 172.18.11.22/32
  - name: net1-extip-egress
    interface: net1
    rateMax: "5" # Mbps
    burstMax: "5" # Mbps
    priority: 2
    direction: egress
    matchType: ip
    matchValue: dst 172.18.11.23/32
```

The VpcNatGateway configuration is as follows:

```yaml
kind: VpcNatGateway
apiVersion: kubeovn.io/v1
metadata:
  name: gw1
spec:
  vpc: test-vpc-1
  subnet: net1
  lanIp: 10.0.1.254
  qosPolicy: qos-natgw-example
  selector:
    - "kubernetes.io/hostname: kube-ovn-worker"
    - "kubernetes.io/os: linux"
```

## View NATGWs with QoS enabled

View the corresponding NATGWs that have been set up using `label`:

```bash
# kubectl get vpc-nat-gw  -l ovn.kubernetes.io/qos=qos-natgw-example
NAME   VPC          SUBNET   LANIP
gw1    test-vpc-1   net1     10.0.1.254
```

## View QoS rules

```bash
# kubectl get qos -A
NAME                SHARED   BINDINGTYPE
qos-eip-example     false    EIP
qos-natgw-example   true     NATGW
```

## Limitations

* QoSPolicy can only be deleted when it is not in use. Therefore, before deleting the QoSPolicy, please check the EIP and NATGW that have enabled QoS, and remove their `spec.qosPolicy` configuration.
