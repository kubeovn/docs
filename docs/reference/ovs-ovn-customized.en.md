# OVS/OVN Customization

Upstream OVN/OVS was originally designed with the goal of a general purpose SDN controller and data plane.
Due to some specific usage of the Kubernetes network, Kube-OVN only focused on part of the features.
In order to achieve better performance, stability and specific features, Kube-OVN has made some modifications to the upstream OVN/OVS.
Users using their own OVN/OVS with Kube-OVN controllers need to be aware of the possible impact of the following changes:

Modification not merged into upstream:

- [4228eab1d7](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/4228eab1d722087ba795e310eadc9e25c4513ec1.patch) Fix memory leak by ofport_usage and trim memory periodically.
- [54056ea65d](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/54056ea65dc28aa1c4c721a2a34d7913f79f8376.patch) Adjust the election timer to avoid large-scale cluster election jitter.
- [6b4dcb311f](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/6b4dcb311f171d81a5d40ea51a273fc356c123db.patch) Add fdb update logging.
- [f627b7721e](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/f627b7721ec282f2edaf798913b1559b939687f0.patch) fdb: fix mac learning in environments with hairpin enabled.
- [3f3e3a436f](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/3f3e3a436ff5eb2eaafbeeae8ea9dc0c514fe8a3.patch) ovsdb-tool: add optional server id parameter for "join-cluster" command.
- [a6cb8215a8](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/a6cb8215a80635129e4fada4c0d25c25fb746bf7.patch) Fix QoS memory leak issue.
- [d4d76ddb2e](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/d4d76ddb2e12cdd9e73bb5e008ebb9fd1b4d6ca6.patch) ovsdb-tool: add fix-cluster command.
- [ffd2328d4a](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/ffd2328d4a55271569e2b89e54a2c18f4e186af8.patch) netdev: reduce cpu utilization for getting device addresses.
- [d088c5d8c2](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/d088c5d8c263552c5a31d87813991aee30ab74de.patch) ovs-router: skip getting source address for kube-ipvs0.
- [1b31f07dc6](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/1b31f07dc60c016153fa35d936cdda0e02e58492.patch) Increase the default probe interval for large cluster.
- [54b7678229](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/54b767822916606dbb78335a3197983f435b5b8a.patch) Update ovs-sandbox for docker run.
- [9ee66bd91b](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/9ee66bd91be65605cffb9a490b4dba3bc13358e9.patch) Modify source route priority.
- [e889d46924](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e889d46924085ca0fe38a2847da973dfe6ea100e.patch) Fix reaching resubmit limit in underlay.
- [f9e97031b5](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/f9e97031b56ab5747b5d73629198331a6daacdfd.patch) ovn-controller: do not send GARP on localnet for Kube-OVN ports.
- [78cade0187](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/78cade01874292e2c101c39b975290ef6c812a50.patch) Add support for conditionally skipping conntrack.
- [85aa6263ad](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/85aa6263ad5b3648eb7ceec90c812328dbb7c6c0.patch) northd: skip conntrack when accessing node local dns ip.
- [34dc3e3fcf](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/34dc3e3fcfacec6597293765ecd6e20fe15581f1.patch) lflow: do not send direct traffic between lports to conntrack.
- [a297b840c2](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/a297b840c2c9f118c7ce6133077087b5999f12dd.patch) Direct output to lsp for dnat packets in logical switch ingress pipelines.
- [03e35ed9c5](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/03e35ed9c5b4de0fa8acbc2c057cdd5957a8d605.patch) ovn-controller: make activation strategy work for single chassis.
- [e7d3ba53cd](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e7d3ba53cdcbc524bb29c54ddb07b83cc4258ed7.patch) Skip node local dns ip conntrack when setting acls.
- [9286e1fd57](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/9286e1fd578fdb8f565a0f4aa9066b538295e1ac.patch) Select local backend first.
- [e5916eb53a](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e5916eb53abc3b7d28c407c3c47566c46116090a.patch) Fix lr-lb dnat with multiple distributed gateway ports.
- [e4e6ea9c5f](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e4e6ea9c5f4ba080b719924e470daa8094ff38a7.patch) Support dedicated BFD LRP.
- [e76880e792](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/e76880e792af56b2a3836098105079f5f8f1ff26.patch) northd: add nb option version_compatibility.
- [477695a010](https://github.com/kubeovn/kube-ovn/blob/master/dist/images/patches/477695a010affe56efdd66b60510fa612f8704c1.patch) northd: skip arp/nd request for lrp addresses from localnet ports.

Merged into upstream modification:

- [20626ea909](https://github.com/ovn-org/ovn/commit/20626ea9097020194fa558865ee8d64ba9ca0816) Multicast traffic bypasses LB and ACL processing stages to improve specific data path performance.
- [a2d9ff3ccd](https://github.com/ovn-org/ovn/commit/a2d9ff3ccd4e12735436b0578ce0020cb62f2c27) Deb build adds compile optimization options.
