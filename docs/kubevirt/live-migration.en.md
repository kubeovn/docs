# Live Migration

In virtual machine usage scenarios, live migration allows a virtual machine to be moved from one node to another for operations such as node maintenance, upgrades, and failover.

KubeVirt faces the following challenges during live migration:

- KubeVirt does not support live migration of virtual machines using bridge network mode by default.
- KubeVirt only handles memory and disk migration without specific optimizations for network migration.
- If the virtual machine's IP changes during migration, it cannot achieve a seamless live migration.
- If the network is interrupted during migration, it cannot achieve a seamless live migration.

Kube-OVN specifically addresses the above issues during the virtual machine migration process, allowing users to perform network-transparent live migrations. Our tests show that network interruption time can be controlled within 0.5 seconds, and TCP connections remain uninterrupted.

## Usage

Users only need to add the annotation `kubevirt.io/allow-pod-bridge-network-live-migration: "true"` in the VM Spec. Kube-OVN will automatically handle network migration during the process.

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

2. **SSH into the Virtual Machine and Test Network Connectivity**

    ```bash
    # password: gocubsgo
    virtctl ssh cirros@testvm
    ping 8.8.8.8
    ```

3. **Perform Migration in Another Terminal and Observe Virtual Machine Network Connectivity**

    ```bash
    virtctl migrate testvm
    ```

It can be observed that during the VM live migration process, the SSH connection remains uninterrupted, and ping only experiences packet loss in a few instances.

## Live Migration Principles

During the live migration process, Kube-OVN implements techniques inspired by the Red Hat team's [Live migration - Reducing downtime with multi-chassis port bindings](https://www.openvswitch.org/support/ovscon2022/slides/Live-migration-with-OVN.pdf).

To ensure network consistency between the source and target virtual machines during migration, the same IP address exists on the network for both the source and target VMs. This requires handling network conflicts and traffic confusion. The specific steps are as follows:

1. KubeVirt initiates the migration and creates the corresponding Pod on the target machine.
2. Kube-OVN detects that the target Pod is for a live migration and reuses the network port information from the source Pod.
3. Kube-OVN sets up traffic replication, causing network traffic to be duplicated to both the source Pod and the target Pod, reducing downtime caused by control plane switching during network transition.
4. Kube-OVN temporarily disables the network port of the target Pod, preventing the target Pod from actually receiving duplicated traffic and avoiding traffic confusion.
5. KubeVirt completes memory synchronization and deactivates the source Pod, causing the source Pod to stop handling network traffic.
6. KubeVirt activates the target Pod. At this point, libvirt sends a RARP request to activate the target Pod's network port, and the target Pod begins handling traffic.
7. KubeVirt deletes the source Pod, completing the live migration process.
8. Kube-OVN listens for migration completion events by watching the Migration CR and stops traffic replication once the migration is complete.

Network interruptions primarily occur between steps 5 and 6. The duration of the network interruption mainly depends on the time taken by libvirt to send the RARP request. Our tests show that the network interruption time can be controlled within 0.5 seconds, and TCP connections remain uninterrupted.