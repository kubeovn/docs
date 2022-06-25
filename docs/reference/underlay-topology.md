## 流量拓扑

### 通过 Pod IP 访问

#### 同节点同子网

内部逻辑交换机直接交换数据包，不进入外部网络。

![同节点同子网](../static/underlay-traffic-1.png)

#### 跨节点同子网

数据包经由节点网卡进入外部交换机，由外部交换机进行交换。

![跨节点同子网](../static/underlay-traffic-2.png)

#### 同节点不同子网

数据包经由节点网卡进入外部网络，由外部交换机及路由器进行交换和路由转发。

![同节点不同子网](../static/underlay-traffic-3.png)

> 此处 br-provider-1 和 br-provider-2 可以是同一个 OVS 网桥，即多个不同子网可以使用同一个 Provider Network。

#### 跨节点不同子网

数据包经由节点网卡进入外部网络，由外部交换机及路由器进行交换和路由转发。

![跨节点不同子网](../static/underlay-traffic-4.png)

#### 外部访问

数据包经由节点网卡进入外部网络，由外部交换机及路由器进行交换和路由转发。

![外部访问](../static/underlay-traffic-5.png)

> 节点与 Pod 之间的通信大体上也遵循此逻辑。

#### 总览

![总览](../static/underlay-traffic-6.png)

#### VLAN 总览

![VLAN 总览](../static/underlay-traffic-7.png)

### 通过 Service IP 访问

Kube-OVN 为每个 Kubernetes Service 在每个子网的逻辑交换机上配置了负载均衡。当 Pod 通过访问 Service IP 访问其它 Pod 时，会构造一个目的地址为 Service IP、目的 MAC 地址为网关 MAC 地址的网络包。网络包进入逻辑交换机后，负载均衡会对网络包进行拦截和 DNAT 处理，将目的 IP 和端口修改为 Service 对应的某个 Endpoint 的 IP 和端口。由于逻辑交换机并未修改网络包的二层目的 MAC 地址，网络包在进入外部交换机后仍然会送到外部网关，此时需要外部网关对网络包进行转发。

#### 同节点同子网

![同节点同子网](../static/underlay-traffic-8.png)

#### 同节点不同子网

![同节点不同子网](../static/underlay-traffic-9.png)
