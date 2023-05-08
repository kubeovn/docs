# Change Join Subnet CIDR

If the Join subnet CIDR created conflicts or does not meet expectations, you can use this document to modify.

> After modifying the Join Subnet CIDR, the previously created Pods will not be able to access the external
> network normally and need to wait for the rebuild completed.

## Delete Join Subnet

```bash
kubectl patch subnet join --type='json' -p '[{"op": "replace", "path": "/metadata/finalizers", "value": []}]'
kubectl delete subnet join
```

## Cleanup Allocated Config

```bash
kubectl annotate node ovn.kubernetes.io/allocated=false --all --overwrite
```

## Modify Join Subnet

Change Join Subnet args in `kube-ovn-controller`:

```bash
kubectl edit deployment -n kube-system kube-ovn-controller
```

Change the CIDR below:

```yaml
args:
- --node-switch-cidr=100.51.0.0/16
```

Reboot the `kube-ovn-controller` and rebuild `join` Subnet:

```bash
kubectl delete pod -n kube-system -lapp=kube-ovn-controller
```

Check the new Join Subnet information:

```bash
# kubectl get subnet
NAME          PROVIDER   VPC           PROTOCOL   CIDR            PRIVATE   NAT     DEFAULT   GATEWAYTYPE   V4USED   V4AVAILABLE   V6USED   V6AVAILABLE   EXCLUDEIPS
join          ovn        ovn-cluster   IPv4       100.51.0.0/16   false     false   false     distributed   2        65531         0        0             ["100.51.0.1"]
ovn-default   ovn        ovn-cluster   IPv4       10.17.0.0/16    false     true    true      distributed   5        65528         0        0             ["10.17.0.1"]
```

## Reconfigure ovn0 NIC Address

The `ovn0` NIC information for each node needs to be re-updated, which can be done by restarting `kube-ovn-cni`:

```bash
kubectl delete pod -n kube-system -l app=kube-ovn-cni
```
