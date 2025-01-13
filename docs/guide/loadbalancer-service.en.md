# LoadBalancer Type Service

Kube-OVN supports the implementation of VPC and VPC gateway. For specific configurations, please refer to the [VPC configuration](../vpc/vpc.en.md).

Due to the complexity of using VPC gateways, the implementation based on VPC gateways has been simplified. It supports creating LoadBalancer type Services in the default VPC, allowing access to Services in the default VPC through LoadBalancerIP.

First, make sure the following conditions are met in the environment:

1. Install `multus-cni` and `macvlan cni`。
2. LoadBalancer Service support relies on simplified implementation of VPC gateway code, still utilizing the vpc-nat-gw image and depending on macvlan for multi-interface functionality support.
3. Currently, it only supports configuration in the default VPC. Support for LoadBalancers in custom VPCs can be referred to in the [VPC configuration](../vpc/vpc.en.md).

## Steps to Configure Default VPC LoadBalancer Service

### Enable Feature Flag

Modify the deployment `kube-ovn-controller` under the kube-system namespace and add the parameter `--enable-lb-svc=true` to the `args` section to enable the feature (by default it's set to false).

```yaml
containers:
- args:
  - /kube-ovn/start-controller.sh
  - --default-cidr=10.16.0.0/16
  - --default-gateway=10.16.0.1
  - --default-gateway-check=true
  - --enable-lb-svc=true                  // parameter is set to true
```

### Create NetworkAttachmentDefinition CRD Resource

Refer to the following YAML and create the `net-attach-def` resource:

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: lb-svc-attachment
  namespace: kube-system
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "macvlan",
      "master": "eth0",                            //Physical network card, configure according to the actual situation
      "mode": "bridge"
    }'
```

By default, the physical NIC `eth0` is used to implement the multi-interface functionality. If another physical NIC is needed, modify the `master` value to specify the name of the desired physical NIC.

### Create Subnet

The created Subnet is used to allocate LoadBalancerIP for the LoadBalancer Service, which should normally  be accessible from outside the cluster. An Underlay Subnet can be configured for address allocation.

Refer to the following YAML to create a new subnet:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: attach-subnet
spec:
  protocol: IPv4
  provider: lb-svc-attachment.kube-system          //The provider format is fixed and consists of the Name.Namespace of the net-attach-def resource created in the previous step
  cidrBlock: 172.18.0.0/16
  gateway: 172.18.0.1
  excludeIps:
  - 172.18.0.0..172.18.0.10
```

In the `provider` parameter of the Subnet, `ovn` or `.ovn` suffix is used to indicate that the subnet is managed by Kube-OVN and requires corresponding logical switch records to be created.

If `provider` is neither `ovn` nor ends with `.ovn`, Kube-OVN only provides the IPAM functionality to record IP address allocation without handling business logic for the subnet.

### Create LoadBalancer Service

Refer to the following YAML to create a LoadBalancer Service:

```yaml
apiVersion: v1
kind: Service
metadata:
   annotations:
     lb-svc-attachment.kube-system.kubernetes.io/logical_switch: attach-subnet #Optional
     ovn.kubernetes.io/attachmentprovider: lb-svc-attachment.kube-system #Required
   labels:
     app: dynamic
   name: test-service
   namespace: default
spec:
   loadBalancerIP: 172.18.0.18 #Optional
   ports:
     - name: test
       protocol: TCP
       port: 80
       targetPort: 80
   selector:
     app: dynamic
   sessionAffinity: None
   type: LoadBalancer
```

In the yaml, the annotation `ovn.kubernetes.io/attachmentprovider` is required, and its value is composed of the Name.Namespace of the `net-attach-def` resource created in the first step. This annotation is used to find the `net-attach-def` resources when creating Pods.

The subnet used for multi-interface address allocation can be specified through an annotation. The annotation key format is `net-attach-def` resource's `Name.Namespace.kubernetes.io/logical_switch`. This configuration is `optional` and if LoadBalancerIP address is not specified, addresses will be dynamically allocated from this subnet and filled into the LoadBalancerIP field.

If a static LoadBalancerIP address is required, the `spec.loadBalancerIP` field can be configured. The address must be within the specified subnet's address range.

After creating the Service using the YAML, you can see the Pod startup information in the same namespace as the Service:

```bash
# kubectl get pod
NAME READY STATUS RESTARTS AGE
lb-svc-test-service-6869d98dd8-cjvll 1/1 Running 0 107m
# kubectl get svc
NAME TYPE CLUSTER-IP EXTERNAL-IP PORT(S) AGE
test-service LoadBalancer 10.109.201.193 172.18.0.18 80:30056/TCP 107m
```

When specifying the `service.spec.loadBalancerIP` parameter, it will be assigned to the service's external IP field. If not specified, the parameter will be assigned a random value.

View the YAML output of the test Pod to see the assigned multi-interface addresses:

```bash
# kubectl get pod -o yaml lb-svc-test-service-6869d98dd8-cjvll
apiVersion: v1
kind: Pod
metadata:
   annotations:
     k8s.v1.cni.cncf.io/network-status: |-
       [{
           "name": "kube-ovn",
           "ips": [
               "10.16.0.2"
           ],
           "default": true,
           "dns": {}
       },{
           "name": "default/test-service",
           "interface": "net1",
           "mac": "ba:85:f7:02:9f:42",
           "dns": {}
       }]
     k8s.v1.cni.cncf.io/networks: default/test-service
     k8s.v1.cni.cncf.io/networks-status: |-
       [{
           "name": "kube-ovn",
           "ips": [
               "10.16.0.2"
           ],
           "default": true,
           "dns": {}
       },{
           "name": "default/test-service",
           "interface": "net1",
           "mac": "ba:85:f7:02:9f:42",
           "dns": {}
       }]
     ovn.kubernetes.io/allocated: "true"
     ovn.kubernetes.io/cidr: 10.16.0.0/16
     ovn.kubernetes.io/gateway: 10.16.0.1
     ovn.kubernetes.io/ip_address: 10.16.0.2
     ovn.kubernetes.io/logical_router: ovn-cluster
     ovn.kubernetes.io/logical_switch: ovn-default
     ovn.kubernetes.io/mac_address: 00:00:00:45:F4:29
     ovn.kubernetes.io/pod_nic_type: veth-pair
     ovn.kubernetes.io/routed: "true"
     test-service.default.kubernetes.io/allocated: "true"
     test-service.default.kubernetes.io/cidr: 172.18.0.0/16
     test-service.default.kubernetes.io/gateway: 172.18.0.1
     test-service.default.kubernetes.io/ip_address: 172.18.0.18
     test-service.default.kubernetes.io/logical_switch: attach-subnet
     test-service.default.kubernetes.io/mac_address: 00:00:00:AF:AA:BF
     test-service.default.kubernetes.io/pod_nic_type: veth-pair
```

Check the service information:

```bash
# kubectl get svc -o yaml test-service
apiVersion: v1
kind: Service
metadata:
   annotations:
     kubectl.kubernetes.io/last-applied-configuration: |
       {"apiVersion":"v1","kind":"Service","metadata":{"annotations":{"test-service.default.kubernetes.io/logical_switch":"attach-subnet"},"labels ":{"app":"dynamic"},"name":"test-service","namespace":"default"},"spec":{"ports":[{"name":"test", "port":80,"protocol":"TCP","targetPort":80}],"selector":{"app":"dynamic"},"sessionAffinity":"None","type":"LoadBalancer "}}
     ovn.kubernetes.io/vpc:ovn-cluster
     test-service.default.kubernetes.io/logical_switch: attach-subnet
   creationTimestamp: "2022-06-15T09:01:58Z"
   labels:
     app: dynamic
   name: test-service
   namespace: default
   resourceVersion: "38485"
   uid: 161edee1-7f6e-40f5-9e09-5a52c44267d0
spec:
   allocateLoadBalancerNodePorts: true
   clusterIP: 10.109.201.193
   clusterIPs:
   - 10.109.201.193
   externalTrafficPolicy: Cluster
   internalTrafficPolicy: Cluster
   ipFamilies:
   - IPv4
   ipFamilyPolicy: SingleStack
   ports:
   - name: test
     nodePort: 30056
     port: 80
     protocol: TCP
     targetPort: 80
   selector:
     app: dynamic
   sessionAffinity: None
   type: LoadBalancer
status:
   loadBalancer:
     ingress:
     - ip: 172.18.0.18
```

## Testing LoadBalancerIP access

Refer to the following YAML to create a test Pod that serves as the Endpoints for the Service:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: dynamic
  name: dynamic
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dynamic
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: dynamic
    spec:
      containers:
      - image: docker.io/library/nginx:alpine
        imagePullPolicy: IfNotPresent
        name: nginx
      dnsPolicy: ClusterFirst
      restartPolicy: Always
```

Under normal circumstances, the provided subnet addresses should be accessible from outside the cluster. To verify, access the Service's `LoadBalancerIP:Port` from within the cluster and check if the access is successful.

```bash
# curl 172.18.0.11:80
<html>
<head>
        <title>Hello World!</title>
        <link href='//fonts.googleapis.com/css?family=Open+Sans:400,700' rel='stylesheet' type='text/css'>
        <style>
        body {
                background-color: white;
                text-align: center;
                padding: 50px;
                font-family: "Open Sans","Helvetica Neue",Helvetica,Arial,sans-serif;
        }
        #logo {
                margin-bottom: 40px;
        }
        </style>
</head>
<body>
                <h1>Hello World!</h1>
                                <h3>Links found</h3>
        <h3>I am on  dynamic-7d8d7874f5-hsgc4</h3>
        <h3>Cookie                  =</h3>
                                        <b>KUBERNETES</b> listening in 443 available at tcp://10.96.0.1:443<br />
                                                <h3>my name is hanhouchao!</h3>
                        <h3> RequestURI='/'</h3>
</body>
</html>
```

Enter the Pod created by the Service and check the network information:

```bash
# ip a
4: net1@if62: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether ba:85:f7:02:9f:42 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.18.0.18/16 scope global net1
       valid_lft forever preferred_lft forever
    inet6 fe80::b885:f7ff:fe02:9f42/64 scope link
       valid_lft forever preferred_lft forever
36: eth0@if37: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1400 qdisc noqueue state UP group default
    link/ether 00:00:00:45:f4:29 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.16.0.2/16 brd 10.16.255.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe45:f429/64 scope link
       valid_lft forever preferred_lft forever

# ip rule
0: from all lookup local
32764: from all iif eth0 lookup 100
32765: from all iif net1 lookup 100
32766: from all lookup main
32767: from all lookup default

# ip route show table 100
default via 172.18.0.1 dev net1
10.109.201.193 via 10.16.0.1 dev eth0
172.18.0.0/16 dev net1 scope link

# iptables -t nat -L -n -v
Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 DNAT       tcp  --  *      *       0.0.0.0/0            172.18.0.18          tcp dpt:80 to:10.109.201.193:80

Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 MASQUERADE  all  --  *      *       0.0.0.0/0            10.109.201.193
```

### Configure the `nodeSelector` for the LB Service Pod

You can specify the node where the LoadBalancer service gateway Pod is deployed by adjusting the `nodeSelector` in the `ovn-vpc-nat-config` ConfigMap.

```yaml
apiVersion: v1
data:
  image: docker.io/kubeovn/vpc-nat-gateway:v1.14.0
  nodeSelector: |
    kubernetes.io/hostname: kube-ovn-control-plane
    kubernetes.io/os: linux
kind: ConfigMap
metadata:
  name: ovn-vpc-nat-config
  namespace: kube-system
