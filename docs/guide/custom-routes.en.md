# Custom Routes

Custom routes can be configured via Pod's annotations. Here is an example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-routes
  annotations:
    ovn.kubernetes.io/routes: |
      [{
        "dst": "192.168.0.101/24",
        "gw": "10.16.0.254"
      }, {
        "gw": "10.16.0.254"
      }]'
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:alpine
```

> Do not set the `dst` field if you want to configure the default route.

For workloads such as Deployment, DaemonSet and StatefulSet, custom routes must be configured via `.spec.template.metadata.annotations`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-routes
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
      annotations:
        ovn.kubernetes.io/routes: |
          [{
            "dst": "192.168.0.101/24",
            "gw": "10.16.0.254"
          }, {
            "gw": "10.16.0.254"
          }]'
    spec:
      containers:
      - name: nginx
        image: docker.io/library/nginx:alpine
```
