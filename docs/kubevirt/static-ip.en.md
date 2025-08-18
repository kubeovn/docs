# Fixed Virtual Machine Addresses

In container environments, container IP addresses are typically dynamically assigned and may change after container restarts. However, VM users prefer their VM's IP address to be fixed for subsequent management and operations.

However, most common CNIs have the following limitations:

- **Unable to bind IP addresses to the VM lifecycle**: The VM's IP address changes after VM restarts or shutdowns.
- **IP addresses are bound to Nodes**: When a VM migrates to a new node, the previous IP cannot be reused.
- **Unable to support IP address configuration**: Users cannot specify the VM's IP address.

Therefore, the `masquerade` network mode of KubeVirt is often used. It forwards the VM's traffic to the host's network interface via iptables to achieve a fixed VM IP. However, compared to the `bridge` mode, `masquerade` has the following issues:

- **Inconsistent Pod and VM IPs**: This increases management complexity. After restarts and live migrations, Pod IPs change, making the external address still not fixed.
- **Performance**: `masquerade` uses iptables for traffic forwarding, resulting in lower performance compared to the `bridge` mode.
- **Limited to Layer 3 Traffic Forwarding**: Some Layer 2 network functionalities cannot be achieved.
- **Potential Traffic Interruptions**: `masquerade` traffic is tracked by conntrack, which may cause traffic interruptions during live migrations.

Kube-OVN supports binding IP addresses to the VM lifecycle under KubeVirt's `bridge` and `managedTap` network modes. The IP address remains unchanged after operations such as VM restarts and live migrations. It also supports configuring fixed IP addresses for VMs by adding annotations.

## Binding IP and VM Lifecycle

For scenarios where users only want the VM's IP address to remain fixed during the VM's lifecycle without specifying the IP address, users can create the VM as usual. Kube-OVN's internal IPAM automatically records the VM's lifecycle, ensuring the VM uses the same IP address after restarts and migrations.

Below is an example using the `bridge` network mode: creating a VM, performing restarts and live migrations, and observing the IP address changes.

1. **Create VM**

    ```bash
    kubectl apply -f - <<EOF
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
    EOF
    ```

2. **View VM Status**

    ```bash
    kubectl get vmi testvm
    ```

3. **Restart VM**

    ```bash
    virtctl restart testvm
    ```

4. **Live Migrate VM**

    ```bash
    virtctl migrate testvm
    ```

You can observe that in bridge mode, the VM's IP address remains unchanged after restarts and live migrations.

## Specifying IP Address

For scenarios where users need to specify the VM's IP address, they can add an annotation to the VM when creating it to assign a specific IP address. Other usage methods are consistent with native KubeVirt.

```bash
kubectl apply -f - <<EOF
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
        ovn.kubernetes.io/ip_address: 10.16.0.15
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
EOF
```
