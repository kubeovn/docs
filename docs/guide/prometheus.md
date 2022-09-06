# 配置原生 Prometheus 获取监控数据

Kube-OVN 提供了丰富的监控数据，用于 OVN/OVS 健康状态检查，以及容器网络和主机网络的连通性检查。Kube-OVN 配置了 ServiceMonitor，可以用于 Prometheus 动态获取监控指标。

在某些情况下，只安装了 Prometheus Server，没有安装其他的组件，可以通过修改 Prometheus 的配置，动态获取集群环境的监控数据。

## Prometheus 配置

以下的配置文档，参考自 [Prometheus 服务发现](https://yunlzheng.gitbook.io/prometheus-book/part-iii-prometheus-shi-zhan/readmd/service-discovery-with-kubernetes)。

### 权限配置

Prometheus 部署在集群内，需要通过 k8s apiserver 来访问集群内的资源，从而实现查询业务的监控数据。

参考以下 yaml，配置 Prometheus 需要的权限：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups:
  - extensions
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: default
```

### Prometheus 配置文件

Prometheus 的启动，依赖于配置文件 prometheus.yml，可以将该文件内容配置在 ConfigMap 内，动态挂载到 Pod 中。

参考以下 yaml，创建 Prometheus 使用的 ConfigMap 文件：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |-
    global:
      scrape_interval:     15s 
      evaluation_interval: 15s
    scrape_configs:
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']

    - job_name: 'kubernetes-nodes'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: node

    - job_name: 'kubernetes-service'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: service

    - job_name: 'kubernetes-endpoints'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: endpoints

    - job_name: 'kubernetes-ingress'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: ingress

    - job_name: 'kubernetes-pods'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: pod
```

Prometheus 提供了基于角色查询 Kubernetes 资源监控的操作，具体配置可以查看官方文档 
[kubernetes_sd_config](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#kubernetes_sd_config)。

在 Kubernetes 集群中，Prometheus 支持查询监控指标的角色包含 node、service、pod、endpoints 和 ingress。在 ConfigMap 配置文件中给出了以上全部资源的监控查询配置示例，可以根据需要选择配置。

### Prometheus 部署

参考以下 yaml 文件，部署 Prometheus Server：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: prometheus
  name: prometheus
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      serviceAccount: prometheus
      containers:
      - image: prom/prometheus:latest
        imagePullPolicy: IfNotPresent
        name: prometheus
        command:
        - "/bin/prometheus"
        args:
        - "--config.file=/etc/prometheus/prometheus.yml"
        ports:
        - containerPort: 9090
          protocol: TCP
        volumeMounts:
        - mountPath: "/etc/prometheus"
          name: prometheus-config
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
```

在部署完 Prometheus 之后，参考以下 yaml 文件，部署 Prometheus Service：

```yaml
kind: Service
apiVersion: v1
metadata:
  name: prometheus
  namespace: default
  labels:
    name: prometheus
spec:
  ports:
    - name: test
      protocol: TCP
      port: 9090
      targetPort: 9090
  type: NodePort
  selector:
    app: prometheus
  sessionAffinity: None
```

将 Prometheus 通过 NodePort 暴露后，即可通过节点来访问 Prometheus。

## Prometheus 监控数据验证

查看环境上 Prometheus 相关的信息：

```bash
# kubectl get svc 
NAME         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
kubernetes   ClusterIP   10.4.0.1       <none>        443/TCP          8d
prometheus   NodePort    10.4.102.222   <none>        9090:32611/TCP   8d
# kubectl get pod -o wide
NAME                          READY   STATUS    RESTARTS   AGE    IP          NODE              NOMINATED NODE   READINESS GATES
prometheus-7544b6b84d-v9m8s   1/1     Running   0          3d5h   10.3.0.7    192.168.137.219   <none>           <none>
# kubectl get endpoints -o wide
NAME         ENDPOINTS                                                        AGE
kubernetes   192.168.136.228:6443,192.168.136.232:6443,192.168.137.219:6443   8d
prometheus   10.3.0.7:9090                                                    8d
```

通过 NodePort 访问 Prometheus，查看 Status/Service Discovery 动态查询到的数据：

![](../static/prometheus-service-discovery.png)

可以看到当前可以查询到集群上全部的 Service 数据信息。

### 配置查询指定的资源

以上的 ConfigMap 配置中，没有添加过滤条件，查询了所有的资源数据。如果只需要某个角色的资源数据，则可以添加过滤条件。

以 Service 为例，修改 ConfigMap 内容，只查询关心的 Service 监控数据。

```yaml
    - job_name: 'kubernetes-service'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: service
      relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: "keep"
        regex: "true"
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_service_name]
        target_label: kubernetes_service_name
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: "(.+)"
```
Service 默认监控路径为 /metrics。如果 Service 提供的监控指标是其他的路径，可以通过给 Service 添加 annotation `prometheus.io/path` 来指定采集路径。

应用以上 yaml，更新 ConfigMap 信息，重建 Prometheus Pod，使配置生效。

查看 kube-system Namespace 下的 Service 信息：
```bash
# kubectl get svc -n kube-system
NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)                  AGE
kube-dns              ClusterIP   10.4.0.10      <none>        53/UDP,53/TCP,9153/TCP   13d
kube-ovn-cni          ClusterIP   10.4.228.60    <none>        10665/TCP                13d
kube-ovn-controller   ClusterIP   10.4.172.213   <none>        10660/TCP                13d
kube-ovn-monitor      ClusterIP   10.4.242.9     <none>        10661/TCP                13d
kube-ovn-pinger       ClusterIP   10.4.122.52    <none>        8080/TCP                 13d
ovn-nb                ClusterIP   10.4.80.213    <none>        6641/TCP                 13d
ovn-northd            ClusterIP   10.4.126.234   <none>        6643/TCP                 13d
ovn-sb                ClusterIP   10.4.216.249   <none>        6642/TCP                 13d
```

给 Service 添加 annotation `prometheus.io/scrape="true"`：

```bash
# kubectl annotate svc -n kube-system kube-ovn-cni  prometheus.io/scrape=true
service/kube-ovn-cni annotated
# kubectl annotate svc -n kube-system kube-ovn-controller  prometheus.io/scrape=true
service/kube-ovn-controller annotated
# kubectl annotate svc -n kube-system kube-ovn-monitor  prometheus.io/scrape=true
service/kube-ovn-monitor annotated
# kubectl annotate svc -n kube-system kube-ovn-pinger  prometheus.io/scrape=true
service/kube-ovn-pinger annotated
```

查看配置后的 Service 信息：

```bash
# kubectl get svc -o yaml -n kube-system kube-ovn-controller
apiVersion: v1
kind: Service
metadata:
  annotations:
    helm.sh/chart-version: v3.10.0-alpha.55
    helm.sh/original-name: kube-ovn-controller
    ovn.kubernetes.io/vpc: ovn-cluster
    prometheus.io/scrape: "true"                        // 添加的 annotation
  labels:
    app: kube-ovn-controller
  name: kube-ovn-controller
  namespace: kube-system
spec:
  clusterIP: 10.4.172.213
  clusterIPs:
  - 10.4.172.213
  internalTrafficPolicy: Cluster
  ipFamilies:
  - IPv4
  ipFamilyPolicy: SingleStack
  ports:
  - name: metrics
    port: 10660
    protocol: TCP
    targetPort: 10660
  selector:
    app: kube-ovn-controller
  sessionAffinity: None
  type: ClusterIP
status:
  loadBalancer: {}
```

查看 Prometheus Status Targets 信息，可以看到只有添加了 annotation 的 Service 被过滤出来：
![](../static/prometheus-filter-service.png)

更多关于 relabel 添加过滤参数的信息，可以参考 [Prometheus-Relabel](https://godleon.github.io/blog/Prometheus/Prometheus-Relabel/)。
