# 自定义 VPC 内部负载均衡

Kubernetes 提供的 Service 可以用作集群内的负载均衡， 但是在自定义 VPC 模式下，
使用 Service 作为内部负载均衡存在如下几个问题：

1. Service IP 范围为集群资源，所有自定义 VPC 共享，无法重叠。
2. 用户无法按照自己意愿设置内部负载均衡的 IP 地址。

为了解决上述问题，Kube-OVN 在 1.11 引入 `SwitchLBRule` CRD，用户可以设置自定义 VPC 内的内部负载均衡规则。

`SwitchLBRule` 支持以下两种方式设置自定义 VPC 内的内部负载均衡规则。

## `Selector` 自动生成负载均衡规则

通过 `selector` 可以通过 `label` 自动关联 `pod` 配置生成负载均衡规则。

`SwitchLBRule` 样例如下：

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

- `selector`, `sessionAffinity` 和 `port` 使用方式同 Kubernetes Service。

- `vip`：自定义负载均衡的 IP 地址。

- `namespace`：`selector` 所选择 Pod 所在命名空间。

Kube-OVN 会根据 `SwitchLBRule` 定义选择的 Pod 得出 Pod 所在 VPC 并设置对应的 L2 LB。

## `Endpoints` 自定义负载均衡规则

通过 `endpoints` 可以自定义负载均衡规则，用以支持无法通过 `selector` 自动生成负载均衡规则的场景，比如负载均衡后端是 `kubevirt` 创建的 `vm` 。

`SwitchLBRule` 样例如下：

```yaml

apiVersion: kubeovn.io/v1
kind: SwitchLBRule
metadata:
  name:  cjh-slr-nginx
spec:
  vip: 1.1.1.1
  sessionAffinity: ClientIP
  namespace: default
  endpoints:
    - 192.168.0.101
    - 192.168.0.102
    - 192.168.0.103
  ports:
  - name: dns
    port: 8888
    targetPort: 80
    protocol: TCP

```

- `sessionAffinity` 和 `port` 使用方式同 Kubernetes Service。
- `vip`：自定义负载均衡的 IP 地址。
- `namespace`：`selector` 所选择 Pod 所在命名空间。
- `endpoints`：负载均衡后端 IP 列表。

如果同时配置了 `selector` 和 `endpoints`, 会自动忽略 `selector` 配置。

## 健康检查

`OVN` 支持 `IPv4` 的负载平衡器服务终端的运行状况检查。
启用运行状况检查后，负载平衡器会对服务终端的状态进行检测维护，并仅使用运行状况良好的服务终端。

[[Health Checks](https://www.ovn.org/support/dist-docs/ovn-nb.5.html)](<https://www.ovn.org/support/dist-docs/ovn-nb.5.html>)

根据 `ovn` 负载均衡器的运行状况检查，对 `SwitchLBRule` 添加健康检查。在创建 `SwitchLBRule` 的同时，从对应的 `VPC` 和 `subnet` 中获取一个可复用的 `vip` 作为检测端点，并添加对应的 `ip_port_mappings` 和 `load_balancer_health_check` 到对应的负载均衡器上。

- 检测端点 `vip` 会自动在对应的 `subnet` 中判断是否存在，并且与 `subnet` 同名，如果不存在则会自动创建，并且在所有关联的 `SwitchLBRule` 被删除后自动被删除。
- 暂时只支持通过 `Selector` 自动生成的负载均衡规则

### 创建负载均衡规则

```bash

root@server:~# kubectl get po -o wide -n vulpecula
NAME                     READY   STATUS    RESTARTS   AGE     IP          NODE     NOMINATED NODE   READINESS GATES
nginx-78d9578975-f4qn4   1/1     Running   3          4d16h   10.16.0.4   worker   <none>           <none>
nginx-78d9578975-t8tm5   1/1     Running   3          4d16h   10.16.0.6   worker   <none>           <none>

# 创建 slr
root@server:~# cat << END > slr.yaml
apiVersion: kubeovn.io/v1
kind: SwitchLBRule
metadata:
  name:  nginx
  namespace:  vulpecula
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
END
root@server:~# kubectl apply -f slr.yaml
root@server:~# kubectl get slr
NAME              VIP       PORT(S)    SERVICE                       AGE
vulpecula-nginx   1.1.1.1   8888/TCP   default/slr-vulpecula-nginx   3d21h

```

可以看到与 `subnet` 同名的 `vip` 已经被创建。

```bash

# 查看检测端点 vip

root@server:~# kubectl get vip
NAME          NS    V4IP        MAC                 V6IP    PMAC   SUBNET        READY   TYPE
vulpecula-subnet    10.16.0.2   00:00:00:39:95:C1   <nil>          vulpecula-subnet   true   

```

通过命令可以查询到对应的 `Load_Balancer_Health_Check` 和 `Service_Monitor`。

```bash

root@server:~# kubectl ko nbctl list Load_Balancer
_uuid               : 3cbb6d43-44aa-4028-962f-30d2dba9f0b8
external_ids        : {}
health_check        : [5bee3f12-6b54-411c-9cc8-c9def8f67356]
ip_port_mappings    : {"10.16.0.4"="nginx-78d9578975-f4qn4.default:10.16.0.2", "10.16.0.6"="nginx-78d9578975-t8tm5.default:10.16.0.2"}
name                : cluster-tcp-session-loadbalancer
options             : {affinity_timeout="10800"}
protocol            : tcp
selection_fields    : [ip_src]
vips                : {"1.1.1.1:8888"="10.16.0.4:80,10.16.0.6:80"}

root@server:~# kubectl ko nbctl list Load_Balancer_Health_Check
_uuid               : 5bee3f12-6b54-411c-9cc8-c9def8f67356
external_ids        : {switch_lb_subnet=vulpecula-subnet}
options             : {failure_count="3", interval="5", success_count="3", timeout="20"}
vip                 : "1.1.1.1:8888"

root@server:~# kubectl ko sbctl list Service_Monitor
_uuid               : 1bddc541-cc49-44ea-9935-a4208f627a91
external_ids        : {}
ip                  : "10.16.0.4"
logical_port        : nginx-78d9578975-f4qn4.default
options             : {failure_count="3", interval="5", success_count="3", timeout="20"}
port                : 80
protocol            : tcp
src_ip              : "10.16.0.2"
src_mac             : "c6:d4:b8:08:54:e7"
status              : online

_uuid               : 84dd24c5-e1b4-4e97-9daa-13687ed59785
external_ids        : {}
ip                  : "10.16.0.6"
logical_port        : nginx-78d9578975-t8tm5.default
options             : {failure_count="3", interval="5", success_count="3", timeout="20"}
port                : 80
protocol            : tcp
src_ip              : "10.16.0.2"
src_mac             : "c6:d4:b8:08:54:e7"
status              : online

```

此时通过负载均衡 `vip` 可以成功得到服务响应。

```bash

root@server:~# kubectl exec -it -n vulpecula nginx-78d9578975-t8tm5 -- curl 1.1.1.1:8888
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<p><em>Thank you for using nginx.</em></p>
</body>
</html>

```

### 更新负载均衡服务终端

通过删除 `pod` 更新负载均衡器的服务终端。

```bash

kubectl delete po nginx-78d9578975-f4qn4
kubectl get po -o wide -n vulpecula
NAME                     READY   STATUS    RESTARTS   AGE     IP          NODE     NOMINATED NODE   READINESS GATES
nginx-78d9578975-lxmvh   1/1     Running   0          31s     10.16.0.8   worker   <none>           <none>
nginx-78d9578975-t8tm5   1/1     Running   3          4d16h   10.16.0.6   worker   <none>           <none>

```

通过命令可以查询到对应的 `Load_Balancer_Health_Check` 和 `Service_Monitor` 已经发生了响应的变化。

```bash

root@server:~# kubectl ko nbctl list Load_Balancer
_uuid               : 3cbb6d43-44aa-4028-962f-30d2dba9f0b8
external_ids        : {}
health_check        : [5bee3f12-6b54-411c-9cc8-c9def8f67356]
ip_port_mappings    : {"10.16.0.4"="nginx-78d9578975-f4qn4.default:10.16.0.2", "10.16.0.6"="nginx-78d9578975-t8tm5.default:10.16.0.2", "10.16.0.8"="nginx-78d9578975-lxmvh.default:10.16.0.2"}
name                : cluster-tcp-session-loadbalancer
options             : {affinity_timeout="10800"}
protocol            : tcp
selection_fields    : [ip_src]
vips                : {"1.1.1.1:8888"="10.16.0.6:80,10.16.0.8:80"}

root@server:~# kubectl ko nbctl list Load_Balancer_Health_Check
_uuid               : 5bee3f12-6b54-411c-9cc8-c9def8f67356
external_ids        : {switch_lb_subnet=vulpecula-subnet}
options             : {failure_count="3", interval="5", success_count="3", timeout="20"}
vip                 : "1.1.1.1:8888"

root@server:~# kubectl ko sbctl list Service_Monitor
_uuid               : 84dd24c5-e1b4-4e97-9daa-13687ed59785
external_ids        : {}
ip                  : "10.16.0.6"
logical_port        : nginx-78d9578975-t8tm5.default
options             : {failure_count="3", interval="5", success_count="3", timeout="20"}
port                : 80
protocol            : tcp
src_ip              : "10.16.0.2"
src_mac             : "c6:d4:b8:08:54:e7"
status              : online

_uuid               : 5917b7b7-a999-49f2-a42d-da81f1eeb28f
external_ids        : {}
ip                  : "10.16.0.8"
logical_port        : nginx-78d9578975-lxmvh.default
options             : {failure_count="3", interval="5", success_count="3", timeout="20"}
port                : 80
protocol            : tcp
src_ip              : "10.16.0.2"
src_mac             : "c6:d4:b8:08:54:e7"
status              : online

```

删除 `SwitchLBRule`，并确认资源状态，可以看到 `Load_Balancer_Health_Check` 和 `Service_Monitor` 都已经被删除，并且对应的 `vip` 也被删除。

```bash

root@server:~# kubectl delete -f slr.yaml 
switchlbrule.kubeovn.io "vulpecula-nginx" deleted
root@server:~# kubectl get vip
No resources found
root@server:~# kubectl ko sbctl list Service_Monitor
root@server:~# 
root@server:~# kubectl ko nbctl list Load_Balancer_Health_Check
root@server:~# 

```
