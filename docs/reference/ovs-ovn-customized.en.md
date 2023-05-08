# OVS/OVN Customization

Upstream OVN/OVS was originally designed with the goal of a general purpose SDN controller and data plane.
Due to some specific usage of the Kubernetes network,Kube-OVN only focused on part of the features.
In order to achieve better performance, stability and specific features, Kube-OVN has made some modifications to the upstream OVN/OVS.
Users using their own OVN/OVS with Kube-OVN controllers need to be aware of the possible impact of the following changes:

Did not merge into the upstream modification.

- [22ea22c40b](https://github.com/kubeovn/ovs/commit/22ea22c40b46ee5adeae977ff6cfca81b3ff25d7) Adjust the election timer to avoid large-scale cluster election jitter.
- [d26ae4de0a](https://github.com/kubeovn/ovn/commit/d26ae4de0ab070f6b602688ba808c8963f69d5c4) Destination non-service traffic bypasses conntrack to improve performance on a particular data path.
- [ab923b2522](https://github.com/kubeovn/ovn/commit/ab923b252271cbbcccc8091e338ee7efe75e5fcd) ECMP algorithm is adjusted from `dp_hash` to `hash` to avoid the hash error problem in some kernels.
- [64383c14a9](https://github.com/kubeovn/ovs/commit/64383c14a9c25e9e0ca53c6758d9499c60132536) Fix kernel Crash issue under Windows.
- [08a95db2ca](https://github.com/kubeovn/ovs/commit/08a95db2ca506fce4d89fdf4fafab74607b2bb9f) Support for github action builds on Windows.
- [680e77a190](https://github.com/kubeovn/ovs/commit/680e77a190ae7df3086bc35bb6150238e97f9020) Windows uses tcp listening by default.
- [94b73d939c](https://github.com/kubeovn/ovn/commit/94b73d939cd33b0531fa9a3422c999cd83ead087) Replaces the Mac address as the destination address after DNAT to reduce additional performance overhead.
- [2dc8e7aa20](https://github.com/kubeovn/ovs/commit/2dc8e7aa202818952b2fa80b47298604530c9de0) vswitchd ofport_usage memory leak.

Merged into upstream modification:

- [20626ea909](https://github.com/ovn-org/ovn/commit/20626ea9097020194fa558865ee8d64ba9ca0816) Multicast traffic bypasses LB and ACL processing stages to improve specific data path performance.
- [a2d9ff3ccd](https://github.com/ovn-org/ovn/commit/a2d9ff3ccd4e12735436b0578ce0020cb62f2c27) Deb build adds compile optimization options.
