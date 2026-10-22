# 配置监控和面板

Kube-OVN 可以将网络控制平面信息以及网络数据平面质量信息指标以 Prometheus 所支持的格式对外输出。

我们使用 [kube-prometheus](https://github.com/coreos/kube-prometheus) 所提供的 CRD 来定义相应的 Prometheus 监控规则。
用户需要预先安装 kube-prometheus 来启用相关的 CRD。Kube-OVN 所支持的全部监控指标请参考 [Kube-OVN 监控指标](../reference/metrics.md)。

## 安装 Prometheus Monitor

Kube-OVN 使用 Prometheus Monitor CRD 来管理监控输出：

```bash
# 网络质量相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/pinger-monitor.yaml
# kube-ovn-controller 相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/controller-monitor.yaml
# kube-ovn-cni 相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/cni-monitor.yaml
# ovn 相关监控指标
kubectl apply -f https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/monitoring/ovn-monitor.yaml
```

Prometheus 拉取监控时间间隔默认为 15s，如果需要调整需要修改 yaml 中的 `interval` 字段。

## 加载 Grafana 面板

Kube-OVN 还提供了预先定义好的 Grafana Dashboard 展示控制平面和数据平面相关信息。

下载对应 Dashboard 模板：

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

`kube-ovn-controller` 运行状况相关面板：

![controller](../static/controller-grafana.png)

`kube-ovn-pinger` 网络质量相关面板：

![pinger](../static/pinger-grafana.png)

`kube-ovn-cni` 运行状况相关面板：

![cni](../static/cni-grafana.png)
