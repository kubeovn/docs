# Traffic Mirror

The traffic mirroring feature allows packets to and from the container network to be copied to a specific NIC of the host.
Administrators or developers can listen to this NIC to get the complete container network traffic for further analysis, monitoring, security auditing and other operations.
It can also be integrated with traditional NPM for more fine-grained traffic visibility.

The traffic mirroring feature introduces some performance loss, with an additional CPU consumption of 5% to 10% depending on CPU performance and traffic characteristics.

![mirror architecture](../static/mirror.png)

## Global Traffic Mirroring Settings

The traffic mirroring is disabled by default, please modify the args of `kube-ovn-cni` DaemonSet to enable it:

- `--enable-mirror=true`: Whether to enable traffic mirroring.
- `--mirror-iface=mirror0`: The name of the NIC that the traffic mirror is copied to. This NIC can be a physical NIC that already exists on the host machine.
  At this point the NIC will be bridged into the br-int bridge and the mirrored traffic will go directly to the underlying switch.
  If the NIC name does not exist, Kube-OVN will automatically create a virtual NIC with the same name, through which the administrator or developer can access all traffic on the current node on the host.
  The default is `mirror0`.

Next, you can listen to the traffic on `mirror0` with tcpdump or other traffic analysis tools.

```bash
tcpdump -ni mirror0
```

## Pod Level Mirroring Settings

If you only need to mirror some Pod traffic, you need to disable the global traffic mirroring and
then add the `ovn.kubernetes.io/mirror` annotation on a specific Pod to enable Pod-level traffic mirroring.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mirror-pod
  namespace: ls1
  annotations:
    ovn.kubernetes.io/mirror: "true"
spec:
  containers:
  - name: mirror-pod
    image: nginx:alpine
```
