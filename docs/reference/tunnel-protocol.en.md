# Tunnel Protocol Selection

Kube-OVN 使用 OVN/OVS 作为数据平面实现，目前支持 `Geneve`，`Vxlan` 和 `STT` 三种隧道封装协议。
这三种协议在功能，性能和易用性上存在着区别，本文档将介绍三种协议在使用中的差异，用户可根据自己的情况进行选择。

## Geneve

`Geneve` 协议为 Kube-OVN 部署时选择的默认隧道协议，也是 OVN 默认推荐的隧道协议。该协议在内核中得到了广泛的支持，
并可以利用现代网卡的通用 Offload 能力进行加速。由于 `Geneve` 有着较长的头部，可以使用 24bit 空间来标志不同的 
datapath 用户可以创建更多数量的虚拟网络。

如果使用 Mellanox 或芯启源的智能网卡 OVS 卸载，`Geneve` 需要较高版本的内核支持，需要选择 5.4 以上的上游内核，
或 backport 了该功能的其他兼容内核。

由于使用 UDP 进行封装，该协议在处理 TCP over UDP 时不能很好的利用现代网卡的 TCP 相关卸载，在处理大包时会消耗较多 
CPU 资源。

## Vxlan

`Vxlan` 为上游 OVN 近期支持的协议，该协议在内核中得到了广泛的支持， 并可以利用现代网卡的通用 Offload 能力进行加速。
由于该协议头部有限，并且 OVN 需要使用额外的空间进行编排，datapath 的数量存在限制，最多只能创建 4096 个 datapath，
每个 datapath 下最多 4096 个端口。同时由于空间有限，基于 `inport` 的 ACL 没有进行支持。

如果使用 Mellanox 或芯启源的智能网卡 OVS 卸载，`Vxlan` 的卸载在常见内核中已获得支持。

由于使用 UDP 进行封装，该协议在处理 TCP over UDP 时不能很好的利用现代网卡的 TCP 相关卸载，在处理大包时会消耗较多
CPU 资源。

## STT

`STT` 协议为 OVN 较早支持的隧道协议，该协议使用类 TCP 的头部，可以充分利用现代网卡通用的 TCP 卸载能力，大幅提升 TCP 
的吞吐量。同时该协议头部较长可支持完整的 OVN 能力和大规模的 datapath。

该协议未在内核中支持，若要使用需要额外编译 OVS 内核模块，并在升级内核时对应再次编译新版本内核模块。

该协议目前未被智能网卡支持，无法使用 OVS 的卸载能力。

## 参考资料
- [https://ipwithease.com/vxlan-vs-geneve-understand-the-difference/](https://blog.russellbryant.net/2017/05/30/ovn-geneve-vs-vxlan-does-it-matter/)
- [OVN FAQ](https://docs.ovn.org/en/latest/faq/general.html)
- [What is Geneve](https://www.redhat.com/en/blog/what-geneve)
