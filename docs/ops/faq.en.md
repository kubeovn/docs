# FAQ

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

## Pod can not Access Service

### Behavior

Pod can not access Service, and `dmesg` show errors:

```bash
netlink：Unknown conntrack attr (type=6, max=5)
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

You can configure the environment variables for ovn-central as follows and turn off compact:

```yaml
- name: ENABLE_COMPACT
  value: "false"
```
