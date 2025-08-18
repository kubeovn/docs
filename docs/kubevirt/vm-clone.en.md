# Virtual Machine Clone

KubeVirt copies all Labels and Annotations from the virtual machine instance by default during the VM cloning process. If the virtual machine uses Kube-OVN Annotations to pin IP, MAC, and other network configurations, this may cause network address conflicts. This document describes how to handle this situation.

## Filtering Annotations

Ignore Kube-OVN related Annotations in the `VirtualMachineClone` resource as shown below:

```yaml
kind: VirtualMachineClone
apiVersion: "clone.kubevirt.io/v1beta1"
metadata:
  name: testclone
spec:
  source:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: vm-source
  target:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: vm-target
  template:
    annotationFilters:
      - "ovn.kubernetes.io/*"
```

## Specifying Cloned VM Address

!!! note

    The `patches` field is supported starting from KubeVirt version 1.6.

You can use the following configuration to specify the IP address of the cloned virtual machine:

```yaml
kind: VirtualMachineClone
apiVersion: "clone.kubevirt.io/v1beta1"
metadata:
  name: testclone
spec:
  source:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: vm-source
  target:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: vm-target
  patches:
  - '{"op": "replace", "path": "/spec/template/metadata/annotations/ovn.kubernetes.io~1ip_address", "value": "10.16.0.15"}'
```

Or if you wanto to random allocate the IP address, try:

```yaml
kind: VirtualMachineClone
apiVersion: "clone.kubevirt.io/v1beta1"
metadata:
  name: testclone
spec:
  source:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: vm-source
  target:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: vm-target
  patches:
  - '{"op": "remove", "path": "/spec/template/metadata/annotations/ovn.kubernetes.io~1ip_address"}'
```

If you need to make more granular modifications to the annotations of a virtual machine clone, please refer to the [KubeVirt Clone API](https://kubevirt.io/user-guide/storage/clone_api/#json-patches).
