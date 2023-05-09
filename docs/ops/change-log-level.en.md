# Change Log Level

Open `kube-ovn.yaml` and set the log level in the parameter list of the service startup script, such as:

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
# The higher the log level, the more detailed the log

```
