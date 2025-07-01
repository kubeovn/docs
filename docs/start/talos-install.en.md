# Install on Talos

[Talos Linux](https://github.com/siderolabs/talos) is a modern Linux distribution built for Kubernetes。

## Deploy Kube-OVN via Helm Chart

You can deploy Kube-OVN on Talos Linux clusters with the following command:

```shell
helm install kube-ovn kubeovn/kube-ovn --wait \
    -n kube-system \
    --version {{ variables.version }} \
    --set OVN_DIR=/var/lib/ovn \
    --set OPENVSWITCH_DIR=/var/lib/openvswitch \
    --set DISABLE_MODULES_MANAGEMENT=true \
    --set cni_conf.MOUNT_LOCAL_BIN_DIR=false
```

If you want to use underlay as the default network, you need to pass the relevant chart values. Here is an example:

```shell
helm install kubeovn kubeovn/kube-ovn --wait \
    -n kube-system \
    --version {{ variables.version }} \
    --set OVN_DIR=/var/lib/ovn \
    --set OPENVSWITCH_DIR=/var/lib/openvswitch \
    --set DISABLE_MODULES_MANAGEMENT=true \
    --set cni_conf.MOUNT_LOCAL_BIN_DIR=false \
    --set networking.NETWORK_TYPE=vlan \
    --set networking.vlan.VLAN_INTERFACE_NAME=enp0s5f1 \
    --set networking.vlan.VLAN_ID=0 \
    --set networking.NET_STACK=ipv4 \
    --set-json networking.EXCLUDE_IPS='"172.99.99.11..172.99.99.99"' \
    --set-json ipv4.POD_CIDR='"172.99.99.0/24"' \
    --set-json ipv4.POD_GATEWAY='"172.99.99.1"'
```

!!! note
    Logical network interfaces, such as VLAN, Bond, and Bridge, cannot be used as provider interfaces for Underlay networks. Physical interfaces used for the Underlay network **MUST** be configured with `ignore=true` in the Talos machine configuration. Here is an example:
    ```yaml
    machine:
      network:
        interfaces:
          - interface: enp0s5f1
            ignore: true
    ```
