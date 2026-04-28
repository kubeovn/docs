# DHCP

When using `managedTap`, `SR-IOV`, or `DPDK` type networks, KubeVirt's built-in DHCP cannot function in these network modes. Kube-OVN leverages OVN's DHCP capabilities to configure DHCP options at both subnet and Pod levels, enabling virtual machines (VMs) under these network types to properly obtain IP addresses via DHCP. Additionally, Kube-OVN's DHCP supports advanced options such as DHCPv6, IPv6RA, DNS, and TFTP, allowing users to customize DHCP service behavior based on their needs.

!!! warning

    For `bridge` type networks, KubeVirt's DHCP intercepts and responds to DHCP requests before Kube-OVN, making Kube-OVN's DHCP settings ineffective. To utilize Kube-OVN's advanced DHCP features, we recommend replacing `bridge` type networks with `managedTap` type networks. For `managedTap` network configuration, refer to [Configuring the managedTap Network Binding Plugin](dual-stack.en.md#configuring-the-managedtap-network-binding-plugin).

## Subnet-Level DHCP Configuration

The Subnet DHCP is configured as follows:

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: sn-dual
spec:
  cidrBlock: "10.0.0.0/24,240e::a00/120"
  default: false
  disableGatewayCheck: true
  disableInterConnection: false
  excludeIps:
    - 10.0.0.1
    - 240e::a01
  gateway: 10.0.0.1,240e::a01
  gatewayNode: ''
  gatewayType: distributed
  natOutgoing: false
  private: false
  protocol: Dual
  provider: ovn
  vpc: vpc-test
  enableDHCP: true
  dhcpV4Options: "lease_time=3600,router=10.0.0.1,server_id=169.254.0.254,server_mac=00:00:00:2E:2F:B8"
  dhcpV6Options: "server_id=00:00:00:2E:2F:C5"
  enableIPv6RA: true
  ipv6RAConfigs: "address_mode=dhcpv6_stateful,max_interval=30,min_interval=5,send_periodic=true"
```

- `enableDHCP`: Whether to enable the DHCP function for the subnet.
- `dhcpV4Options`,`dhcpV6Options`: This field directly exposes DHCP-related options within ovn-nb, please read [DHCP Options](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#DHCP_Options_TABLE){: target="_blank" } for more detail.
The default value is `"lease_time=3600, router=$ipv4_gateway, server_id=169.254.0.254, server_mac=$random_mac"` and `server_id=$random_mac`.
- `enableIPv6RA`: Whether to enable the route broadcast function of DHCPv6.
- `ipv6RAConfigs`: This field directly exposes DHCP-related options within ovn-nb Logical_Router_Port, please read [Logical Router Port](https://man7.org/linux/man-pages/man5/ovn-nb.5.html#Logical_Router_Port_TABLE){: target="_blank" } for more detail.
The default value is `address_mode=dhcpv6_stateful, max_interval=30, min_interval=5, send_periodic=true`.

## Per-Pod DHCP Configuration

In addition to subnet-level DHCP configuration, Kube-OVN supports configuring DHCP options for each Pod's network interface individually via Pod annotations. Per-Pod DHCP configuration has the highest priority, overriding subnet-level DHCP settings, and is independent of the subnet's `enableDHCP` setting.

### Annotation Format

```bash
# Primary network (provider="ovn")
ovn.kubernetes.io/dhcp-v4-options: "lease_time=3600,router=10.0.0.1,dns_server=8.8.8.8"
ovn.kubernetes.io/dhcp-v6-options: "server_id=00:00:00:00:00:01"

# Attachment network (provider="net1.ns1.ovn")
net1.ns1.ovn.kubernetes.io/dhcp-v4-options: "lease_time=7200"
```

The annotation key format is `<provider>.kubernetes.io/dhcp-v4-options` and `<provider>.kubernetes.io/dhcp-v6-options`, where `<provider>` is the network provider name. For the default network, the provider is `ovn`. For attachment networks added via Multus, the provider format is `<net-attach-def-name>.<namespace>.ovn`.

### Usage Examples

The following example sets custom DHCPv4 options for a Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dhcp-pod
  annotations:
    ovn.kubernetes.io/dhcp-v4-options: "lease_time=3600,router=10.0.0.1,dns_server=8.8.8.8"
    ovn.kubernetes.io/dhcp-v6-options: "server_id=00:00:00:00:00:01"
spec:
  containers:
    - name: test
      image: docker.io/library/nginx:alpine
```

For Multus multi-NIC scenarios, you can set DHCP options separately for each network interface by provider:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-nic-dhcp-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: '[{"name": "net1", "namespace": "ns1"}]'
    ovn.kubernetes.io/dhcp-v4-options: "lease_time=3600,router=10.0.0.1"
    net1.ns1.ovn.kubernetes.io/dhcp-v4-options: "lease_time=7200,router=10.0.1.1"
spec:
  containers:
    - name: test
      image: docker.io/library/nginx:alpine
```

### Priority

The DHCP options priority from highest to lowest is:

1. **Pod annotations**: DHCP options set via `<provider>.kubernetes.io/dhcp-v4-options` and `<provider>.kubernetes.io/dhcp-v6-options`.
2. **Subnet configuration**: DHCP options set via the `dhcpV4Options` and `dhcpV6Options` fields in the Subnet CRD.

When a Pod has DHCP annotations, the Pod-level DHCP configuration is used exclusively, ignoring the subnet-level settings.

!!! note

    Removing DHCP annotations from a running Pod does not immediately revert the DHCP settings. A Pod restart is required for the changes to take effect.
