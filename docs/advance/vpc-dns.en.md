# Custom VPC DNS

Due to the isolation of the user-defined VPC and the default VPC network, the coredns deployed in the default VPC cannot be accessed from within the custom VPC. If you wish to use the intra-cluster domain name resolution capability provided by Kubernetes within your custom VPC, you can refer to this document and utilize the vpc-dns CRD to do so.

This CRD eventually deploys a coredns that has two NICs, one in the user-defined VPC and the other in the default VPC to enable network interoperability and provide an internal load balancing within the custom VPC through the [custom VPC internal load balancing](./vpc-internal-lb.en.md).

## Deployment of vpc-dns dependent resources

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

In addition to the above resources, the feature relies on the nat-gw-pod image for routing configuration.

## Configuring Additional Network

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

## Configuring Configmap for vpc-dns

Create a configmap under the kube-system namespace to configure the vpc-dns usage parameters that will be used later to start the vpc-dns function:

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

* `enable-vpc-dns`：enable vpc dns feature, true as default
* `coredns-image`：dns deployment image. Defaults to the clustered coredns deployment version
* `coredns-vip`：The vip that provides lb services for coredns.
* `coredns-template`：The URL where the coredns deployment template is located. defaults to the current version of the ovn directory. `coredns-template.yaml` default is `https://raw.githubusercontent.com/kubeovn/kube-ovn/<kube-ovn version>/yamls/coredns-template.yaml`.
* `nad-name`：Configured network-attachment-definitions Resource name.
* `nad-provider`：The name of the provider to use.
* `k8s-service-host`：The ip used for coredns to access the k8s apiserver service, defaults to the apiserver address within the cluster.
* `k8s-service-port`：The port used for coredns to access the k8s apiserver service, defaults to the apiserver port within the cluster.

## Deploying vpc-dns

configure vpc-dns yaml：

```yaml
kind: VpcDns
apiVersion: kubeovn.io/v1
metadata:
  name: test-cjh1
spec:
  vpc: cjh-vpc-1
  subnet: cjh-subnet-1
  replicas: 2
```

* `vpc` ： The name of the vpc used to deploy the dns component.
* `subnet`：Sub-name for deploying dns components.
* `replicas`: vpc dns deployment replicas

View information about deployed resources:

```bash
# kubectl get vpc-dns
NAME        ACTIVE   VPC         SUBNET   
test-cjh1   false    cjh-vpc-1   cjh-subnet-1   
test-cjh2   true     cjh-vpc-1   cjh-subnet-2 
```

ACTIVE : true Customized dns component deployed, false No deployment.

Restrictions: only one custom dns component will be deployed under a VPC

* When multiple vpc-dns resources are configured under a VPC (i.e., different subnets for the same VPC), only one vpc-dns resource is in the state `true``, and the others are`fasle`.
* When the `true` vpc-dns is removed, the other `false` vpc-dns will be obtained for deployment.

## Validate deployment results

To view vpc-dns Pod status, use label app=vpc-dns to view all vpc-dns pod status:

```bash
# kubectl -n kube-system get pods -l app=vpc-dns
NAME                                 READY   STATUS    RESTARTS   AGE
vpc-dns-test-cjh1-7b878d96b4-g5979   1/1     Running   0          28s
vpc-dns-test-cjh1-7b878d96b4-ltmf9   1/1     Running   0          28s
```

View switch lb rule status information:

```bash
# kubectl -n kube-system get slr
NAME                VIP         PORT(S)                  SERVICE                             AGE
vpc-dns-test-cjh1   10.96.0.3   53/UDP,53/TCP,9153/TCP   kube-system/slr-vpc-dns-test-cjh1   113s
```

Go to the Pod under this VPC and test the dns resolution:

```bash
nslookup kubernetes.default.svc.cluster.local 10.96.0.3
```

The subnet where the switch lb rule under this VPC is located and the pods under other subnets under the same VPC can be resolved.
