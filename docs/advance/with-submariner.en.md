# Cluster Inter-Connection with Submariner

[Submariner](https://submariner.io/) is an open source networking component that connects multiple Kubernetes cluster Pod and Service 
networks which can help Kube-OVN interconnect multiple clusters.

Compared to [OVN-IC](./with-ovn-ic.md), Submariner can connect Kube-OVN and non-Kube-OVN cluster networks, and
Submariner can provide cross-cluster capability for services. However, Submariner currently only enables the default subnets to be connected, 
and cannot selectively connect multiple subnets.

## Prerequisites

- The Service CIDRs of the two clusters and the CIDR of the default Subnet cannot overlap.

## Install Submariner

Download the `subctl` binary and deploy it to the appropriate path:

```bash
curl -Ls https://get.submariner.io | bash
export PATH=$PATH:~/.local/bin
echo export PATH=\$PATH:~/.local/bin >> ~/.profile
```

Change `kubeconfig` context to the cluster that need to deploy `submariner-broker`:

```bash
subctl deploy-broker
```

In this document the default subnet CIDR for `cluster0` is `10.16.0.0/16` and the default subnet CIDR for `cluster1` is `11.16.0.0/16`.

Switch `kubeconfig` to `cluster0` to register the cluster to the broker, and register the gateway node:

```bash
subctl  join broker-info.subm --clusterid  cluster0 --clustercidr 10.16.0.0/16  --natt=false --cable-driver vxlan --health-check=false
kubectl label nodes cluster0 submariner.io/gateway=true
```

Switch `kubeconfig` to `cluster1` to register the cluster to the broker, and register the gateway node:

```bash
subctl  join broker-info.subm --clusterid  cluster1 --clustercidr 11.16.0.0/16  --natt=false --cable-driver vxlan --health-check=false
kubectl label nodes cluster1 submariner.io/gateway=true
```

Next, you can start Pods in each of the two clusters and try to access each other using IPs.

Network communication problems can be diagnosed by using the `subctl` command:

```bash
subctl show all
subctl diagnose all
```

For more Submariner operations please read [Submariner Usage](https://submariner.io/operations/usage/).
