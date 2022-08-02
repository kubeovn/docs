# Uninstall

If you need to remove the Kube-OVN and replace it with another network plugin, 
please follow the steps below to remove all the corresponding Kube-OVN component and OVS configuration 
to avoid interference with other network plugins.

Feel free to contact us with an Issue to give us feedback on why you don't use Kube-OVN to help us improve it.

## Delete Resource in Kubernetes

Download and run the script below to delete resource created in Kubernetes:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/cleanup.sh
bash cleanup.sh
```

## Cleanup Config and Logs on Every Node

Run the following commands on each node to clean up the configuration retained by ovsdb and openvswitch:

```bash
rm -rf /var/run/openvswitch
rm -rf /var/run/ovn
rm -rf /etc/origin/openvswitch/
rm -rf /etc/origin/ovn/
rm -rf /etc/cni/net.d/00-kube-ovn.conflist
rm -rf /etc/cni/net.d/01-kube-ovn.conflist
rm -rf /var/log/openvswitch
rm -rf /var/log/ovn
rm -fr /var/log/kube-ovn
```

## Reboot Node

Reboot the machine to ensure that the corresponding NIC information and iptable/ipset rules 
are cleared to avoid the interference with other network plugins:

```bash
reboot
```
