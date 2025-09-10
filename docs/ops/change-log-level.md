# 调整日志等级

编辑 `kube-ovn.yaml` 文件，在服务启动脚本的参数列表中设置日志等级，示例如下：

``` bash
vi kube-ovn.yaml
# ...
        - name: kube-ovn-controller
          image: "docker.io/kubeovn/kube-ovn:{{ variables.version }}"
          imagePullPolicy: IfNotPresent
          args:
          - /kube-ovn/start-controller.sh
          - --v=3
# ...
# 日志等级越高，日志就越详细
```
