
# Use IPsec to encrypt communication between nodes

This function is supported from v1.13.0 onwards, and the host UDP 500 and 4500 ports need to be available.

## Encryption process

kube-ovn-cni is responsible for applying for certificates and will create a certificate signing request to kube-ovn-controller. kube-ovn-controller will automatically approve the certificate application, and then kube-ovn-cni will generate an ipsec configuration file based on the certificate and finally start the ipsec process.

## Configure IPsec

Change the args `--enable-ovn-ipsec=false` in kube-ovn-controller and kube-ovn-cni to `--enable-ovn-ipsec=true`.
