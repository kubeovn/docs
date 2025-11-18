# Network Interface Hotplug

Kube-OVN and [Multus Dynamic Networks Controller](https://github.com/k8snetworkplumbingwg/multus-dynamic-networks-controller) work together to enable the [network interface hotplug](https://kubevirt.io/user-guide/network/hotplug_interfaces/) feature supported by KubeVirt in v1.4.0, allowing secondary network interfaces to be added or removed without restarting the VM.

## Prerequisites

Install Multus in [Thick mode](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/thick-plugin.md):

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/refs/heads/master/deployments/multus-daemonset-thick.yml
```

Install [Multus Dynamic Networks Controller](https://github.com/k8snetworkplumbingwg/multus-dynamic-networks-controller):

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-dynamic-networks-controller/refs/heads/main/manifests/dynamic-networks-controller.yaml
```

## Create Secondary Network

### Create NetworkAttachmentDefinition

Set the `provider` suffix to `ovn`:

```yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: attachnet
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "kube-ovn",
      "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
      "provider": "attachnet.default.ovn"
    }'
```

- `spec.config.type`: Set to `kube-ovn` to trigger the CNI plugin to use Kube-OVN subnet.
- `server_socket`: The socket file used for Kube-OVN communication. Default location is `/run/openvswitch/kube-ovn-daemon.sock`.
- `provider`: The `<name>.<namespace>.ovn` of the current NetworkAttachmentDefinition. Kube-OVN will use this information to find the corresponding Subnet resource. Note that the suffix must be set to `ovn`.

### Create a Kube-OVN Subnet

If using Kube-OVN as a secondary network interface, the `provider` should be set to the corresponding NetworkAttachmentDefinition's `<name>.<namespace>.ovn`, and must end with the `ovn` suffix.
Example of creating a Subnet with Kube-OVN providing the secondary network interface:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: attachnet
spec:
  protocol: IPv4
  provider: attachnet.default.ovn
  cidrBlock: 172.17.0.0/16
  gateway: 172.17.0.1
  excludeIps:
  - 172.17.0.0..172.17.0.10
```

## Adjust VM Network

Create a VM using the following yaml:

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-fedora
spec:
  runStrategy: Always
  template:
    spec:
      domain:
        devices:
          disks:
          - disk:
              bus: virtio
            name: containerdisk
          interfaces:
          - masquerade: {}
            name: defaultnetwork
          rng: {}
        resources:
          requests:
            memory: 1024M
      networks:
      - name: defaultnetwork
        pod: {}
      terminationGracePeriodSeconds: 0
      volumes:
      - containerDisk:
          image: quay.io/kubevirt/fedora-with-test-tooling-container-disk:devel
        name: containerdisk
```

### Add Network Interface

Modify the VM Spec to add a new network interface field:

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-fedora
template:
  spec:
    domain:
      devices:
        interfaces:
        - name: defaultnetwork
          masquerade: {}
          # new interface
        - name: dyniface1
          bridge: {}
    networks:
    - name: defaultnetwork
      pod: {}
      # new network
    - name: dyniface1
      multus:
        networkName: attachnet
```

### Remove Network Interface

Dynamically remove a network interface by setting the `interface` `state` to `absent`:

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-fedora
template:
  spec:
    domain:
      devices:
        interfaces:
          - name: defaultnetwork
            masquerade: {}
          # set the interface state to absent 
          - name: dyniface1
            state: absent
            bridge: {}
    networks:
      - name: defaultnetwork
        pod: {}
      - name: dyniface1
        multus:
          networkName: attachnet
```
