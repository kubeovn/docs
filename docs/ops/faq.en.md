# FAQ

For a better understanding of how to troubleshoot issues, see the [architecture overview](../reference/architecture.en.md) for Kube-OVN components and their interactions.

## General Troubleshooting Steps

1. Identify which network paths are affected:
    - Test connectivity between Pods.
    - Test connectivity between Pods and nodes.
    - Test access to Services from Pods.
    - Test DNS resolution from Pods.
    - Test access to external networks from Pods.
    - Check the `kube-ovn-pinger` logs on the affected node for network failures.
2. Check component logs for errors:
    - Check Pod logs for network failures.
    - Check kube-ovn-cni logs on the node for CNI errors.
    - Check ovs-ovn logs on the node for OVS errors.
    - Check kube-ovn-controller logs for controller errors.
    - Check ovn-central logs for OVN errors.
    - Check the node's dmesg output for kernel errors.
    - Check the node's `netstat -s` output for network errors.
3. Check component metrics for unusual CPU, memory, and I/O usage.

Use `kubectl ko log` to collect the logs and information above.

## Pod Creation Fails with an IP Conflict Event

### Behavior

The Pod does not reach the Running state. `kubectl describe pod` shows `duplicate IPv4 address <ip> found on logical switch port <port>`.

### Solution

1. Check whether the Pod uses a static IP. If it does, the address is already in use; choose another address or remove the Pod using it.
2. Search kube-ovn-controller logs for allocation and release events involving the conflicting IP.
3. Check whether a kube-ovn-controller restart or leader transition caused incorrect IP reclamation.
4. Run `kubectl ko nbctl show` to inspect the ports and IPs in the OVN database.
5. If an IP port remains in OVN but no longer exists in Kubernetes, remove the stale port with `kubectl ko nbctl lsp-del <port>`.

## Pod Creation Fails with a Gateway Ping Event

### Behavior

The Pod does not reach the Running state. `kubectl describe pod` shows `network <ip> with gateway <gw ip> is not ready for interface eth0 after 30 checks`.

### Solution

1. Run `kubectl ko sbctl show` to check whether the Pod port exists.
2. If it does not, collect ovn-central and ovs-ovn logs, check for errors, and restart those components before retrying.
3. If it does, check whether a network policy blocks the Pod from reaching its gateway.
4. For an Underlay network, ask the network administrator about restrictions on the physical network and see the [Underlay installation guide](../start/underlay.en.md).

## Pod Cannot Access an External Network

### Behavior

The Pod can reach destinations inside the cluster's default VPC but cannot reach external destinations.

### Solution

1. Use `kubectl ko trace` to check whether an ACL blocks traffic in the OVN logical flow path.
2. Adjust the ACL policy if one blocks the traffic.
3. Otherwise, inspect Subnet status to confirm the gateway node and its network connectivity.
4. If the gateway node is wrong or its network is unavailable, update the gateway node in the Subnet spec.
5. Check kube-ovn-controller logs for errors during gateway changes.

## Pod IP Is Outside the Specified CIDR

### Behavior

The Pod starts, but its IP address is outside the specified CIDR.

### Solution

1. Check `/etc/cni/net.d/` on the host for CNI configuration files other than Kube-OVN's.
2. Rename or remove any conflicting configuration files.
3. Restart kubelet and all Pods on the affected node.

## Debug Pod Fails to Start

### Behavior

A Pod created with `kubectl debug` remains in ContainerCreating. Its events report `network not ready` or `no address allocated`.

### Solution

Export the debug Pod's YAML and remove these annotations:

```yaml
ovn.kubernetes.io/ip_address
ovn.kubernetes.io/mac_address
ovn.kubernetes.io/allocated
ovn.kubernetes.io/routed
```

Delete the debug Pod and recreate it with the modified YAML.

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

Community feedback indicates that both CentOS 7 and Kylin may exhibit this issue. On Kylin, kernel `4.19.90-25.16.v2101` resolves it.

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

Starting from v1.11.x, in a cluster with 10,000 or more Pods, frequent OVN NB or SB leader elections may be caused by Kube-OVN periodically running ovsdb-server/compact, which affects leader election.

### Solution

To mitigate this issue, since v1.13 `ENABLE_COMPACT` is set to `false` by default (see `dist/images/install.sh` and `start-db.sh`), and no manual configuration is required. If your cluster was upgraded from an earlier version, please make sure the environment variable on the ovn-central container is not explicitly set to `true`:

```yaml
- name: ENABLE_COMPACT
  value: "false"
```
