# Install Kube-OVN From Calico

If a Kubernetes cluster already has Calico installed and needs to change to Kube-OVN you can refer to this document.

> Since the installation of Calico may vary from version to version and the existing Pod network may be disrupted during the replacement process, 
> it is recommended that you plan ahead and compare the differences in Calico installation from version to version.

## Uninstall Calico

For Calico installed from an Operator:

```bash
kubectl delete -f https://projectcalico.docs.tigera.io/manifests/tigera-operator.yaml
kubectl delete -f https://projectcalico.docs.tigera.io/manifests/custom-resources.yaml
```

For Calico installed from manifests:

```bash
kubectl delete -f https://projectcalico.docs.tigera.io/manifests/calico.yaml 
```

## Cleanup Config Files

Delete the CNI-related configuration files on each machine, depending on the environment:

```bash
rm -f /etc/cni/net.d/10-calico.conflist
rm -f /etc/cni/net.d/calico-kubeconfig
```

Calico still leaves routing rules, iptables rules, veth network interfaces and other configuration information on the node, 
so it is recommended to reboot the node to clean up the relevant configuration to avoid problems that are difficult to troubleshoot.

## 安装 Kube-OVN

可参考[一键安装](../start/one-step-install.md)正常进行安装。
