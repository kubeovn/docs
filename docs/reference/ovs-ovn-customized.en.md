# OVS/OVN Customization

Upstream OVN/OVS was originally designed with the goal of a general purpose SDN controller and data plane.
Due to some specific usage of the Kubernetes network,Kube-OVN only focused on part of the features.
In order to achieve better performance, stability and specific features, Kube-OVN has made some modifications to the upstream OVN/OVS.
Users using their own OVN/OVS with Kube-OVN controllers need to be aware of the possible impact of the following changes:

Did not merge into the upstream modification.

- [38df6fa3f7](https://github.com/kubeovn/ovs/commit/38df6fa3f721dc53464fcff61dbc2bc79c710ab1) Adjust the election timer to avoid large-scale cluster election jitter.
- [d4888c4e75](https://github.com/kubeovn/ovs/commit/d4888c4e75f2288d8ff4f04ee57538659f118f5b) add fdb update logging.
- [d4888c4e75](https://github.com/kubeovn/ovs/commit/403fbd0f6561c8985302734608c2de659671c563) fdb: fix mac learning in environments with hairpin enabled.
- [9a81b91368](https://github.com/kubeovn/ovs/commit/9a81b91368b27afda97657a8864b729dc2e029e2) ovsdb-tool: add optional server id parameter for "join-cluster" command.
- [62d4969877](https://github.com/kubeovn/ovn/commit/62d4969877712c26fe425698d898b440f91b44bf) fix ssl listen address.
- [0700cb90f9](https://github.com/kubeovn/ovn/commit/0700cb90f950db1fb43490545dd4fc41afa46d70) Destination non-service traffic bypasses conntrack to improve performance on a particular data path.
- [c48049a64f](https://github.com/kubeovn/ovn/commit/c48049a64fedb1278f9158770a12751ee5bfc358) ECMP algorithm is adjusted from `dp_hash` to `hash` to avoid the hash error problem in some kernels.
- [64383c14a9](https://github.com/kubeovn/ovs/commit/64383c14a9c25e9e0ca53c6758d9499c60132536) Fix kernel Crash issue under Windows.
- [08a95db2ca](https://github.com/kubeovn/ovs/commit/08a95db2ca506fce4d89fdf4fafab74607b2bb9f) Support for github action builds on Windows.
- [680e77a190](https://github.com/kubeovn/ovs/commit/680e77a190ae7df3086bc35bb6150238e97f9020) Windows uses tcp listening by default.
- [05e57b3227](https://github.com/kubeovn/ovn/commit/05e57b322758461c54d5cad030486c3d25942c73) add support for windows.
- [0181b68be1](https://github.com/kubeovn/ovn/commit/0181b68be18e96bc4ca68a0c3e5082da34c9dcdd) br-int controller 默认监听 127.0.0.1:6653。
- [b3801ecb73](https://github.com/kubeovn/ovs/commit/b3801ecb732a788efd2380a7daca4e2a7726128e) modify src route priority.
- [977e569539](https://github.com/kubeovn/ovs/commit/977e569539893460cd27b2287d6042b62079ea65) fix reaching resubmit limit in underlay.
- [540592b9ff](https://github.com/kubeovn/ovn/commit/540592b9fff8c5574ae605086fdaa16b718551f7) Replaces the Mac address as the destination address after DNAT to reduce additional performance overhead.
- [10972d9632](https://github.com/kubeovn/ovs/commit/10972d963208490c5fe6ff66247b86b947136da6) Fix vswitchd ofport_usage memory leak.

Merged into upstream modification:

- [20626ea909](https://github.com/ovn-org/ovn/commit/20626ea9097020194fa558865ee8d64ba9ca0816) Multicast traffic bypasses LB and ACL processing stages to improve specific data path performance.
- [a2d9ff3ccd](https://github.com/ovn-org/ovn/commit/a2d9ff3ccd4e12735436b0578ce0020cb62f2c27) Deb build adds compile optimization options.
