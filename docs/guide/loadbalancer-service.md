
Kube-OVN已经支持了Vpc和Vpc网关的实现，具体配置可以参考 [Vpc配置](https://github.com/kubeovn/kube-ovn/blob/master/docs/vpc.md)。

由于Vpc网关的使用比较复杂，基于Vpc网关的实现做了简化，支持在默认Vpc下创建LoadBalancer类型的Service，实现通过LoadBalancerIP来访问默认Vpc下的Service。

首先确认环境上满足以下条件：
1. 安装了multus-cni和macvlan cni。
2. LoadBalancer Service的支持，是对Vpc网关代码进行简化实现的，仍然使用vpc-nat-gw的镜像，依赖macvlan提供多网卡功能支持。
3. 目前只支持在默认Vpc配置，自定义Vpc下的LoadBalancer支持可以参考Vpc的文档[Vpc配置](https://github.com/kubeovn/kube-ovn/blob/master/docs/vpc.md)。

# 默认Vpc LoadBalancer Service配置步骤
## 开启特性开关
修改kube-system namespace下的deployment kube-ovn-controller，在args中增加参数 --enable-lb-svc=true，开启功能开关，该参数默认为false。

## 创建subnet
创建的Subnet，用于给LoadBalancer Service分配LoadBalancerIP，该地址正常情况下在集群外应该可以访问到。可以配置underlay subnet用于地址分配。

使用以下yaml，创建新子网

```
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: attach-subnet
spec:
  protocol: IPv4
  provider: lb-svc                      # provider不要填写ovn，或者以.ovn为结尾
  cidrBlock: 172.18.0.0/16
  gateway: 172.18.0.1
  excludeIps:
  - 172.18.0.0..172.18.0.10
```
subnet中provider参数为ovn或者以.ovn为后缀结束，表示该子网是由Kube-OVN管理使用，需要对应创建logical-switch记录。
provider非ovn或者不是以.ovn为后缀结束，则Kube-OVN只提供IPAM功能，记录IP地址分配情况，不对子网做业务逻辑处理。

## 创建LoadBalancer Service
使用以下yaml，创建LoadBalancer Service

```
apiVersion: v1
kind: Service
metadata:
  annotations:
    test-service.default.kubernetes.io/logical_switch: attach-subnet    #必须
    ovn.kubernetes.io/attchmentnic: eth1                                #可选
  labels:
    app: dynamic
  name: test-service
  namespace: default
spec:
  loadBalancerIP: 172.18.0.18                                           #可选
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
在yaml中，通过annotation指定多网卡地址分配使用的子网，annotation key格式为 svcName.svcNamespace.kubernetes.io/logical_switch。该配置为必须选项，在没有指定LoadBalancerIP地址的情况下，将从该子网动态分配地址，填充到LoadBalancerIP字段。

如果需要静态配置LoadBalancerIP地址，可以配置spec.loadBalancerIP 字段，该地址需要在指定子网的地址范围内。

默认情况下，通过物理网卡eth0来实现多网卡功能，如果需要使用其他物理网卡，可以通过ovn.kubernetes.io/attchmentnic annotation来指定使用的物理网卡名称。

在执行yaml创建Service后，在Service同Namespace下，可以看到Pod启动信息
```
apple@bogon svc % kubectl get pod
NAME                                      READY   STATUS    RESTARTS   AGE
lb-svc-test-service-6869d98dd8-cjvll      1/1     Running   0          107m
apple@bogon svc % kubectl get svc
NAME              TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
test-service      LoadBalancer   10.109.201.193   172.18.0.11   80:30056/TCP   107m
apple@bogon svc %
```
查看测试Pod的yaml输出，存在多网卡分配的地址信息
```
apple@bogon svc % kubectl get pod -o yaml lb-svc-test-service-6869d98dd8-cjvll
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
    test-service.default.kubernetes.io/ip_address: 172.18.0.11
    test-service.default.kubernetes.io/logical_switch: attach-subnet
    test-service.default.kubernetes.io/mac_address: 00:00:00:AF:AA:BF
    test-service.default.kubernetes.io/pod_nic_type: veth-pair
```

查看Service的信息
```
apple@bogon svc % kubectl get svc -o yaml test-service
apiVersion: v1
kind: Service
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"Service","metadata":{"annotations":{"test-service.default.kubernetes.io/logical_switch":"attach-subnet"},"labels":{"app":"dynamic"},"name":"test-service","namespace":"default"},"spec":{"ports":[{"name":"test","port":80,"protocol":"TCP","targetPort":80}],"selector":{"app":"dynamic"},"sessionAffinity":"None","type":"LoadBalancer"}}
    ovn.kubernetes.io/vpc: ovn-cluster
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
    - ip: 172.18.0.11
```

## 测试LoadBalancerIP访问

创建测试Pod，作为Service的Endpoints 提供服务。
```
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
      - image: qaimages:helloworld
        imagePullPolicy: IfNotPresent
        name: qaimages
      dnsPolicy: ClusterFirst
      restartPolicy: Always
```


正常情况下，提供的子网地址，在集群外应该可以正常访问到。为了简单验证，在集群内访问Service 的 LoadBalancerIP:Port，查看是否正常访问成功。
```
root@kube-ovn-control-plane:/kube-ovn# curl 172.18.0.11:80
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

进入Service创建的Pod，查看网络的信息
```
bash-5.1# ip a
4: net1@if62: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether ba:85:f7:02:9f:42 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.18.0.11/16 scope global net1
       valid_lft forever preferred_lft forever
    inet6 fe80::b885:f7ff:fe02:9f42/64 scope link
       valid_lft forever preferred_lft forever
36: eth0@if37: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1400 qdisc noqueue state UP group default
    link/ether 00:00:00:45:f4:29 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.16.0.2/16 brd 10.16.255.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::200:ff:fe45:f429/64 scope link
       valid_lft forever preferred_lft forever
bash-5.1#
bash-5.1# ip rule
0:	from all lookup local
32764:	from all iif eth0 lookup 100
32765:	from all iif net1 lookup 100
32766:	from all lookup main
32767:	from all lookup default
bash-5.1#
bash-5.1# ip route show table 100
default via 172.18.0.1 dev net1
10.109.201.193 via 10.16.0.1 dev eth0
172.18.0.0/16 dev net1 scope link
bash-5.1#
bash-5.1# iptables -t nat -L -n -v
Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 DNAT       tcp  --  *      *       0.0.0.0/0            172.18.0.11          tcp dpt:80 to:10.109.201.193:80

Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 MASQUERADE  all  --  *      *       0.0.0.0/0            10.109.201.193
bash-5.1#
```
