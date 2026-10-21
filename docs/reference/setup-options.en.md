# Installation and Configuration Options

In [One-Click Installation](../start/one-step-install.en.md) we use the default configuration for installation.
Kube-OVN also supports more custom configurations, which can be configured in the installation script,
or later by changing the parameters of individual components.
This document will describe what these customization options do, and how to configure them.

## Built-in Network Settings

Kube-OVN will configure two built-in Subnets during installation:

1. `default` Subnet, as the default subnet used by the Pod to assign IPs, with a default CIDR of `10.16.0.0/16` and a gateway of `10.16.0.1`.
2. The `join` subnet, as a special subnet for network communication between the Node and Pod, has a default CIDR of `100.64.0.0/16` and a gateway of `100.64.0.1`.

The configuration of these two subnets can be changed during installation via the installation scripts variables:

```bash
POD_CIDR="10.16.0.0/16"
POD_GATEWAY="10.16.0.1"
JOIN_CIDR="100.64.0.0/16"
EXCLUDE_IPS=""
```

`EXCLUDE_IP` sets the address range for which `kube-ovn-controller` will not automatically assign from it, the format is: `192.168.10.20..192.168.10.30`.

Note that in the Overlay case these two Subnets CIDRs cannot conflict with existing host networks and Service CIDRs.

You can change the address range of both Subnets after installation by referring to [Change Subnet CIDR](../ops/change-default-subnet.en.md) and [Change Join Subnet CIDR](../ops/change-join-subnet.en.md).

## Config Service CIDR

Since some of the iptables and routing rules set by `kube-proxy` will conflict with the rules set by Kube-OVN,
Kube-OVN needs to know the CIDR of the service to set the corresponding rules correctly.

This can be done by modifying the installation script:

```bash
SVC_CIDR="10.96.0.0/12"  
```

You can also modify the args of the `kube-ovn-controller` Deployment after installation:

```yaml
args:
- --service-cluster-ip-range=10.96.0.0/12
```

## Overlay NIC Selection

In the case of multiple NICs on a node, Kube-OVN will select the NIC corresponding to the Kubernetes Node IP as the NIC
for cross-node communication between containers and establish the corresponding tunnel.

If you need to select another NIC to create a container tunnel, you can change it in the installation script:

```bash
IFACE=eth1
```

This option supports regular expressions separated by commas, e.g. 'ens[a-z0-9]*,eth[a-z0-9]*'.

It can also be adjusted after installation by modifying the args of the `kube-ovn-cni` DaemonSet:

```yaml
args:
- --iface=eth1
```

If each machine has a different NIC name and there is no fixed pattern, you can use the node annotation `ovn.kubernetes.io/tunnel_interface` to configure each node one by one.
This annotation will override the configuration of `iface`.

```bash
kubectl annotate node no1 ovn.kubernetes.io/tunnel_interface=ethx
```

To specify different encapsulation NICs for different subnets, please refer to [Overlay Encapsulation NIC Selection](../advance/node-network.en.md).

## Config MTU

Since Overlay encapsulation requires additional space, Kube-OVN will adjust the MTU of the container NIC based on the MTU of the selected NIC when creating the container NIC.
By default, the Pod NIC MTU is the host NIC MTU - 100 on the Overlay Subnet, and the Pod NIC and host NIC have the same MTU on the Underlay Subnet.

If you need to adjust the size of the MTU under the Overlay subnet, you can modify the parameters of the `kube-ovn-cni` DaemonSet:

```yaml
args:
- --mtu=1333
```

In addition, if the underlying host network enables Jumbo Frames (e.g., MTU 9000), the automatically calculated Pod MTU will also be large. When Pod traffic egresses to the external internet (where the path MTU is typically 1500), an overly large MTU can lead to fragmentation drops or PMTUD blackholes. You can apply an upper bound to the auto-computed Pod MTU via `--max-mtu` (set to 0 to disable the limit):

```yaml
args:
- --max-mtu=1400
```

## Global Traffic Mirroring Setting

When global traffic mirroring is enabled, Kube-OVN will create a `mirror0` virtual NIC on each node
and copy all container network traffic from the current machine to that NIC,
Users can perform traffic analysis with tcpdump and other tools. This function can be enabled in the installation script:

```bash
ENABLE_MIRROR=true
```

It can also be adjusted after installation by modifying the args of the `kube-ovn-cni` DaemonSet:

```yaml
args:
- --enable-mirror=true
```

The ability to mirror traffic is disabled in the default installation,
if you need fine-grained traffic mirroring or need to mirror traffic to additional NICs please refer to [Traffic Mirror](../guide/mirror.en.md).

## LB Settings

In Underlay scenarios, `kube-proxy` cannot intercept container network traffic, so it cannot implement Service forwarding functionality. In this case, you can enable OVN's built-in L2 LB capability to implement ClusterIP forwarding. In scenarios where Service forwarding capability is not needed, you can disable the LB capability to achieve better performance. Note that this feature only implements ClusterIP forwarding for container networks and cannot replace all capabilities of `kube-proxy`, so it cannot replace `kube-proxy`.

This feature can be configured in the installation script:

```bash
ENABLE_LB=false
```

It can also be configured after installation by changing the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-lb=false
```

The LB feature is enabled in the default installation.

The spec field `enableLb` has been added to the subnet crd definition since Kube-OVN v1.12.0 to migrate the LB function of Kube-OVN to the subnet level. You can set whether to enable the LB function based on different subnets. The `enable-lb` parameter in the `kube-ovn-controller` deployment is used as a global switch to control whether to create a load-balancer record. The `enableLb` parameter added in the subnet is used to control whether the subnet is associated with a load-balancer record. After the previous version is upgraded to v1.12.0, the `enableLb` parameter of the subnet will automatically inherit the value of the original global switch parameter.

## NetworkPolicy Settings

Kube-OVN uses ACLs in OVN to implement NetworkPolicy.
Users can choose to disable the NetworkPolicy feature or use the Cilium Chain approach to implement NetworkPolicy using eBPF.
In this case, the NetworkPolicy feature of Kube-OVN can be disabled to achieve better performance on the control plane and data plane.

This feature can be configured in the installation script:

```bash
ENABLE_NP=false
```

It can also be configured after installation by changing the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-np=false
```

NetworkPolicy is enabled by default.

## EIP and SNAT Settings

If the EIP and SNAT capabilities are not required on the default VPC,
users can choose to disable them to reduce the performance overhead of `kube-ovn-controller` in
large scale cluster environments and improve processing speed.

This feature can be configured in the installation script:

```bash
ENABLE_EIP_SNAT=false
```

It can also be configured after installation by changing the args of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-eip-snat=false
```

EIP and SNAT is enabled by default. More information can refer to [EIP and SNAT](../guide/eip-snat.en.md).

## LoadBalancer Service Support Settings

In the default VPC, you can enable this option to support `LoadBalancer` type Services. For detailed usage and other configurable parameters, please refer to [LoadBalancer Service](../guide/loadbalancer-service.md).

This feature is disabled by default. It can be configured in the installation script:

```bash
ENABLE_LB_SVC=true
```

Or configured post-installation by modifying the arguments of the `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-lb-svc=true
```

To support advanced load balancer services backed by VPC NAT Gateway nftables share DNAT (allowing multiple backend Pods to share the same public EIP:Port with ClientIP session affinity), configure the following parameter (enabled by default):

```bash
ENABLE_NFTABLE_LB_SVC=true
```

Or configure post-installation via `kube-ovn-controller` Deployment arguments:

```yaml
args:
- --enable-nftable-lb-svc=true
```

## Centralized Gateway ECMP Settings

The centralized gateway supports two mode of high availability, primary-backup and ECMP.
If you want to enable ECMP mode, you need to change the args of `kube-ovn-controller` Deployment:

```yaml
args:
- --enable-ecmp=true 
```

Centralized gateway default installation under the primary-backup mode, more gateway-related content please refer to [Config Subnet](../guide/subnet.en.md).

The spec field `enableEcmp` has been added to the subnet crd definition since Kube-OVN v1.12.0 to migrate the ECMP switch to the subnet level. You can set whether to enable ECMP mode based on different subnets. The `enable-ecmp` parameter in the `kube-ovn-controller` deployment is no longer used. After the previous version is upgraded to v1.12.0, the subnet switch will automatically inherit the value of the original global switch parameter.

## Kubevirt VM Fixed Address Settings

For VM instances created by Kubevirt, `kube-ovn-controller` can assign and manage IP addresses in a similar way to the StatefulSet Pod.
This allows VM instances address fixed during start-up, shutdown, upgrade, migration, and other operations throughout their lifecycle,
making them more compatible with the actual virtualization user experience.

This feature is enabled by default after v1.10.6. To disable this feature, you need to change the following args in the `kube-ovn-controller` Deployment:

```yaml
args:
- --keep-vm-ip=false
```

## CNI Settings

By default, Kube-OVN installs the CNI binary in the `/opt/cni/bin` directory
and the CNI configuration file `01-kube-ovn.conflist` in the `/etc/cni/net.d` directory.
If you need to change the installation location and the priority of the CNI configuration file,
you can modify the following parameters of the installation script.

```bash
CNI_CONF_DIR="/etc/cni/net.d"
CNI_BIN_DIR="/opt/cni/bin"
CNI_CONFIG_PRIORITY="01"
```

Or change the Volume mount and args of the `kube-ovn-cni` DaemonSet after installation:

```yaml
volumes:
- name: cni-conf
  hostPath:
    path: "/etc/cni/net.d"
- name: cni-bin
  hostPath:
    path:"/opt/cni/bin"
...
args:
- --cni-conf-name=01-kube-ovn.conflist
```

## Tunnel Type Settings

The default encapsulation mode of Kube-OVN Overlay is Geneve,
if you want to change it to Vxlan or STT,
please adjust the following parameters in the installation script:

```bash
TUNNEL_TYPE="vxlan"
```

Or change the environment variables of `ovs-ovn` DaemonSet after installation:

```yaml
env:
- name: TUNNEL_TYPE
  value: "vxlan"
```

If you need to use the STT tunnel and need to compile additional kernel modules for ovs, please refer to [Performance Tuning](../advance/performance-tuning.en.md).

Please refer to [Tunneling Protocol Selection](../reference/tunnel-protocol.en.md) for the differences between the different protocols in practice.

## SSL Settings

The OVN DB API interface supports SSL encryption to secure the connection.
To enable it, adjust the following parameters in the installation script:

```bash
ENABLE_SSL=true
```

The SSL is disabled by default.

## Conntrack-skip Destination CIDR List

For destinations that need to bypass conntrack processing (for example, side traffic that already has NAT or session affinity handled elsewhere), a skip list can be configured in the installation script or as a `kube-ovn-controller` flag. Multiple CIDRs are comma-separated:

```bash
SKIP_CONNTRACK_DST_CIDRS="10.10.0.0/16,fd00:10::/64"
```

```yaml
args:
- --skip-conntrack-dst-cidrs=10.10.0.0/16,fd00:10::/64
```

Empty by default.

## Enable OVN IPSec

Once enabled, Kube-OVN encrypts the inter-node Geneve/Vxlan/STT tunnels via OVN's built-in IPSec capability and issues certificates automatically.

```bash
ENABLE_OVN_IPSEC=true
```

This switch must be turned on for both the controller and the daemon:

```yaml
args:
- --enable-ovn-ipsec=true
```

For details, see [OVN IPSec](../advance/ovn-ipsec.en.md).

## AdminNetworkPolicy / DNS Name Resolver Support

Enable AdminNetworkPolicy (ANP/CNP) and DNS-name-based access control (which depends on the `DNSNameResolver` CRD):

```bash
ENABLE_ANP=true
ENABLE_DNS_NAME_RESOLVER=true
```

```yaml
args:
- --enable-anp=true
- --enable-dns-name-resolver=true
```

For usage, see [Domain-name-based Access Control](../guide/egress-firewall.en.md).

## VPC NAT Gateway Master Switch

Controls whether the VPC NAT Gateway controllers are enabled. Enabled by default:

```bash
ENABLE_NAT_GW=true
```

The runtime switch can also be controlled via the `enable-vpc-nat-gw` field in the `ovn-vpc-nat-gw-config` ConfigMap.

## ovn-northd Thread Count

For large-scale clusters, the number of `ovn-northd` worker threads can be tuned to speed up incremental computation:

```bash
OVN_NORTHD_N_THREADS=4
```

Defaults to 1. Choose a value based on the available node CPU resources.

## NetworkPolicy Enforcement Mode

Kube-OVN supports two NetworkPolicy enforcement modes, `standard` and `lax`. The global default can be configured as follows:

```bash
NP_ENFORCEMENT=standard
```

```yaml
args:
- --np-enforcement=standard
```

The mode can also be overridden on individual NetworkPolicies via the `ovn.kubernetes.io/network_policy_enforcement` annotation. See [NetworkPolicy Support](../guide/networkpolicy.en.md) for details.

## Disable VXLAN TX Checksum Offload

Some NICs have compatibility issues with checksum offload during VXLAN tunnel encapsulation, which can be disabled:

```bash
SET_VXLAN_TX_OFF=true
```

```yaml
args:
- --set-vxlan-tx-off=true
```

## KubeVirt Live Migration Optimization

Once enabled, the controller optimizes port-binding switches during KubeVirt live migration to reduce transient packet loss. Enabled by default:

```bash
ENABLE_LIVE_MIGRATION_OPTIMIZE=true
```

## OVN LB Prefer Local Endpoint

Once enabled, the OVN built-in LoadBalancer prefers endpoints on the same node, intended to be used together with `externalTrafficPolicy=Local`:

```bash
ENABLE_OVN_LB_PREFER_LOCAL=true
```

```yaml
args:
- --enable-ovn-lb-prefer-local=true
```

## External Gateway ConfigMap Namespace

ConfigMaps related to the centralized external gateway (such as `external-gw-config`) live in `kube-system` by default. They can be moved to a different namespace via:

```bash
EXTERNAL_GATEWAY_CONFIG_NS=kube-system
```

## Non-Primary CNI Mode

In this mode, Kube-OVN only acts as an attachment network provider and no longer allocates the Pod primary-network IP; the primary network is delegated to another CNI. Both the controller and the daemon must enable this switch:

```yaml
args:
- --non-primary-cni-mode=true
```

It can also be configured via Helm with `cni_conf.NON_PRIMARY_CNI=true` (chart v1) or `cni.nonPrimaryCNI=true` (chart v2). See [Non-Primary CNI Mode](../start/non-primary-mode.en.md) for details.

## Bind Local IP Settings

Services including `kube-ovn-controller`, `kube-ovn-cni`, and `kube-ovn-monitor` support binding to the local IP address. This feature was designed primarily for security considerations in scenarios where services are not permitted to listen on `0.0.0.0` (for example, when a service is deployed on an edge gateway where external users could otherwise directly access it via a public IP and port). This feature is enabled by default and controlled by the following parameter in the installation script:

```bash
ENABLE_BIND_LOCAL_IP=true
```

Taking `kube-ovn-monitor` as an example, when enabled, the service will bind to the local Pod IP:

```bash
# netstat -tunlp |grep kube-ovn
tcp        0      0 172.18.0.5:10661        0.0.0.0:*               LISTEN      2612/./kube-ovn-mon
```

After installation, it can also be adjusted by modifying the environment variable in the Deployment or DaemonSet of the corresponding service:

```yaml
env:
- name: ENABLE_BIND_LOCAL_IP
  value: "false"
```

## TProxy Transparent Proxy Settings

In custom non-default VPC scenarios, workload Pods reside in isolated networks where host kubelets cannot reach the Pod private IP directly from the node IP, causing Kubernetes liveness and readiness probes to fail. When TProxy is enabled, Kube-OVN leverages transparent proxy redirection on the host to ensure probes function properly. This feature is disabled by default.

It can be enabled in the installation script:

```bash
ENABLE_TPROXY=true
```

Or adjusted post-installation by modifying the `kube-ovn-cni` DaemonSet arguments:

```yaml
args:
- --enable-tproxy=true
```

## Underlay ARP IP Conflict Detection Settings

In Underlay physical direct-connect mode, to prevent an assigned Pod IP from conflicting with an existing physical host on the network, Kube-OVN actively sends gratuitous ARP probe packets before activating the address to verify whether the IP is already in use.

This feature is enabled by default. If strict network firewalls cause false positives, it can be adjusted in the installation script:

```bash
ENABLE_ARP_DETECT_IP_CONFLICT=false
```

Or modified post-installation in the `kube-ovn-cni` DaemonSet arguments:

```yaml
args:
- --enable-arp-detect-ip-conflict=false
```

## Gateway Netfilter Mode Settings

The Kube-OVN node daemon requires Linux kernel Netfilter mechanisms to manage gateway traffic redirection and routing rules. This parameter specifies the underlying Netfilter implementation type: `auto` (default auto-detection), `iptables`, or `nftables`. This can be explicitly set on modern Linux distributions that only support nftables (such as Debian 12 or RHEL 9).

It can be configured in the installation script:

```bash
GATEWAY_NETFILTER_MODE=auto
```

Or adjusted post-installation via `kube-ovn-cni` DaemonSet arguments:

```yaml
args:
- --gateway-netfilter-mode=auto
```

## Experimental ACL Traffic Sampling Settings

Kube-OVN supports capturing NetworkPolicy traffic events (such as allowed traffic or default-deny decisions) via the OVN ACL Sampling mechanism for security auditing and network observability.

It can be enabled in the installation script:

```bash
ENABLE_ACL_SAMPLING=true
```

After enabling, configure the parameters in the `kube-ovn-controller` Deployment and `kube-ovn-cni` DaemonSet:

```yaml
args:
- --enable-acl-sampling=true
- --acl-sampling-allow-probability-percent=100
- --acl-sampling-default-deny-probability-percent=100
```

## Garbage Collection and Inspection Interval Settings

The Kube-OVN controller runs background tasks for garbage collection (cleaning up orphaned LSP ports and unbound IPs) and periodic health inspections. You can tune their execution intervals via the following parameters:

```yaml
args:
# Garbage collection interval in seconds; set to 0 to disable GC (default: 360)
- --gc-interval=360
# Inspection and state synchronization interval in seconds (default: 20)
- --inspect-interval=20
```

## Controller Leader Election Tuning Settings

In large-scale clusters, multi-zone deployments, or environments with elevated network latency, default leader election timeouts may trigger premature failovers due to transient jitter. You can fine-tune the controller HA leader election timings via:

```yaml
args:
# Duration that non-leader candidates wait before attempting to acquire leadership (default: 30s)
- --leader-elect-lease-duration=30s
# Duration that the acting leader retries refreshing leadership before giving up (default: 20s)
- --leader-elect-renew-deadline=20s
# Interval between leader election retry attempts (default: 6s)
- --leader-elect-retry-period=6s
```

## TLS Security Specification and Cipher Suites Settings

When enabling secure serving for the API and metrics endpoint (`--secure-serving=true`), you can configure TLS protocol versions and cipher suites to comply with enterprise security baselines:

```yaml
args:
- --secure-serving=true
# Supported values: TLS10, TLS11, TLS12, TLS13
- --tls-min-version=TLS12
- --tls-max-version=TLS13
# Permitted cipher suites (matching Go crypto/tls names, comma-separated)
- --tls-cipher-suites=TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
```


