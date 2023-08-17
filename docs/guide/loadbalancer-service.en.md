# LoadBalancer Type Service

Kube-OVN already supports the implementation of VPC and VPC gateway. For specific configration, please refer to [VPC 配置](vpc.en.md)。

Since the use of the VPC gateway is complicated, the implementation based on the VPC gateway has been simplified. It supports creating a `LoadBalancer` type of Service under the default VPC, and accessing the Service under the default VPC through the LoadBalancerIP.

The environment must meets the following conditions:

1. Install `multus-cni` and `macvlan cni`。
2. The support of LoadBalancer Service is a simplified implementation of the VPC gateway code. It still uses the image of `vpc-nat-gw` and relies on macvlan to provide multi-network card function support.
3. Currently it only supports the `default VPC` configuration. For LoadBalancer support under custom VPC, please refer to the VPC document [VPC 配置](vpc.en.md).

## Default VPC LoadBalancer Service configuration steps

### 开启特性开关

Modify the deployment `kube-ovn-controller` under the kube-system namespace, add the parameter `--enable-lb-svc=true` in `args`, and enable the function switch, which defaults to false.

```yaml
containers:
- args:
  - /kube-ovn/start-controller.sh
  - --default-cidr=10.16.0.0/16
  - --default-gateway=10.16.0.1
  - --default-gateway-check=true
  - --enable-lb-svc=true                  // parameter is set to true
```

### Create NetworkAttachmentDefinition CRD resource

Create a `net-attach-def` resource by applying the following yaml:

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

By default, the physical network card `eth0` is used to implement the multi-network card function. If you need to use other physical network cards, you can specify the name of the physical network card to be used by modifying the value of `master`.

### Create Subnet

The created Subnet is used to assign LoadBalancerIP to LoadBalancer Service, which should be accessible outside the cluster under normal circumstances. An Underlay Subnet can be configured for address assignment.

Create a new subnet by applying the following yaml:

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

The `provider` parameter in Subnet ends with `ovn` or `.ovn` as the suffix, indicating that the subnet is managed and used by Kube-OVN, and a `logical switch` record needs to be created accordingly.

`provider` does not end with `ovn` or does not end with `.ovn`, Kube-OVN only provides the IPAM function, records the IP address allocation, and does not perform business logic processing on the subnet.

### Create LoadBalancer Service

Create a LoadBalancer Service with reference to the following yaml:

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

In yaml, the annotation `ovn.kubernetes.io/attachmentprovider` is required, and its value is composed of the Name.Namespace of the `net-attach-def` resource created in the first step. This annotation is used to look for `net-attach-def` resources when creating Pods.

The subnet used for multi-NIC address allocation can be specified through annotation. The annotation key format is `Name.Namespace.kubernetes.io/logical_switch` of the net-attach-def resource. This configuration is an `optional` option. If no LoadBalancerIP address is specified, an address will be dynamically allocated from this subnet to fill in the LoadBalancerIP field.

If you need to statically configure the LoadBalancerIP address, you can configure the `spec.loadBalancerIP` field, and the address needs to be within the address range of the specified subnet.

After executing yaml to create the Service, under the same Namespace as the Service, you can see the Pod startup information:

```bash
# kubectl get pod
NAME READY STATUS RESTARTS AGE
lb-svc-test-service-6869d98dd8-cjvll 1/1 Running 0 107m
# kubectl get svc
NAME TYPE CLUSTER-IP EXTERNAL-IP PORT(S) AGE
test-service LoadBalancer 10.109.201.193 172.18.0.18 80:30056/TCP 107m
```

When the `service.spec.loadBalancerIP` parameter is specified, the parameter is finally assigned to the service external-ip field. If not specified, this parameter is randomly assigned a value.

View the yaml output of the test Pod, and there is address information allocated by multiple NICs:

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

## Test LoadBalancerIP access

Referring to the following yaml, create a test Pod to serve as the Endpoints of the Service:

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
```
