# VPC Peering

VPC peering provides a mechanism for bridging two VPC networks through logical routes so that workloads within two VPCs
can access each other through private addresses as if they were on the same private network, without the need for NAT forwarding through a gateway.

## Prerequisites

1. This feature is only available for customized VPCs.
2. To avoid route overlap the subnet CIDRs within the two VPCs cannot overlap.
3. Currently, only interconnection of two VPCs is supported.
4. Every `vpcPeerings` entry must set `localConnectIP` as a CIDR with a mask, for example `169.254.0.1/30`. Both endpoints must belong to the same CIDR, and it must not overlap an existing subnet.

## Usage

First create two non-interconnected VPCs with one Subnet under each VPC,
and the CIDRs of the Subnets do not overlap with each other.

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-1
spec: {}
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net1
spec:
  vpc: vpc-1
  cidrBlock: 10.0.0.0/16
---
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-2
spec: {}
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net2
spec:
  vpc: vpc-2
  cidrBlock: 172.31.0.0/16
```

Add `vpcPeerings` and the corresponding static routes within each VPC:

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-1
spec: 
  vpcPeerings:
    - remoteVpc: vpc-2
      localConnectIP: 169.254.0.1/30
  staticRoutes:
    - cidr: 172.31.0.0/16
      nextHopIP: 169.254.0.2
      policy: policyDst
---
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: vpc-2
spec:
  vpcPeerings:
    - remoteVpc: vpc-1
      localConnectIP: 169.254.0.2/30
  staticRoutes:
    - cidr: 10.0.0.0/16
      nextHopIP: 169.254.0.1
      policy: policyDst
```

- `remoteVpc`: the name of another peering VPC.
- `localConnectIP`: Required. The IP address and CIDR of the interconnection endpoint, for example `169.254.0.1/30`. Both endpoints should belong to the same CIDR, and it must not overlap an existing subnet.
- `cidr`: CIDR of the peering Subnet.
- `nextHopIP`: the `localConnectIP` on the other end of the peering VPC.

### Parameter validation

When a VPC is created or updated, the admission webhook validates `localConnectIP` for every peering entry. An empty value is rejected with an error similar to:

```text
localConnectIP is required for vpc peering with vpc-2, e.g. 169.254.0.1/30
```

Non-empty values must also be valid CIDRs; validation failure prevents the interconnection logical router port from being created. If the admission webhook is disabled, the VPC controller repeats the required-field and CIDR checks during reconciliation and stops processing the VPC on failure. Set `localConnectIP` explicitly in every peering entry.

Create Pods under the two Subnets

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/logical_switch: net1
  name: vpc-1-pod
spec:
  containers:
    - name: vpc-1-pod
      image: docker.io/library/nginx:alpine
---
apiVersion: v1
kind: Pod
metadata:
  annotations:
    ovn.kubernetes.io/logical_switch: net2
  name: vpc-2-pod
spec:
  containers:
    - name: vpc-2-pod
      image: docker.io/library/nginx:alpine
```

Test the network connectivity

```bash
# kubectl exec -it vpc-1-pod -- ping $(kubectl get pod vpc-2-pod -o jsonpath='{.status.podIP}')
PING 172.31.0.2 (172.31.0.2): 56 data bytes
64 bytes from 172.31.0.2: seq=0 ttl=62 time=0.655 ms
64 bytes from 172.31.0.2: seq=1 ttl=62 time=0.086 ms
64 bytes from 172.31.0.2: seq=2 ttl=62 time=0.098 ms
^C
--- 172.31.0.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.086/0.279/0.655 ms
# kubectl exec -it vpc-2-pod -- ping $(kubectl get pod vpc-1-pod -o jsonpath='{.status.podIP}')
PING 10.0.0.2 (10.0.0.2): 56 data bytes
64 bytes from 10.0.0.2: seq=0 ttl=62 time=0.594 ms
64 bytes from 10.0.0.2: seq=1 ttl=62 time=0.093 ms
64 bytes from 10.0.0.2: seq=2 ttl=62 time=0.088 ms
^C
--- 10.0.0.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.088/0.258/0.594 ms
```
