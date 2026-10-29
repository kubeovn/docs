# FAQ

For an overview of the components involved in troubleshooting, see the [architecture](../reference/architecture.en.md).

## General troubleshooting

1. Narrow down the failing path: test Pod-to-Pod, Pod-to-node, Pod-to-Service, DNS, and external connectivity separately. Check the `kube-ovn-pinger` logs on affected nodes.
2. Check the affected Pod and the `kube-ovn-cni`, `ovs-ovn`, `kube-ovn-controller`, and `ovn-central` logs. Inspect node `dmesg` and `netstat -s` output for kernel or network errors.
3. Check CPU, memory, and I/O metrics for the affected components. Use `kubectl ko log all` to collect component logs and node diagnostics; see the [CLI guide](./kubectl-ko.en.md).

## Pod creation fails with an IP conflict

### Behavior

The Pod does not become Running, and its events report an address conflict on a logical switch port.

### Solution

1. Check whether the Pod requests a static IP and whether another Pod already uses it. If so, assign a different IP or resolve the conflicting workload.
2. Inspect `kube-ovn-controller` logs for allocations and releases of the address, including controller restarts or leader changes.
3. Compare the Kubernetes Pod and IP allocation records with the ports shown by `kubectl ko nbctl show`. Remove an orphaned OVN port only after confirming that no active workload owns it.

## Pod creation fails during the gateway connectivity check

### Behavior

The Pod does not become Running, and its events contain `network <ip> with gateway <gw ip> is not ready for interface eth0 after <n> checks`.

### Solution

1. Use `kubectl ko sbctl show` to check whether the Pod's logical port has propagated to the OVN southbound database.
2. If the port is missing, inspect the `ovn-central` and `ovs-ovn` logs for synchronization errors.
3. If the port is present, check whether network policies prevent the Pod from reaching its gateway. For an Underlay subnet, also check physical network restrictions with the network administrator and see the [Underlay installation guide](../start/underlay.en.md).

## Pod cannot reach an external network

### Behavior

A Pod in the default VPC can reach destinations inside the cluster but cannot reach external destinations.

### Solution

1. Use `kubectl ko trace` to identify any ACL that blocks the traffic. Adjust the policy if it is responsible.
2. Check the Subnet status and gateway node selection, then verify the gateway node's external connectivity. If the configured gateway node is unavailable, update the Subnet gateway node configuration.
3. Check `kube-ovn-controller` logs for errors during gateway changes.

## Pod IP is outside the expected CIDR

### Behavior

The Pod starts, but its IP is outside the configured Subnet CIDR.

### Solution

Check `/etc/cni/net.d/` on the node for other CNI configuration files and determine which CNI handled the Pod. If another configuration took precedence, correct the CNI configuration and recreate the affected Pod after confirming the node's intended network setup.

## Debug Pod fails to start

### Behavior

A Pod created with `kubectl debug` remains in ContainerCreating, and its events report `network not ready` or `no address allocated`.

### Solution

If the debug Pod inherited the original Pod's Kube-OVN allocation annotations, export its manifest and remove the stale `ovn.kubernetes.io/ip_address`, `ovn.kubernetes.io/mac_address`, `ovn.kubernetes.io/allocated`, and `ovn.kubernetes.io/routed` annotations. Recreate the debug Pod from the corrected manifest so Kube-OVN can allocate its own address.

## Kylin ARM system cross-host container access intermittently fails

### Behavior

There is a problem with Kylin ARM system and some NIC offload, which can cause intermittent container network failure.

Use `netstat` to identify the problem:

```bash
# netstat -us
IcmpMsg:
    InType0: 22
    InType3: 24
    InType8: 117852
    OutType0: 117852
    OutType3: 29
    OutType8: 22
Udp:
    3040636 packets received
    0 packets to unknown port received.
    4 packet receive errors
    602 packets sent
    0 receive buffer errors
    0 send buffer errors
    InCsumErrors: 4
UdpLite:
IpExt:
    InBcastPkts: 10244
    InOctets: 4446320361
    OutOctets: 1496815600
    InBcastOctets: 3095950
    InNoECTPkts: 7683903
```

If `InCsumErrors` is present and increases with network failures, you can confirm that this is the problem.

### Solution

The fundamental solution requires communication with Kylin and the corresponding network card manufacturer to update the system and drivers.
A temporary solution would be to turn off `tx offload` on the physical NIC, but this would cause a significant degradation in tcp performance.

```bash
ethtool -K eth0 tx off
```

From the community feedback, the problem can be solved by the `4.19.90-25.16.v2101` kernel.

## Pod cannot Access Service

### Behavior

Pod cannot access Service, and `dmesg` show errors:

```bash
netlink: Unknown conntrack attr (type=6, max=5)
openvswitch: netlink: Flow actions may not be safe on all matching packets.
```

This log indicates that the in-kernel OVS version is too low to support the corresponding NAT operation.

### Solution

1. Upgrade the kernel module or compile the OVS kernel module manually.
2. If you are using an Overlay network you can change the `kube-ovn-controller` args, setting `--enable-lb=false` to disable the OVN LB to use kube-proxy for service forwarding.

## Frequent leader selection occurs in ovn-central

### Behavior

Starting from the v1.11.x version, in a cluster with 1w Pod or more, if OVN NB or SB frequently elects the master, the possible reason is that Kube-OVN periodically performs the ovsdb-server/compact action, which affects the master selection logic.

### Solution

To mitigate this issue, since v1.13 `ENABLE_COMPACT` is set to `false` by default (see `dist/images/install.sh` and `start-db.sh`), and no manual configuration is required. If your cluster was upgraded from an earlier version, please make sure the environment variable on the ovn-central container is not explicitly set to `true`:

```yaml
- name: ENABLE_COMPACT
  value: "false"
```
