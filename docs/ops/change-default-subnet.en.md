# Change Subnet CIDR

If a subnet CIDR is created that conflicts or does not meet expectations,
it can be modified by following the steps in this document.

> After modifying the subnet CIDR, the previously created Pods will not be able to access the network properly and need to be rebuilt.
> Careful consideration is recommended before operating. This document is only for business subnet CIDR changes,
> if you need to change the Join subnet CIDR, please refer to [Change Join CIDR](./change-join-subnet.en.md).

## Edit Subnet

Use `kubectl edit` to modify `cidrBlock`, `gateway` and `excludeIps`.

```bash
kubectl edit subnet test-subnet
```

## Rebuild all Pods under this Subnet

Take the subnet binding `test` Namespace as example:

```bash
for pod in $(kubectl get pod --no-headers -n "$ns" --field-selector spec.restartPolicy=Always -o custom-columns=NAME:.metadata.name,HOST:spec.hostNetwork | awk '{if ($2!="true") print $1}'); do
  kubectl delete pod "$pod" -n test --ignore-not-found
done
```

If only the default subnet is used, you can delete all Pods that are not in host network mode using the following command:

```bash
for ns in $(kubectl get ns --no-headers -o custom-columns=NAME:.metadata.name); do
  for pod in $(kubectl get pod --no-headers -n "$ns" --field-selector spec.restartPolicy=Always -o custom-columns=NAME:.metadata.name,HOST:spec.hostNetwork | awk '{if ($2!="true") print $1}'); do
    kubectl delete pod "$pod" -n "$ns" --ignore-not-found
  done
done
```

## Change Default Subnet Settings

If you are modifying the CIDR for the default Subnet, you also need to change the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --default-cidr=10.17.0.0/16
- --default-gateway=10.17.0.1
- --default-exclude-ips=10.17.0.1
```
