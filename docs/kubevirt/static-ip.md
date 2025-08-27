# VM 固定 IP

在容器场景下，容器的 IP 地址通常是动态分配的，并且会在容器重启后发生变化。但是对于 VM 用户来说，他们希望 VM 的 IP 地址是固定的，来进行后续的管理和操作。

但是大部分常见 CNI 存在下面的局限性：

- 无法将 IP 地址和 VM 生命周期绑定，VM 重启或者后 IP 发生变化。
- IP 地址和 Node 绑定，VM 迁移到新的节点后无法复用之前 IP。
- 无法支持 IP 地址配置，用户无法指定 VM 的 IP 地址。

因此通常会使用 KubeVirt 的 `masquerade` 网络模式，通过 iptables 将 VM 的流量转发到宿主机网卡上，从而实现 VM 的 IP 固定，但 `masquerade` 相比 `bridge` 存在以下问题：

- Pod IP 和 VM IP 不一致，管理方面存在复杂度，且重启和热迁移后 Pod IP 发生变化，外部访问来看地址依然不固定。
- `masquerade` 使用 iptables 进行流量转发，性能相比 `bridge` 模式要差。
- `masquerade` 只支持三层流量转发，一些二层网络功能无法实现。
- `masquerade` 流量通过 conntrack 记录转发状态，热迁移期间存在流量中断可能。

Kube-OVN 支持为 KubeVirt 下 `bridge` 和 `managedTap` 网络模式下的 IP 和 VM 生命周期绑定，该 IP 地址在 VM 重启，热迁移等操作后仍然保持不变。同时也支持通过添加 annotation 的方式为 VM 配置固定 IP 地址。

## IP 和 VM 生命周期绑定

对于只希望 VM 生命周期内 IP 地址固定，但不需要指定 IP 地址的场景，用户只需按原先方式创建 VM 即可。Kube-OVN 内部的 IPAM 会自动记录 VM 生命周期，保证 VM 在重启和迁移后使用相同的 IP 地址。

下面以 `bridge` 网络模式为例，创建一个 VM，进行重启，热迁移等操作，并观察 IP 地址的变化。

1. 创建 VM

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: testvm
spec:
  runStrategy: Always 
  template:
    metadata:
      labels:
        kubevirt.io/size: small
        kubevirt.io/domain: testvm
      annotations:
        kubevirt.io/allow-pod-bridge-network-live-migration: "true"
    spec:
      domain:
        devices:
          disks:
            - name: containerdisk
              disk:
                bus: virtio
            - name: cloudinitdisk
              disk:
                bus: virtio
          interfaces:
          - name: default
            bridge: {}
        resources:
          requests:
            memory: 64M
      networks:
      - name: default
        pod: {}
      volumes:
        - name: containerdisk
          containerDisk:
            image: quay.io/kubevirt/cirros-container-disk-demo
        - name: cloudinitdisk
          cloudInitNoCloud:
            userDataBase64: SGkuXG4=
```

2. 查看 VM 状态

```bash
kubectl get vmi testvm
```

3. 重启 VM

```bash
virtctl restart testvm
```

4. 热迁移 VM

```bash
virtctl migrate testvm
```

可观察到在 bridge 模式下 VM 重启和热迁移后，IP 地址保持不变。

## 指定 IP 地址

对于需要指定 VM 的 IP 地址的场景，用户可以通过创建 VM 时添加 annotation 的方式为 VM 指定 IP 地址。其他使用方式和原生 KubeVirt 一致。

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: testvm
spec:
  runStrategy: Always 
  template:
    metadata:
      labels:
        kubevirt.io/size: small
        kubevirt.io/domain: testvm
      annotations:
        ovn.kubernetes.io/ip_address: 10.16.0.15 #(1)
        kubevirt.io/allow-pod-bridge-network-live-migration: "true"
    spec:
      domain:
        devices:
          disks:
            - name: containerdisk
              disk:
                bus: virtio
            - name: cloudinitdisk
              disk:
                bus: virtio
          interfaces:
          - name: default
            bridge: {}
        resources:
          requests:
            memory: 64M
      networks:
      - name: default
        pod: {}
      volumes:
        - name: containerdisk
          containerDisk:
            image: quay.io/kubevirt/cirros-container-disk-demo
        - name: cloudinitdisk
          cloudInitNoCloud:
            userDataBase64: SGkuXG4=
```

1. :man_raising_hand: 在这里指定 IP 地址。
