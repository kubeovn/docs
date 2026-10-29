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

## 使用 kube-ovn-v2 Helm Chart 部署监控资源

`kube-ovn-v2` Helm Chart 可以创建内置的 `PrometheusRule` 和 Grafana Dashboard ConfigMap。两项功能默认关闭，需要先安装 Prometheus Operator CRD；Dashboard ConfigMap 还需要集群中的 kube-prometheus-stack Grafana sidecar 监听 `grafana_dashboard: "1"` 标签。

下面的配置会启用两项功能，并把资源放到 `monitoring` 命名空间：

```yaml
prometheusRule:
  enabled: true
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
grafanaDashboards:
  enabled: true
  namespace: monitoring
  datasource: Prometheus
```

安装或升级时传入该文件：

```bash
helm upgrade --install kube-ovn oci://ghcr.io/kubeovn/charts/kube-ovn-v2 \
  --namespace kube-system \
  --values monitoring-values.yaml
```

`prometheusRule` 包含 Kube-OVN 的基础告警规则。告警依赖控制器、OVN monitor、pinger 和 agent 的指标采集；可以通过 Chart 中各组件的 `serviceMonitor.enabled` 开启采集，也可以配置外部抓取。可以使用 `prometheusRule.additionalGroups` 追加符合 `PrometheusRule.spec.groups[]` 格式的自定义规则。

`grafanaDashboards.datasource` 必须使用只包含字母、数字、点、下划线或连字符的 Prometheus 数据源名称，默认值为 `Prometheus`。Chart 会把内置 Dashboard 中的 `${DS_PROMETHEUS}` 占位符替换为该名称。

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
