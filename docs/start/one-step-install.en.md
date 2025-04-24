# One-Click Installation

Kube-OVN provides a one-click installation script to help you quickly install a highly available,
production-ready Kube-OVN container network with Overlay networking by default.

Helm Chart installation is supported since Kube-OVN v1.12.0, and the default deployment is Overlay networking.

If you need Underlay/Vlan networking as the default container network，please read [Underlay Installation](./underlay.en.md)

Before installation please read [Prerequisites](./prepare.en.md) first to make sure the environment is ready.

## Script Installation

### Download the installation script

We recommend using the stable release version for production environments, please use the following command to download:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/{{ variables.branch }}/dist/images/install.sh
```

If you are interested in the latest features of the master branch, please use the following command to download:

```bash
wget https://raw.githubusercontent.com/kubeovn/kube-ovn/master/dist/images/install.sh
```

### Modify Configuration Options

Open the script using the editor and change the following variables to the expected:

```bash
REGISTRY="kubeovn"                     # Image Repo 
VERSION="{{ variables.version }}"                      # Image Tag
POD_CIDR="10.16.0.0/16"                # Default subnet CIDR don't overlay with SVC/NODE/JOIN CIDR
SVC_CIDR="10.96.0.0/12"                # Be consistent with apiserver's service-cluster-ip-range
JOIN_CIDR="100.64.0.0/16"              # Pod/Host communication Subnet CIDR, don't overlay with SVC/NODE/POD CIDR
LABEL="node-role.kubernetes.io/master" # The node label to deploy OVN DB
IFACE=""                               # The name of the host NIC used by the container network, or if empty use the NIC that host Node IP in Kubernetes
TUNNEL_TYPE="geneve"                   # Tunnel protocol，available options: geneve, vxlan or stt. stt requires compilation of ovs kernel module
```

You can also use regular expression to math NIC names，such as `IFACE=enp6s0f0,eth.*`.

### Run the Script

> The script needs to be executed with root permission

`bash install.sh`

Wait Kube-OVN ready.

## Helm Chart Installation

Since the installation of Kube-OVN requires setting some parameters, to install Kube-OVN using Helm, you need to follow the steps below.

### View the node IP address

```bash
$ kubectl get node -o wide
NAME                     STATUS     ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
kube-ovn-control-plane   NotReady   control-plane   20h   v1.26.0   172.18.0.3    <none>        Ubuntu 22.04.1 LTS   5.10.104-linuxkit   containerd://1.6.9
kube-ovn-worker          NotReady   <none>          20h   v1.26.0   172.18.0.2    <none>        Ubuntu 22.04.1 LTS   5.10.104-linuxkit   containerd://1.6.9
```

### Add label to node

```bash
$ kubectl label node -lbeta.kubernetes.io/os=linux kubernetes.io/os=linux --overwrite
node/kube-ovn-control-plane not labeled
node/kube-ovn-worker not labeled

$ kubectl label node -lnode-role.kubernetes.io/control-plane kube-ovn/role=master --overwrite
node/kube-ovn-control-plane labeled

# The following labels are used for the installation of dpdk images and can be ignored in non-dpdk cases
$ kubectl label node -lovn.kubernetes.io/ovs_dp_type!=userspace ovn.kubernetes.io/ovs_dp_type=kernel --overwrite
node/kube-ovn-control-plane labeled
node/kube-ovn-worker labeled
```

### Add Helm Repo information

```bash
$ helm repo add kubeovn https://kubeovn.github.io/kube-ovn/
"kubeovn" has been added to your repositories

$ helm repo list
NAME            URL
kubeovn         https://kubeovn.github.io/kube-ovn/

$ helm search repo kubeovn
NAME                CHART VERSION   APP VERSION DESCRIPTION
kubeovn/kube-ovn    0.1.0           1.12.0      Helm chart for Kube-OVN
```

### Run helm install to install Kube-OVN

The Node0IP, Node1IP, and Node2IP parameters are the IP addresses of the cluster master nodes, respectively. For other parameters, you can refer to the variable definitions in the values.yaml file.

```bash
# Single master node environment install
$ helm install kube-ovn kubeovn/kube-ovn --version {{ variables.version }} --set MASTER_NODES=${Node0IP}

# Using the node information above as an example, execute the install command
$ helm install kube-ovn kubeovn/kube-ovn --version {{ variables.version }} --set MASTER_NODES=172.18.0.3
NAME: kube-ovn
LAST DEPLOYED: Fri Mar 31 12:43:43 2023
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None

# Highly Available Cluster Installation
$ helm install kube-ovn kubeovn/kube-ovn --version {{ variables.version }} --set MASTER_NODES=${Node0IP}\,${Node1IP}\,${Node2IP}
```
