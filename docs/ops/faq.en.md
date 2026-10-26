# FAQ

To better diagnose issues, please refer to [Architecture](../reference/architecture.md) first to understand the components of Kube-OVN and the interactions between them.

## General Troubleshooting Steps

1. Diagnose network link connectivity:
    - Test whether Pods can communicate with each other
    - Test whether Pods can communicate with the host node
    - Test whether Pods can access Kubernetes Services properly
    - Test whether DNS name resolution functions normally within Pods
    - Test whether Pods can access external networks properly
    - Inspect the `kube-ovn-pinger` logs on problematic nodes to check for network access failures
2. Check component logs to determine whether error messages are output:
    - Check Pod logs to verify if application-level network errors occurred
    - Check node `kube-ovn-cni` logs to see if CNI plugin encountered processing errors
    - Check node `ovs-ovn` logs to see if OVS encountered processing errors
    - Check `kube-ovn-controller` logs to verify whether the controller encountered errors
    - Check `ovn-central` logs to verify whether OVN encountered errors
    - Check node `dmesg` logs to verify whether kernel-level network errors occurred
    - Check node `netstat -s` logs to observe TCP/UDP/IP protocol error statistics
3. Check monitoring metrics of each component to identify CPU, memory, and I/O anomalies

The above logs and diagnostics can be collected via the `kubectl ko logs` command.

## Pod Creation Failed with IP Conflict Event

### Behavior

The Pod cannot transition to the `Running` state, and `kubectl describe pod` shows the event:
`duplicate IPv4 address <ip> found on logical switch port <port>`.

### Solution

1. Confirm whether the Pod is intended to have a static/fixed IP. If it is a static IP Pod, the address is already occupied; change the allocated IP or delete the Pod occupying the IP.
2. Check the `kube-ovn-controller` logs and filter for the IP allocation and release process of the conflicting IP.
3. Observe whether `kube-ovn-controller` restarts or leader election switchover caused IP release failures.
4. Run `kubectl ko nbctl show` to inspect the ports and IPs actually recorded in the OVN database.
5. If the OVN database is inconsistent with Kubernetes resources and stale logical switch ports exist, clean them up manually via `kubectl ko nbctl lsp-del <port>`.

## Pod Creation Failed with Ping Gateway Failed Event

### Behavior

The Pod cannot transition to the `Running` state, and `kubectl describe pod` shows the event:
`network <ip> with gateway <gw ip> is not ready for interface eth0 after 30 checks`.

### Solution

1. Run `kubectl ko sbctl show` to verify whether the Pod's logical port information exists in the Southbound database.
2. If the port does not exist, collect logs from `ovn-central` and `ovs-ovn` to identify potential errors, and restart `ovn-central` and `ovs-ovn` to retry.
3. If the port exists, check whether NetworkPolicies are blocking the Pod from communicating with its gateway.
4. In Underlay network mode, check with your network administrator to see if the underlying physical network has ARP or security restrictions; refer to [Underlay Installation](../start/underlay.md).

## Pod Cannot Access External Network

### Behavior

In the default VPC, Pods can communicate normally within the cluster, but cannot access external networks outside the cluster.

### Solution

1. Run `kubectl ko trace` to verify whether ACLs on the OVN logical flow path block the traffic.
2. If ACL restrictions exist, adjust your ACL policies.
3. If no ACL restrictions exist, check the Subnet status to verify whether the centralized gateway node information is correct and the gateway node is healthy.
4. If the gateway node information is incorrect or the node has network anomalies, update the Subnet Spec to specify a healthy gateway node.
5. Collect `kube-ovn-controller` logs to check for error logs during gateway failover.

## Pod IP Not in Specified CIDR

### Behavior

The Pod is created successfully, but its assigned IP address does not fall within the expected Subnet CIDR.

### Solution

1. Check whether other non-Kube-OVN CNI configuration files exist under `/etc/cni/net.d/` on the host node.
2. If other CNI config files exist, rename or remove them.
3. Restart `kubelet` and all Pods running on that node.

## Debug Pod Failed to Create

### Behavior

A Pod created via `kubectl debug` remains stuck in `ContainerCreating`, and Pod events report `network not ready` or `no address allocated`.

### Solution

Export the Pod's YAML definition after creating the debug Pod, and remove the following Annotations from the YAML:

```yaml
ovn.kubernetes.io/ip_address
ovn.kubernetes.io/mac_address
ovn.kubernetes.io/allocated
ovn.kubernetes.io/routed
```

Delete the failed debug Pod, and recreate a new debug Pod using the edited YAML.

## Intermittent Cross-Host Container Access Failures on ARM Systems

### Behavior

Compatibility issues between ARM-based operating systems (such as CentOS 7 on ARM or Kylin Linux) and certain physical NIC offload features may cause intermittent container network packet drops.

Identify the problem using `netstat`:

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

If `InCsumErrors` is present and increases alongside communication failures, this issue is confirmed.

### Solution

The fundamental resolution requires upgrading the OS kernel and NIC drivers with the hardware vendor.
As a temporary workaround, disable `tx offload` on the physical NIC (note that this may result in a noticeable drop in TCP throughput):

```bash
ethtool -K eth0 tx off
```

Based on community feedback, upgrading Kylin Linux to kernel `4.19.90-25.16.v2101` or later resolves this issue.

## Pod Cannot Access Service

### Behavior

A Pod cannot access endpoints backing a Kubernetes Service, and `dmesg` reports errors like:

```bash
netlink: Unknown conntrack attr (type=6, max=5)
openvswitch: netlink: Flow actions may not be safe on all matching packets.
```

This log indicates that the in-kernel OVS module version is too low to support the requested NAT operations.

### Solution

1. Upgrade the Linux kernel module or compile a newer OVS kernel module manually.
2. If only using Overlay networking, you can update the `kube-ovn-controller` argument by setting `--enable-lb=false` to disable OVN native LB and use `kube-proxy` for Service forwarding.

## Frequent Leader Election Occurs in ovn-central

### Behavior

Starting with v1.11.x, in clusters running 10,000 Pods or more, if OVN NB or SB databases experience frequent leader re-elections, the cause is typically periodic `ovsdb-server/compact` executions interfering with Raft consensus heartbeats.

### Solution

To mitigate this issue, since v1.13 `ENABLE_COMPACT` is set to `false` by default (see `dist/images/install.sh` and `start-db.sh`), and no manual configuration is required. If your cluster was upgraded from an earlier version, verify that the environment variable on the `ovn-central` container is not explicitly set to `true`:

```yaml
- name: ENABLE_COMPACT
  value: "false"
```
