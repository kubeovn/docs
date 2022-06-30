# One-Click Installation

Kube-OVN provides a one-click installation script to help you quickly install a highly available, 
production-ready Kube-OVN container network with Overlay networking by default.

If you need Underlay/Vlan networking as the default container network，please read [Underlay Installation](./underlay.en.md)

Before installation please read [Prerequisites](./prepare.en.md) first to make sure the environment is ready.

## Download the installation script

We recommend using the stable release version for production environments, please use the following command to download:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/release-1.10/dist/images/install.sh
```

If you are interested in the latest features of the master branch, please use the following command to download:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/images/install.sh
```

## Modify Configuration Options

Open the script using the editor and change the following variables to the expected:

```bash
REGISTRY="kubeovn"                     # Image Repo 
VERSION="v1.10.2"                      # Image Tag
POD_CIDR="10.16.0.0/16"                # Default subnet CIDR don't overlay with SVC/NODE/JOIN CIDR
SVC_CIDR="10.96.0.0/12"                # Be consistent with apiserver's service-cluster-ip-range
JOIN_CIDR="100.64.0.0/16"              # Pod/Host communication Subnet CIDR, don't overlay with SVC/NODE/POD CIDR
LABEL="node-role.kubernetes.io/master" # The node label to deploy OVN DB
IFACE=""                               # The name of the host NIC used by the container network, or if empty use the NIC that host Node IP in Kubernetes
TUNNEL_TYPE="geneve"                   # Tunnel protocol，available options: geneve, vxlan or stt. stt requires compilation of ovs kernel module
```

You can also use regular expression to math NIC names，such as `IFACE=enp6s0f0,eth.*`.

## Run the Script

`bash install.sh`

Wait Kube-OVN ready.
