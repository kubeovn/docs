# Tunnel Protocol Selection

Kube-OVN uses OVN/OVS as the data plane implementation and currently supports `Geneve`, `Vxlan` and `STT` tunnel encapsulation protocols.
These three protocols differ in terms of functionality, performance and ease of use.
This document will describe the differences in the use of the three protocols so that users can choose according to their situation.
[OVN Architecture Design Decision](https://www.man7.org/linux/man-pages/man7/ovn-architecture.7.html#DESIGN_DECISIONS) can be referenced for the differences in design among these three protocols in OVN.

## Geneve

The `Geneve` protocol is the default tunneling protocol selected during Kube-OVN deployment and is also the default recommended tunneling protocol for OVN.
This protocol is widely supported in the kernel and can be accelerated using the generic offload capability of modern NICs.
Since `Geneve` has a variable header, it is possible to use 24bit space to mark different datapaths users can create a larger number of virtual networks and a single datapath can support 32767 ports.

If you are using Mellanox or Corigine SmartNIC OVS offload, `Geneve` requires a higher kernel version.
Upstream kernel of 5.4 or higher, or other compatible kernels that backports this feature.

Due to the use of UDP encapsulation, this protocol does not make good use of the TCP-related offloads of modern NICs when handling TCP over UDP,
and consumes more CPU resources when handling large packets.

## Vxlan

`Vxlan` is a recently supported protocol in the upstream OVN,
which is widely supported in the kernel and can be accelerated using the common offload capabilities of modern NICs.
Due to the limited length of the protocol header and the additional space required for OVN orchestration,
there is a limit to the number of datapaths that can be created,
with a maximum of 4096 datapaths and a maximum of 4096 ports under each datapath.
Also, `inport`-based ACLs are not supported due to header length limitations.

`Vxlan` offloading is supported in common kernels if using Mellanox or Corigine SmartNIC.

Due to the use of UDP encapsulation, this protocol does not make good use of the TCP-related offloads of modern NICs when handling TCP over UDP,
and consumes more CPU resources when handling large packets.

## STT

The `STT` protocol is an early tunneling protocol supported by the OVN that uses TCP-like headers to
take advantage of the TCP offload capabilities common to modern NICs and significantly increase TCP throughput.
The protocol also has a long header to support full OVN capabilities and large-scale datapaths.

This protocol is not supported in the kernel. To use it, you need to compile an additional OVS kernel module and recompile
the new version of the kernel module when upgrading the kernel.

This protocol is not currently supported by the SmartNic and cannot use the offloading capability of OVS offloading.

## References

- [https://ipwithease.com/vxlan-vs-geneve-understand-the-difference/](https://ipwithease.com/vxlan-vs-geneve-understand-the-difference/){: target="_blank" }
- [OVN FAQ](https://docs.ovn.org/en/latest/faq/general.html){: target="_blank" }
- [What is Geneve](https://www.redhat.com/en/blog/what-geneve){: target="_blank" }
