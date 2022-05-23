# 配置监控和面板

Kube-OVN 可以将网络控制平面信息以及网络数据平面质量信息指标以 Prometheus 所支持的格式对外暴露。

我们使用 [kube-prometheus](https://github.com/coreos/kube-prometheus) 所提供的 CRD 来定义相应的 Prometheus 监控规则。
用户需要预先安装 kube-prometheus 来启用相关的 CRD。

## 安装 Prometheus Monitor

```bash
# 网咯质量相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/pinger-monitor.yaml
# kube-ovn-controller 相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/controller-monitor.yaml
# kube-ovn-cni 相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/cni-monitor.yaml
# ovn 相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/ovn-monitor.yaml
```

## 加载 Grafana 面板
Kube-OVN 还提供了预先定义好的 Grafana Dashboard 展示控制平面和数据平面相关信息。

下载对应 Dashboard 模板
```bash
# 网络质量相关面板
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/pinger-grafana.json
# kube-ovn-controller 相关面板
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/controller-grafana.json
# kube-ovn-cni 相关面板
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/cni-grafana.json
# ovn 相关面板
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/ovn-grafana.json
# ovs 相关面板
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/ovs-grafana.json
```

在 Grafana 中导入模板，并将数据源设置为对应的 Prometheus 即可看到如下 Dashboard：

![controller](../static/controller-grafana.png)
![pinger](../static/pinger-grafana.png)
![cni](../static/cni-grafana.png)
