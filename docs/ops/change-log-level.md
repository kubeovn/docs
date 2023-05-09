# 调整日志等级

打开 `kube-ovn.yaml`，在服务启动脚本的参数列表中设置 log 等级，比如：

``` bash
vi kube-ovn.yaml
# ...
        - name: kube-ovn-controller
          image: "kubeovn/kube-ovn:v1.12.0"
          imagePullPolicy: IfNotPresent
          args:
          - /kube-ovn/start-controller.sh
          - --v=3
# ...
# log 等级越高，log 就越详细
```
