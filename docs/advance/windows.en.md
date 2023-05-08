# Windows Support

Kube-OVN supports Kubernetes cluster networks that include Windows system nodes,
allowing unified containers network management.

## Prerequisites

- Read [Adding Windows nodes](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/adding-windows-nodes/) to add Windows nodes.
- Windows nodes must have the KB4489899 patch installed for Overlay/VXLAN networks to work properly, and it is recommended to update your system to the latest version.
- Hyper-V and management tools must be installed on the Windows node.
- Due to Windows restrictions tunnel encapsulation can only be used in Vxlan mode.
- SSL, IPv6, dual-stack, QoS features are not supported at this time.
- Dynamic subnet and dynamic tunnel interface are not supported at this time. You need to create the subnet and select the network interface before installing the Windows node.
- Multiple `ProviderNetwork`s are not supported, and the bridge interface configuration cannot be dynamically adjusted.

## Install OVS on Windows

Due to some issues with upstream OVN and OVS support for Windows containers, a modified installation package provided by Kube-OVN is required.

Use the following command to enable the `TESTSIGNING` startup item on the Windows node, which requires a system reboot to take effect.

```bash
bcdedit /set LOADOPTIONS DISABLE_INTEGRITY_CHECKS
bcdedit /set TESTSIGNING ON
bcdedit /set nointegritychecks ON
```

Download [Windows package](https://github.com/kubeovn/kube-ovn/releases/download/v1.10.0/kube-ovn-win64.zip) on Windows node and install.

Confirm that the service is running properly after installation:

```bash
PS > Get-Service | findstr ovs
Running  ovsdb-server  Open vSwitch DB Service
Running  ovs-vswitchd  Open vSwitch Service
```

## Install Kube-OVN

Download the installation script in the Windows node [install.ps1](https://github.com/kubeovn/kube-ovn/blob/{{ variables.branch }}/dist/windows/install.ps1).

Add relevant parameters and run:

```bash
.\install.ps1 -KubeConfig C:\k\admin.conf -ApiServer https://192.168.140.180:6443 -ServiceCIDR 10.96.0.0/12
```

By default, Kube-OVN uses the NIC where the node IP is located as the tunnel interface.
If you need to use another NIC, you need to add the specified annotation to the Node before installation, e.g. `ovn.kubernetes.io/tunnel_interface=Ethernet1`.
