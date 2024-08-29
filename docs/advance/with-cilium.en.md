# Integration with Cilium

[Cilium](https://cilium.io/) is an eBPF-based networking and security component. Kube-OVN uses the
[CNI Chaining](https://docs.cilium.io/en/stable/gettingstarted/cni-chaining/) mode to enhance existing features.
Users can use both the rich network abstraction capabilities of Kube-OVN and the monitoring and security capabilities that come with eBPF.

By integrating Cilium, Kube-OVN users can have the following gains:

- Richer and more efficient security policies.
- Hubble-based monitoring and UI.

![](../static/cilium-integration.png)

## Prerequisites

1. Linux kernel version above 4.19 or other compatible kernel for full eBPF capability support.
2. Install Helm in advance to prepare for the installation of Cilium, please refer to [Installing Helm](https://helm.sh/docs/intro/install/) to deploy Helm.

## Configure Kube-OVN

In order to fully utilize the security capabilities of Cilium, you need to disable the `networkpolicy` feature within Kube-OVN
and adjust the CNI configuration priority.

Change the following variables in the `install.sh` script:

```bash
ENABLE_NP=false
CNI_CONFIG_PRIORITY=10
```

If the deployment is complete, you can adjust the args of `kube-ovn-controller`:

```yaml
args:
- --enable-np=false
```

Modify the `kube-ovn-cni` args to adjust the CNI configuration priority:

```yaml
args:
- --cni-conf-name=10-kube-ovn.conflist
```

Adjust the Kube-OVN cni configuration name on each node:

```bash
mv /etc/cni/net.d/01-kube-ovn.conflist /etc/cni/net.d/10-kube-ovn.conflist
```

## Deploy Cilium

Create the `chaining.yaml` configuration file to use Cilium's `generic-veth` mode:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cni-configuration
  namespace: kube-system
data:
  cni-config: |-
    {
      "name": "generic-veth",
      "cniVersion": "0.3.1",
      "plugins": [
        {
          "type": "kube-ovn",
          "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
          "ipam": {
              "type": "kube-ovn",
              "server_socket": "/run/openvswitch/kube-ovn-daemon.sock"
          }
        },
        {
          "type": "portmap",
          "snat": true,
          "capabilities": {"portMappings": true}
        },
        {
          "type": "cilium-cni"
        }
      ]
    }
```

Installation the chaining config:

```bash
kubectl apply -f chaining.yaml
```

Deploying Cilium with Helm:

```bash
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --version 1.11.6 \
    --namespace kube-system \
    --set cni.chainingMode=generic-veth \
    --set cni.customConf=true \
    --set cni.configMap=cni-configuration \
    --set routingMode=native \
    --set enableIPv4Masquerade=false \
    --set enableIdentityMark=false
```

Confirm that the Cilium installation was successful:

```bash
# cilium  status
    /¯¯\
 /¯¯\__/¯¯\    Cilium:         OK
 \__/¯¯\__/    Operator:       OK
 /¯¯\__/¯¯\    Hubble:         disabled
 \__/¯¯\__/    ClusterMesh:    disabled
    \__/

DaemonSet         cilium             Desired: 2, Ready: 2/2, Available: 2/2
Deployment        cilium-operator    Desired: 2, Ready: 2/2, Available: 2/2
Containers:       cilium             Running: 2
                  cilium-operator    Running: 2
Cluster Pods:     8/11 managed by Cilium
Image versions    cilium             quay.io/cilium/cilium:v1.10.5@sha256:0612218e28288db360c63677c09fafa2d17edda4f13867bcabf87056046b33bb: 2
                  cilium-operator    quay.io/cilium/operator-generic:v1.10.5@sha256:2d2f730f219d489ff0702923bf24c0002cd93eb4b47ba344375566202f56d972: 2

```
