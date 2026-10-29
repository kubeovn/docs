# 配置监控和面板

Kube-OVN 可以将网络控制平面信息以及网络数据平面质量信息指标以 Prometheus 所支持的格式对外输出。

我们使用 [kube-prometheus](https://github.com/coreos/kube-prometheus) 所提供的 CRD 来定义相应的 Prometheus 监控规则。
用户需要预先安装 kube-prometheus 来启用相关的 CRD。Kube-OVN 所支持的全部监控指标请参考 [Kube-OVN 监控指标](../reference/metrics.md)。

## 安装 ServiceMonitor

Kube-OVN 使用 `ServiceMonitor` CRD 来管理监控输出：

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

`kube-ovn-v2` Helm Chart 可以创建内置的 `PrometheusRule` 和 Grafana Dashboard ConfigMaps。两项功能默认关闭。请先安装 Prometheus Operator CRDs。

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

`prometheusRule.namespace` 和 `grafanaDashboards.namespace` 为空时，会回退到 `.Values.namespace`。示例中的 `monitoring` 命名空间必须预先存在；`helm --namespace kube-system` 只指定 Helm release 的命名空间，不会创建这个 override 命名空间。四个组件的 `ServiceMonitor` 仍由各组件在 Chart 命名空间（`.Values.namespace`）中创建。

安装或升级时传入该文件：

```bash
helm upgrade --install kube-ovn oci://ghcr.io/kubeovn/charts/kube-ovn-v2 \
  --namespace kube-system \
  --values monitoring-values.yaml
```

`prometheusRule` 包含 controller、pinger、subnet 和 OVSDB 范围的基础告警规则。大多数规则依赖抓取 controller、OVN monitor、pinger 和 agent 暴露的指标：可以开启以下四个 ServiceMonitor 开关：`controller.serviceMonitor.enabled`、`monitor.serviceMonitor.enabled`、`pinger.serviceMonitor.enabled` 和 `agent.serviceMonitor.enabled`；也可以配置外部抓取，但必须提供相同的 job 和 metric labels。没有这些抓取时，依赖抓取的告警不会触发。

`KubeOvnControllerAbsent` 使用 `absent(up{job="kube-ovn-controller"})`，即使没有任何 target，也会在持续约 15m 后触发。在尚未接入抓取时，请在 Alertmanager 中 silence/inhibit 该告警，或关闭 `prometheusRule.enabled`。还可以使用 `prometheusRule.additionalGroups` 追加符合 `PrometheusRule.spec.groups[]` 格式的自定义规则。

`grafanaDashboards.datasource` 必须使用只包含字母、数字、点、下划线或连字符的 Prometheus 数据源名称，默认值为 `Prometheus`。Chart 会把内置 Dashboard 中所有的 `${DS_PROMETHEUS}` 占位符替换为该名称。

启用 `grafanaDashboards.enabled` 后，Helm 会创建带有 `grafana_dashboard: "1"` 标签的 Dashboard ConfigMaps。配置了 Grafana sidecar 时会自动导入；没有 sidecar 时，请按下面的手工步骤导入 Dashboard 模板。

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
