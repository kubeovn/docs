# Use IPsec to encrypt communication between nodes

Since v1.13.0, Kube-OVN supports end-to-end encryption of inter-node tunnels (Geneve/Vxlan/STT) by leveraging the IPsec capability built into OVN/OVS.

## Prerequisites

- UDP port 500 (IKE) and UDP port 4500 (NAT-T) must be allowed between nodes.
- Kernel modules such as `xfrm` and `af_key` must be enabled. Either strongSwan or libreswan shipped by your distribution is sufficient.

## Encryption process

When `kube-ovn-cni` starts up, it issues a CertificateSigningRequest, which is automatically approved and signed by `kube-ovn-controller`. `kube-ovn-cni` then uses the issued certificate to write the IPsec configuration and start the ipsec process.

## Enable IPsec

Change the startup arguments of the `kube-ovn-controller` Deployment and the `kube-ovn-cni` DaemonSet from `--enable-ovn-ipsec=false` to `--enable-ovn-ipsec=true`, or set the following variable in the install script:

```bash
ENABLE_OVN_IPSEC=true
```

## Issue certificates with cert-manager (optional)

If [cert-manager](https://cert-manager.io/) is already deployed in your cluster and you want it to be in charge of issuing and rotating IPsec certificates, you can additionally enable `--cert-manager-ipsec-cert=true`. With this flag enabled, kube-ovn-cni will request IPsec certificates based on cert-manager-issued certificates instead of relying on Kube-OVN's built-in CA.

```yaml
args:
- --enable-ovn-ipsec=true
- --cert-manager-ipsec-cert=true
```

## Verification and troubleshooting

- Run `ovs-appctl ipsec/show` inside the `kube-ovn-cni` container on any node to inspect the IPsec tunnels, SAs, SPIs and other information related to peer nodes.
- `kubectl get csr` shows the CSRs sent by kube-ovn-cni. If IPsec is not effective on a node, first verify that its CSR has been approved (and check `signer.go`-related entries in the controller logs if necessary).
- To disable IPsec, change the arguments above back to `false`. The controller will clean up the corresponding IPsec configuration. If any SA still lingers on a node, restart the `kube-ovn-cni` Pod on that node.
