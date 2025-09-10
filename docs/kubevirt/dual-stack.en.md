# Dual-Stack Network

In KubeVirt's Bridge network mode, the DHCP service is provided by `virt-launcher`. However, KubeVirt currently only implements DHCP for IPv4 single-stack, which prevents KubeVirt VMs in Bridge mode from dynamically obtaining IPv6 addresses through the RA (Router Advertisement) protocol. Although Kube-OVN provides DHCP and RA capabilities, these features are ineffective because KubeVirt intercepts DHCP/RA requests in advance.

In versions of KubeVirt after 1.4.0, a new Network Binding Plugin introduces a Bridge-like network mode called `managedTap`. In this mode, KubeVirt does not intercept DHCP requests. Therefore, by combining the new `managedTap` mode with Kube-OVN's DHCP/RA capabilities, it is possible to automatically obtain dual-stack network addresses for VMs.

## Configuring Dual-Stack DHCP

Enable DHCP and IPv6 RA features in the Subnet of Kube-OVN, as shown in the following YAML configuration:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: dual-stack-subnet
spec:
  cidrBlock: "10.244.0.0/16,fd00:10:244::/64"
  enableDHCP: true
  enableIPv6RA: true
```

## Configuring the `managedTap` Network Binding Plugin

Register the `managedTap` Network Binding Plugin in KubeVirt:

```bash
# kubectl patch kubevirts -n kubevirt kubevirt --type=json -p=\
'[{"op": "add", "path": "/spec/configuration/network",   "value": {
    "binding": {
        "managedtap": {
            "domainAttachmentType": "managedTap"
        }
    }
}}]'
```

## Create a virtual machine, specifying the use of the `managedTap` network type

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: dual-stack-vm
  namespace: default
spec:
  running: false
  template:
    spec:
      domain:
        devices:
          interfaces:
            - name: default
              binding:
                name: managedtap
      networks:
        - name: default
          pod: {}
```

By following these steps, VMs can obtain their corresponding IPv4/IPv6 addresses through the DHCP and IPv6 RA protocols.
