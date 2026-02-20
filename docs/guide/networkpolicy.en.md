# NetworkPolicy Usage

NetworkPolicy is a network policy interface provided by Kubernetes to control network traffic between Pods and between Pods and other network endpoints.
Kube-OVN implements the Kubernetes NetworkPolicy specification through OVN's ACL mechanism, providing two different enforcement modes to adapt to different scenarios and NetworkPolicy logging to troubleshoot NetworkPolicy rules.

## Implementation Mechanism in Kube-OVN

Kube-OVN implements NetworkPolicy through OVN (Open Virtual Network) native capabilities, primarily using three OVN components:

### Port Group

When a NetworkPolicy is created, Kube-OVN creates a Port Group for that policy to organize all logical ports of Pods matching the `podSelector` together.
The Port Group name format is `<policy-name>.<namespace-name>`, where `-` is replaced with `.`.

### Address Set

Address Sets are used to store the set of IP addresses that are allowed or denied access as defined in NetworkPolicy rules. For each NetworkPolicy rule,
Kube-OVN calculates the corresponding IP addresses based on `podSelector`, `namespaceSelector`, or `ipBlock` and stores them in Address Sets.

Two types of Address Sets are created for each NetworkPolicy's Ingress and Egress rules: Allow and Except:

- `<policy-name>.<namespace-name>.ingress.allow`: Allowed ingress IP addresses
- `<policy-name>.<namespace-name>.ingress.except`: Excluded ingress IP addresses
- `<policy-name>.<namespace-name>.egress.allow`: Allowed egress IP addresses
- `<policy-name>.<namespace-name>.egress.except`: Excluded egress IP addresses

### ACL (Access Control List)

ACL is the component in OVN that actually performs traffic control. Kube-OVN converts NetworkPolicy rules into OVN ACL rules
and associates them with the corresponding Port Group. ACL rules contain match conditions, priorities, and actions (allow or deny).

ACL priority ranges used by Kube-OVN for NetworkPolicy:

- Ingress Allow rules: Priority 2001
- Egress Allow rules: Priority 2001
- Default Deny rules: Priority 1000

Through this approach, Kube-OVN can efficiently implement Kubernetes NetworkPolicy semantics and fully leverage OVN's distributed ACL capabilities.

## Notes

### Relationship with Other Access Control Mechanisms

Kube-OVN supports multiple network access control mechanisms:

- **NetworkPolicy**: Kubernetes standard network policy
- **Network Policy API**: AdminNetworkPolicy and BaselineAdminNetworkPolicy
- **Subnet ACL**: Subnet-level access control
- **Security Group**: Security groups

These mechanisms are all implemented through OVN ACLs at the underlying level. Although NetworkPolicy and Network Policy API are designed with rule layering to avoid priority conflicts,
using multiple access control mechanisms simultaneously may lead to complex rule management and priority conflicts. **It is recommended not to use multiple access control rules simultaneously.**

### Named Port Limitations

The NetworkPolicy specification supports using Named Ports to specify ports, for example:

```yaml
ports:
- protocol: TCP
  port: http
```

Kube-OVN has limitations on Named Port support: **Currently only Named Ports mapping to the same port number are supported**.

If multiple Pods in the cluster use the same Named Port name but map to different port numbers, NetworkPolicy will not work correctly and may cause errors.
For example, if Pod A's `http` port maps to 8080 while Pod B's `http` port maps to 8081, NetworkPolicy rules using `port: http` will have issues.

It is recommended to ensure that all relevant Pods' ports with the same name map to the same port number when using Named Ports, or use numeric port numbers directly to avoid this issue.

### Performance Impact of IPBlock Except Rules

NetworkPolicy's `ipBlock` rules support the `except` field to exclude specific IP address ranges:

```yaml
egress:
- to:
  - ipBlock:
      cidr: 10.0.0.0/8
      except:
      - 10.0.1.0/24
      - 10.0.2.0/24
```

In OVN's flow table implementation, `except` rules cause significant flow table bloat. Each `except` subnet requires additional ACL rules to implement,
which increases the size of the OVN database and the complexity of flow table processing, negatively impacting network performance.

**It is recommended to avoid using `except` rules whenever possible.** If you must exclude certain IP address ranges, consider the following alternatives:

- Split the CIDR into multiple non-overlapping smaller segments and directly specify the allowed segments
- Use more precise `podSelector` or `namespaceSelector` instead of IP address filtering

## NetworkPolicy Logging

Kube-OVN provides NetworkPolicy logging functionality to help administrators quickly determine whether network policy rules are effective and troubleshoot network connectivity issues.

!!! warning

    Once NetworkPolicy logging is enabled, logs need to be printed for every packet that matches a rule, which introduces additional performance overhead.
    In malicious attack scenarios, a large number of logs in a short period may exhaust CPU resources.
    
    It is recommended to disable logging by default in production environments and only enable it dynamically when troubleshooting issues.
    
    You can use the `ovn.kubernetes.io/acl_log_meter_rate` annotation to limit the rate of ACL log generation to avoid performance issues caused by excessive logs.

### Enable Logging

Add the annotation `ovn.kubernetes.io/enable_log` to the NetworkPolicy where logging needs to be enabled:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
  annotations:
    ovn.kubernetes.io/enable_log: "true"
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

After enabling logging, only denied (Drop) traffic logs will be recorded by default.

### View Logs

Logs are recorded in the `/var/log/ovn/ovn-controller.log` file on the node where the Pod is located:

```bash
# tail -f /var/log/ovn/ovn-controller.log
2022-07-20T05:55:03.229Z|00394|acl_log(ovn_pinctrl0)|INFO|name="np/default-deny-ingress.default/IPv4/0", verdict=drop, severity=warning, direction=to-lport: udp,vlan_tci=0x0000,dl_src=00:00:00:21:b7:d1,dl_dst=00:00:00:8d:0b:86,nw_src=10.16.0.10,nw_dst=10.16.0.7,nw_tos=0,nw_ecn=0,nw_ttl=63,tp_src=54343,tp_dst=53
```

The logs contain detailed five-tuple information (source IP, destination IP, protocol, source port, destination port), making it easy to troubleshoot issues.

### Logging Allowed Traffic

Starting from Kube-OVN v1.13.0, the `ovn.kubernetes.io/log_acl_actions` annotation can be used to log allowed traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-client
  namespace: default
  annotations:
    ovn.kubernetes.io/enable_log: "true"
    ovn.kubernetes.io/log_acl_actions: "allow"
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: client
```

The value of `ovn.kubernetes.io/log_acl_actions` can be:

- `drop`: Only log denied traffic (default)
- `allow`: Only log allowed traffic
- `allow,drop`: Log both allowed and denied traffic

View logs for allowed traffic:

```bash
# tail -f /var/log/ovn/ovn-controller.log
2024-08-14T09:27:49.590Z|00004|acl_log(ovn_pinctrl0)|INFO|name="np/allow-from-client.default/ingress/IPv4/0", verdict=allow, severity=info, direction=to-lport: icmp,vlan_tci=0x0000,dl_src=96:7b:b0:2f:a0:1a,dl_dst=a6:e5:1b:c2:1b:f8,nw_src=10.16.0.7,nw_dst=10.16.0.12,nw_tos=0,nw_ecn=0,nw_ttl=64,nw_frag=no,icmp_type=8,icmp_code=0
```

### Rate Limiting Logs

To avoid performance issues caused by excessive logs, you can limit the log output rate using the `ovn.kubernetes.io/acl_log_meter_rate` annotation:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-client
  namespace: default
  annotations:
    ovn.kubernetes.io/enable_log: "true"
    ovn.kubernetes.io/log_acl_actions: "allow"
    ovn.kubernetes.io/acl_log_meter_rate: "100"
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: client
```

The value of `ovn.kubernetes.io/acl_log_meter_rate` represents the maximum number of log entries allowed per second, measured in logs per second. For example, setting it to `100` means at most 100 log entries will be output per second.

### Disable Logging

Set the annotation `ovn.kubernetes.io/enable_log` to `false` to disable logging:

```bash
kubectl annotate networkpolicy -n default allow-from-client ovn.kubernetes.io/enable_log=false --overwrite
```

## Policy Enforcement Modes

Kube-OVN supports two enforcement modes with different strictness levels:

- **standard**: Default mode that strictly enforces policies according to the NetworkPolicy specification. Any IP traffic not in the rules will be denied.
- **lax**: Relaxes restrictions in certain scenarios to provide better compatibility. In this mode, only TCP/UDP/SCTP traffic is denied, meaning ICMP or other L4 protocol IP traffic not in the rules will be allowed, and DHCP UDP traffic is also allowed to better accommodate virtualization scenarios.

You can specify the enforcement mode by adding an annotation to the NetworkPolicy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example-policy
  namespace: default
  annotations:
    ovn.kubernetes.io/enforcement: "lax"
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

You can also globally configure the default enforcement mode using the `--network-policy-enforcement` parameter when starting the Kube-OVN controller.

## See also

- [Multi-network NetworkPolicy](./multi-network-policy.en.md)
