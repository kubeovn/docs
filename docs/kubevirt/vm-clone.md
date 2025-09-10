# 虚拟机克隆

KubeVirt 在 Clone 虚拟机的过程中默认会复制虚拟机实例上所有的 Label 和 Annotation，如果虚拟机使用了 Kube-OVN 的 Annotation 固定了 IP、MAC 等网络配置，可能会导致网络地址冲突。本文档将会介绍如何处理这种情况。

## 过滤 Annotation

在 `VirtualMachineClone` 资源中忽略 Kube-OVN 相关的 Annotation，如下所示：

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

## 指定克隆后虚拟机地址

!!! note

    `patches` 字段在 KubeVirt 1.6 版本开始支持。

可以使用如下配置指定克隆后虚拟机的 IP 地址：

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

如果需要对克隆后的虚拟机随机分配地址，请使用下面的配置：

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

如果你希望对虚拟机克隆的 Annotation 进行更细粒度的修改请参考 [KubeVirt Clone API](https://kubevirt.io/user-guide/storage/clone_api/#json-patches){: target="_blank" }。
