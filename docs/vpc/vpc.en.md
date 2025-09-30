# Config VPC

Kube-OVN supports multi-tenant isolation level VPC networks. Different VPC networks are independent of each other
and can be configured separately with Subnet CIDRs, routing policies, security policies, outbound gateways, EIP, etc.

> VPC is mainly used in scenarios where strong isolation is required for multi-tenant networks
> and some Kubernetes networking features conflict under multi-tenant networks.
> For example, node and pod access, NodePort functionality, network access-based health checks,
> and DNS capabilities are not supported in multi-tenant network scenarios at this time.
> In order to facilitate common Kubernetes usage scenarios, Kube-OVN has a special design for the default
> VPC where the Subnet under the VPC can meet the Kubernetes specification.
> The custom VPC supports static routing, EIP and NAT gateways as described in this document.
> Common isolation requirements can be achieved through network policies and Subnet ACLs under the default VPC,
> so before using a custom VPC, please make sure whether you need VPC-level isolation and understand the limitations under the custom VPC.
> For Underlay subnets, physical switches are responsible for data-plane forwarding, so VPCs cannot isolate Underlay subnets.

![](../static/network-topology.png)

## Implementation Principle

In Kube-OVN, each VPC is mapped to a [Logical Router](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#Logical_Router_TABLE){: target="_blank" } in OVN. Multiple logical routers are independent network units, and each logical router can be associated with its own [Logical Switches](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#Logical_Switch_TABLE){: target="_blank" }, thereby having independent network ports and IP address spaces. Traffic from different VPCs is distinguished and isolated by different Datapath IDs when traversing tunnels, and forwarding is performed based on Datapath IDs. This ensures IP address space isolation, allowing the same IP addresses to be used in different VPCs without conflicts. For tunnel encapsulation formats, refer to [OVN Architecture Design Decisions](https://man7.org/linux/man-pages/man7/ovn-architecture.7.html#DESIGN_DECISIONS){: target="_blank" }.  

## Creating Custom VPCs

Create two VPCs:

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  namespaces:
  - ns1
---
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-2
spec:
  namespaces:
    - ns2
```

- `namespaces`: Limit which namespaces can use this VPC. If empty, all namespaces can use this VPC.

Create two Subnets, belonging to two different VPCs and having the same CIDR:

```yaml
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net1
spec:
  vpc: test-vpc-1
  cidrBlock: 10.0.1.0/24
  protocol: IPv4
  namespaces:
    - ns1
---
kind: Subnet
apiVersion: kubeovn.io/v1
metadata:
  name: net2
spec:
  vpc: test-vpc-2
  cidrBlock: 10.0.1.0/24
  protocol: IPv4
  namespaces:
    - ns2
```

Create Pods under two separate Namespaces:

```yaml
apiVersion: v1
kind: Pod
metadata:
  namespace: ns1
  name: vpc1-pod
spec:
  containers:
    - name: vpc1-pod
      image: docker.io/library/nginx:alpine
---
apiVersion: v1
kind: Pod
metadata:
  namespace: ns2
  name: vpc2-pod
spec:
  containers:
    - name: vpc2-pod
      image: docker.io/library/nginx:alpine
```

After running successfully, you can observe that the two Pod addresses belong to the same CIDR,
but the two Pods cannot access each other because they are running on different tenant VPCs.

## Create VPC NAT Gateway

Pod access to the external network within the VPC requires a VPC gateway, which bridges the physical and tenant networks and provides floating IP, SNAT and DNAT capabilities.

The VPC gateway function relies on Multus-CNI function, please refer to [multus-cni](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/quickstart.md){: target = "_blank" }.

!!! note

    Subnets under custom VPCs do not support distributed gateways and centralized gateways under default VPCs.

    Currently, custom VPCs support three solutions for external network connectivity: VPC NAT Gateway, OVN Gateway, and Egress Gateway. Among them, VPC NAT Gateway is the earliest supported egress method by Kube-OVN, creating a multi-NIC Pod for each VPC NAT Gateway, with one NIC connected to the custom VPC network and another NIC connected to the underlying physical network through Macvlan, implementing various ingress/egress operations through iptables within the Pod. This method currently supports the most features and has been used for the longest time, but it also has the disadvantages of single point of failure and complex usage.

    OVN Gateway uses various NAT capabilities natively supported within OVN to implement ingress/egress, which can improve performance through hardware acceleration and achieve failover through OVN's built-in BFD. Since it exposes OVN's native concepts, users need to be fairly familiar with OVN's application.

    Egress Gateway is an improvement to address the single point issue of VPC NAT Gateway, implementing horizontal scaling and fast failover, but currently only implements egress capability without ingress capability.

### Configuring the External Network

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: ovn-vpc-external-network
spec:
  protocol: IPv4
  provider: ovn-vpc-external-network.kube-system
  cidrBlock: 192.168.0.0/24
  gateway: 192.168.0.1  # IP address of the physical gateway
  excludeIps:
  - 192.168.0.1..192.168.0.10
---
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: ovn-vpc-external-network
  namespace: kube-system
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "macvlan",
      "master": "eth1",
      "mode": "bridge",
      "ipam": {
        "type": "kube-ovn",
        "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
        "provider": "ovn-vpc-external-network.kube-system"
      }
    }'
```

- This Subnet is used to manage the available external addresses and the address will be allocated to VPC NAT Gateway through Macvlan, so please communicate with your network administrator to give you the available physical segment IPs.
- The VPC gateway uses Macvlan for physical network configuration, and `master` of `NetworkAttachmentDefinition` should be the NIC name of the corresponding physical network NIC.
- `name`: External network name.

For macvlan mode, the nic will send packets directly through that node NIC,
relying on the underlying network devices for L2/L3 level forwarding capabilities. You need to configure the corresponding gateway,
Vlan and security policy in the underlying network device in advance.

1. For OpenStack VM environments, you need to turn off `PortSecurity` on the corresponding network port.
2. For VMware vSwitch networks, `MAC Address Changes`, `Forged Transmits` and `Promiscuous Mode Operation` should be set to `allow`.
3. For Hyper-V virtualization,  `MAC Address Spoofing` should be enabled in VM nic advanced features.
4. Public clouds, such as AWS, GCE, AliCloud, etc., do not support user-defined Mac, so they cannot support Macvlan mode network.
5. Due to the limitations of Macvlan itself, a Macvlan sub-interface cannot access the address of the parent interface, which means that it is not possible to access the Pod through the network on the host machine where the VpcNATGateway Pod is located.
6. If the physical network card corresponds to a switch interface in Trunk mode, a sub-interface needs to be created on the network card and provided to Macvlan for use.

### Enabling the VPC Gateway

The VPC gateway functionality can be enabled by configuring the `ovn-vpc-nat-gw-config` in the `kube-system` namespace. The `nodeSelector` can be used to specify the node where the gateway is deployed:

```yaml
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: ovn-vpc-nat-config
  namespace: kube-system
data:
  image: docker.io/kubeovn/vpc-nat-gateway:{{ variables.version }}
  nodeSelector: |
    kubernetes.io/hostname: kube-ovn-control-plane
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: ovn-vpc-nat-gw-config
  namespace: kube-system
data:
  enable-vpc-nat-gw: 'true'
```

- `image`: The image used by the Gateway Pod.
- `enable-vpc-nat-gw`: Controls whether the VPC Gateway feature is enabled.

### Create VPC Gateway

```yaml
kind: VpcNatGateway
apiVersion: kubeovn.io/v1
metadata:
  name: gw1
spec:
  vpc: test-vpc-1
  subnet: net1
  lanIp: 10.0.1.254
  selector:
    - "kubernetes.io/hostname: kube-ovn-worker"
    - "kubernetes.io/os: linux"
  externalSubnets:
    - ovn-vpc-external-network
```

- `vpc`: The VPC to which this VpcNatGateway belongs.
- `subnet`: A Subnet within the VPC, the VPC Gateway Pod will use `lanIp` to connect to the tenant network under that subnet.
- `lanIp`: An unused IP within the `subnet` that the VPC Gateway Pod will eventually use. When configuring routing for a VPC, the  `nextHopIP` needs to be set to the `lanIp` of the current VpcNatGateway.
- `selector`: The node selector for VpcNatGateway Pod has the same format as NodeSelector in Kubernetes.
- `externalSubnets`: External network used by the VPC gateway, if not configured, `ovn-vpc-external-network` is used by default, and only one external network is supported in the current version.

Other configurable parameters:

- `tolerations`: Configure tolerance for the VPC gateway. For details, see [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/#taint-nodes-by-condition)
- `affinity`: Configure affinity for the Pod or node of the VPC gateway. For details, see [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)

Things to note when using VPC-NAT-GW:

1. After the nat gw pod is created, the nic net1 arp is disabled and the physical gateway cannot be pinged. After creating the eip, the arp will be automatically enabled and the ping to underlay gateway should be ok.

### Create EIP

EIP allows for floating IP, SNAT, and DNAT operations after assigning an IP from an external network segment to a VPC gateway.

Randomly assign an address to the EIP:

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-random
spec:
  natGwDp: gw1
```

Fixed EIP address assignment:

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-static
spec:
  natGwDp: gw1
  v4ip: 192.168.0.100
```

Specify the external network on which the EIP is located:

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eip-random
spec:
  natGwDp: gw1
  externalSubnet: ovn-vpc-external-network
```

- `externalSubnet`: The name of the external network on which the EIP is located. If not specified, it defaults to `ovn-vpc-external-network`. If specified, it must be one of the `externalSubnets` of the VPC gateway.

### Create DNAT Rules

Through the DNAT rules, external can access to an IP and port within a VPC through an EIP and port.

```yaml
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eipd01
spec:
  natGwDp: gw1

---
kind: IptablesDnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: dnat01
spec:
  eip: eipd01
  externalPort: '8888'
  internalIp: 10.0.1.10
  internalPort: '80'
  protocol: tcp
```

### Create SNAT Rules

Through SNAT rules, when a Pod in the VPC accesses an external address, it will go through the corresponding EIP for SNAT.

```yaml
---
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eips01
spec:
  natGwDp: gw1
---
kind: IptablesSnatRule
apiVersion: kubeovn.io/v1
metadata:
  name: snat01
spec:
  eip: eips01
  internalCIDR: 10.0.1.0/24
```

### Create Floating IP

Through floating IP rules, one IP in the VPC will be completely mapped to the EIP, and the external can access the IP in the VPC through this EIP. When the IP in the VPC accesses the external address, it will be SNAT to this EIP

```yaml
---
kind: IptablesEIP
apiVersion: kubeovn.io/v1
metadata:
  name: eipf01
spec:
  natGwDp: gw1

---
kind: IptablesFIPRule
apiVersion: kubeovn.io/v1
metadata:
  name: fip01
spec:
  eip: eipf01
  internalIp: 10.0.1.5
```

## Custom Routing

Within the custom VPC, users can customize the routing rules within the VPC and combine it with the gateway for more flexible forwarding.
Kube-OVN supports static routes and more flexible policy routes.

### Static Routes

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  staticRoutes:
    - cidr: 0.0.0.0/0
      nextHopIP: 10.0.1.254
      policy: policyDst
    - cidr: 172.31.0.0/24
      nextHopIP: 10.0.1.253
      policy: policySrc
      routeTable: "rtb1"
```

- `policy`: Supports destination routing `policyDst` and source routing `policySrc`.
- When there are overlapping routing rules, the rule with the longer CIDR mask has higher priority,
  and if the mask length is the same, the destination route has a higher priority over the source route.
- `routeTable`: You can store the route in specific table, default is main table. Associate with subnet please defer to [Create Custom Subnets](../guide/subnet.en.md/#create-custom-subnets)

### Policy Routes

Traffic matched by static routes can be controlled at a finer granularity by policy routing.
Policy routing provides more precise matching rules, priority control and more forwarding actions.
This feature brings the OVN internal logical router policy function directly to the outside world, for more information on its use, please refer to [Logical Router Policy](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#Logical_Router_Policy_TABLE){: target = "_blank" }.

An example of policy routes:

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  policyRoutes:
    - action: drop
      match: ip4.src==10.0.1.0/24 && ip4.dst==10.0.1.250
      priority: 11
    - action: reroute
      match: ip4.src==10.0.1.0/24
      nextHopIP: 10.0.1.252
      priority: 10
```

## Custom Internal Load Balancing Rules

Kubernetes' built-in Service capability can fulfill internal load balancing functions, but due to Kubernetes implementation limitations, Service IP addresses are globally allocated and cannot be duplicated. For VPC usage scenarios, users want to customize the address range of internal load balancing, and load balancing addresses under different VPCs may overlap. Kubernetes' built-in Service functionality cannot fully satisfy this requirement.

For such scenarios, Kube-OVN provides the `SwitchLBRule` resource, allowing users to customize the address range of internal load balancing.

An example of `SwitchLBRule`:

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

- `vip`: Custom internal load balancing address.
- `namespace`: Namespace where the load balancer backend Pods are located.
- `sessionAffinity`: Same functionality as Service's `sessionAffinity`.
- `selector`: Same functionality as Service's `selector`.
- `ports`: Same functionality as Service's `port`.

View deployed internal load balancer rules:

```bash
# kubectl get slr
NAME                VIP         PORT(S)                  SERVICE                             AGE
vpc-dns-test-cjh2   10.96.0.3   53/UDP,53/TCP,9153/TCP   kube-system/slr-vpc-dns-test-cjh2   88m
```

## Custom vpc-dns

Due to the isolation between custom VPCs and default VPC networks, Pods in VPCs cannot use the default coredns service for domain name resolution. If you want to use coredns to resolve Service domain names within the custom VPC, you can use the `vpc-dns` resource provided by Kube-OVN.

### Create an Additional Network

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: ovn-nad
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "ovn-nad.default.ovn"
    }'
```

### Modify the Provider of the ovn-default Logical Switch

Modify the provider of ovn-default to the provider `ovn-nad.default.ovn` configured above in nad:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: ovn-default
spec:
  cidrBlock: 10.16.0.0/16
  default: true
  disableGatewayCheck: false
  disableInterConnection: false
  enableDHCP: false
  enableIPv6RA: false
  excludeIps:
  - 10.16.0.1
  gateway: 10.16.0.1
  gatewayType: distributed
  logicalGateway: false
  natOutgoing: true
  private: false
  protocol: IPv4
  provider: ovn-nad.default.ovn
  vpc: ovn-cluster
```

### Modify the vpc-dns ConfigMap

Create a ConfigMap in the kube-system namespace, configure the vpc-dns parameters to be used for the subsequent vpc-dns feature activation:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpc-dns-config
  namespace: kube-system
data:
  coredns-vip: 10.96.0.3
  enable-vpc-dns: "true"
  nad-name: ovn-nad
  nad-provider: ovn-nad.default.ovn
```

- `enable-vpc-dns`: (optional) `true` to enable the feature, `false` to disable the feature. Default `true`.
- `coredns-image`: (optional): DNS deployment image. Default is the cluster coredns deployment version.
- `coredns-template`: (optional): URL of the DNS deployment template. Default: `yamls/coredns-template.yaml` in the current version repository.
- `coredns-vip`: VIP providing LB service for coredns.
- `nad-name`: Name of the configured `network-attachment-definitions` resource.
- `nad-provider`: Name of the used provider.
- `k8s-service-host`: (optional) IP used by coredns to access the k8s apiserver service.
- `k8s-service-port`: (optional) Port used by coredns to access the k8s apiserver service.

### Deploying VPC-DNS Dependent Resources

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:vpc-dns
rules:
  - apiGroups:
    - ""
    resources:
    - endpoints
    - services
    - pods
    - namespaces
    verbs:
    - list
    - watch
  - apiGroups:
    - discovery.k8s.io
    resources:
    - endpointslices
    verbs:
    - list
    - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: vpc-dns
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:vpc-dns
subjects:
- kind: ServiceAccount
  name: vpc-dns
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vpc-dns
  namespace: kube-system
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpc-dns-corefile
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
          lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
          pods insecure
          fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        forward . /etc/resolv.conf {
          prefer_udp
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

### Deploy vpc-dns

```yaml
kind: VpcDns
apiVersion: kubeovn.io/v1
metadata:
  name: test-cjh1
spec:
  vpc: cjh-vpc-1
  subnet: cjh-subnet-1
```

- `vpc`: The VPC name used to deploy the DNS component.
- `subnet`: The subnet name used to deploy the DNS component.

View resource information:

```bash
[root@hci-dev-mst-1 kubeovn]# kubectl get vpc-dns
NAME        ACTIVE   VPC         SUBNET
test-cjh1   false    cjh-vpc-1   cjh-subnet-1
test-cjh2   true     cjh-vpc-1   cjh-subnet-2
```

- `ACTIVE`: if the custom vpc-dns is ready.

### Restrictions

- Only one custom DNS component will be deployed in one VPC;
- When multiple VPC-DNS resources (i.e. different subnets in the same VPC) are configured in one VPC, only one VPC-DNS resource with status `true` will be active, while the others will be `false`;
- When the `true` VPC-DNS is deleted, another `false` VPC-DNS will be deployed.

## Default subnet selection for custom VPC

If the custom VPC is running multiple Subnets, you can specify the default Subnet for that VPC.

```yaml
kind: Vpc
apiVersion: kubeovn.io/v1
metadata:
  name: test-vpc-1
spec:
  namespaces:
  - ns1
  defaultSubnet: test
```

- `defaultSubnet`: Name of the subnet that should be used by custom VPC as the default one.

Please note that it will annotate the VPC namespaces with just one logical switch using `"ovn.kubernetes.io/logical_switch"` annotation.
Any of the new Pods without `"ovn.kubernetes.io/logical_switch"` annotation will be added to the default Subnet.

### Custom VPC Pod supports livenessProbe and readinessProbe

Since the Pods under the custom VPC do not communicate with the network of the node, the probe packets sent by the kubelet cannot reach the Pods in the custom VPC. Kube-OVN uses TProxy to redirect the detection packets sent by kubelet to Pods in the custom VPC to achieve this function.

The configuration method is as follows, add the parameter `--enable-tproxy=true` in DaemonSet `kube-ovn-cni`:

```yaml
spec:
  template:
    spec:
      containers:
      - args:
        - --enable-tproxy=true
```

Restrictions for this feature:

1. When Pods under different VPCs have the same IP under the same node, the detection function fails.
2. Currently, only `tcpSocket` and `httpGet` are supported.
