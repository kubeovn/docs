# VPC Egress Gateway Observability

VPC Egress Gateway can run one native observability sidecar in every gateway Pod. The sidecar can expose internal and external interface counters, expose low-cardinality conntrack NAT metrics, and write versioned NAT flow logs to its container standard output. All three capabilities are disabled by default and do not affect gateway data-plane readiness.

## Requirements and Upgrade Notes

- Kubernetes 1.29 or later with the `SidecarContainers` feature enabled is required because the observer uses a [restartable init container](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/). The controller performs a server-side dry-run with a zero-replica Deployment and verifies that the API server preserves the restartable-init policy. If the version is too old, the feature is disabled, or the capability cannot be verified, the controller does not inject the observer and sets `ObservabilityConfigured=False`; the gateway data plane continues to reconcile normally. Transient capability-probe errors are retried.
- Upgrade the `vpc-egress-gateways.kubeovn.io` CRD explicitly before creating resources that use `spec.observability`. Helm does not upgrade CRDs that are already installed automatically. Apply the CRD delivered with the same Kube-OVN version, using your normal CRD upgrade procedure.
- Conntrack collection requires `NET_ADMIN` in the gateway Pod network namespace. The official observer binary carries only the `CAP_NET_ADMIN` file capability, while the generated container security context admits only `NET_ADMIN` into the capability bounding set. `allowPrivilegeEscalation` is enabled so that this trusted file capability survives the non-root launcher `exec`; the observer still runs as UID and GID 65534, drops all other capabilities, and uses a read-only root filesystem.
- Prometheus Operator is optional. The gateway works without the ServiceMonitor CRD.

## Enabling Observability

The following example enables both metrics collectors and JSON flow logs:

```yaml
apiVersion: kubeovn.io/v1
kind: VpcEgressGateway
metadata:
  name: gateway1
  namespace: default
spec:
  vpc: ovn-cluster
  replicas: 2
  externalSubnet: macvlan1
  policies:
    - snat: true
      subnets:
        - ovn-default
  observability:
    resources:
      requests:
        cpu: 20m
        memory: 64Mi
      limits:
        cpu: 200m
        memory: 256Mi
    interfaceMetrics:
      enabled: true
    conntrack:
      metrics:
        enabled: true
      log:
        enabled: true
        events: [start, end]
        rateLimit:
          recordsPerSecond: 100
          burst: 1000
        filters:
          include: []
          exclude: []
    serviceMonitor:
      labels:
        monitoring: platform
      annotations: {}
```

When `resources` is empty or omitted, the observer requests `20m` CPU and `64Mi` memory and is limited to `200m` CPU and `256Mi` memory.
The interface-only mode is continuously tested to remain at or below `20MiB` of steady-state resident memory; the larger default request leaves room for conntrack cache and log-queue growth.

The controller stores the runtime configuration in a per-gateway ConfigMap. Collector switches, flow-log events, filters, and rate limits are reloaded without replacing gateway Pods. The following changes update the Deployment and replace Pods:

- enabling observability for the first time;
- disabling all observability capabilities;
- changing `observability.resources`;
- changing the gateway workload image.

If an explicitly selected older workload image does not contain `/kube-ovn/vpc-egress-gateway-observer`, the launcher runs `sleep infinity` instead, so the missing binary does not block the data plane. A custom image that does contain the observer must preserve its `CAP_NET_ADMIN` file capability; otherwise, interface metrics remain available but conntrack metrics and flow logs report collector errors.

## Metrics

The observer serves `/metrics` and `/healthz` on TCP port `10666`. It uses a private Prometheus registry and does not expose `go_*`, `process_*`, or `promhttp_*` metrics. Every metric includes the identity labels `namespace`, `name`, `pod`, and `node`.

### Interface Metrics

Interface metrics are read from `/proc/net/dev` on every scrape. The observer resolves the primary interface and the external Multus interface from the Pod `network-status` annotation on the first successful scrape and caches those names for the lifetime of the process.

| Metric | Additional labels | Description |
| :--- | :--- | :--- |
| `kube_ovn_vpc_egress_gateway_interface_rx_bytes_total` | `interface`, `type` | Received bytes. |
| `kube_ovn_vpc_egress_gateway_interface_tx_bytes_total` | `interface`, `type` | Transmitted bytes. |
| `kube_ovn_vpc_egress_gateway_interface_rx_packets_total` | `interface`, `type` | Received packets. |
| `kube_ovn_vpc_egress_gateway_interface_tx_packets_total` | `interface`, `type` | Transmitted packets. |
| `kube_ovn_vpc_egress_gateway_interface_drops_total` | `interface`, `type`, `direction` | Dropped packets. |
| `kube_ovn_vpc_egress_gateway_interface_errors_total` | `interface`, `type`, `direction` | Packet errors. |

The `type` label is `internal` or `external`, and `direction` is `rx` or `tx`.

### Conntrack Metrics

Conntrack metrics aggregate flows without using IP addresses or ports as labels:

| Metric | Additional labels | Description |
| :--- | :--- | :--- |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_flows_active` | `address_family`, `protocol`, `nat_type` | Current NAT flows initialized from the table dump and maintained from events. |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_flows_started_total` | `address_family`, `protocol`, `nat_type` | NAT flows observed starting after the observer subscribed. |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_flows_ended_total` | `address_family`, `protocol`, `nat_type` | NAT flow end events observed. |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_packets_total` | `address_family`, `protocol`, `nat_type`, `direction` | Packets observed when conntrack accounting is available. |
| `kube_ovn_vpc_egress_gateway_conntrack_nat_bytes_total` | `address_family`, `protocol`, `nat_type`, `direction` | Bytes observed when conntrack accounting is available. |

`address_family` is `ipv4` or `ipv6`. Known `protocol` values are `tcp`, `udp`, `sctp`, `icmp`, and `icmpv6`; all other protocol numbers are aggregated as `other`. `nat_type` is `snat`, `dnat`, or `snat_dnat`, and `direction` is `original` or `reply`.

Operational metrics use the `kube_ovn_vpc_egress_gateway_observability_*` prefix. They report collector availability, configuration reload results, conntrack events and errors, cache entries/capacity/evictions, emitted and dropped log records, and conntrack accounting availability. One collector failing does not make `/metrics` fail or suppress data from the other collector.

## ServiceMonitor Discovery

When either metrics collector is enabled, the controller creates a per-gateway headless Service with `publishNotReadyAddresses: true` and a numeric `targetPort` of `10666`. It also creates a ServiceMonitor in the gateway namespace. User labels and annotations from `observability.serviceMonitor` are merged into the ServiceMonitor metadata, but controller-required selector labels cannot be overridden.

If the ServiceMonitor CRD is absent, the controller sets `ServiceMonitorReady=False` and retries periodically. It creates the ServiceMonitor automatically after the CRD becomes available. This condition is separate from the existing gateway `Ready` condition.

## JSON Flow Logs

Flow logs are JSON Lines written only to the `observability` container standard output. Diagnostics are written to standard error. Read the records with:

```shell
kubectl logs -n default <gateway-pod> -c observability
```

The `v1` schema emits `start` and `end` lifecycle records. Raw conntrack update events are not logged. A record resembles:

```json
{"schemaVersion":"v1","timestamp":"2026-08-05T03:40:00Z","event":"end","conntrackID":2471802592,"zone":0,"namespace":"default","name":"gateway1","pod":"gateway1-7c9b8f8db7-r9x8m","node":"worker-1","addressFamily":"ipv4","protocol":"tcp","protocolNumber":6,"natType":["snat"],"original":{"sourceIP":"10.16.0.25","sourcePort":42136,"destinationIP":"203.0.113.10","destinationPort":443},"translated":{"sourceIP":"172.17.0.11","sourcePort":42136,"destinationIP":"203.0.113.10","destinationPort":443},"counters":{"originalPackets":8,"originalBytes":624,"replyPackets":7,"replyBytes":591}}
```

For protocols aggregated as `other`, `protocolNumber` retains the original IP protocol number. `natType` is a stable sorted array and can contain both `dnat` and `snat`. The `counters` object is omitted when conntrack accounting is unavailable; the observer never changes `nf_conntrack_acct`.

The observer subscribes to conntrack events before dumping the existing table. Existing NAT flows initialize the active-flow metric and cache, but do not produce historical `start` logs. The cache is limited to 65,536 entries. The netlink event channel and asynchronous log queue are each limited to 4,096 entries. A blocked container log consumer or full log queue drops log records without blocking conntrack collection.

By default, all NAT flows and both lifecycle events are logged, subject to a per-Pod limit of 100 records per second with a burst of 1,000. These are operational, best-effort records and metrics; they are not intended for billing-grade accounting.

## Flow-log Filters

Each include or exclude rule can match address families, protocols, NAT types, and fields in the original or translated tuple. Values within one field are ORed, configured fields within one rule are ANDed, and rules in one list are ORed. Exclude rules take precedence over include rules. An empty include list matches every NAT flow.

Ports use inclusive structured ranges. The following configuration logs TCP SNAT flows from `10.16.0.0/16` to destination ports 80 through 443, except translated destinations in `192.0.2.0/24`:

```yaml
spec:
  observability:
    conntrack:
      log:
        enabled: true
        filters:
          include:
            - protocols: [tcp]
              natTypes: [snat]
              original:
                sourceCIDRs: [10.16.0.0/16]
                destinationPorts:
                  - start: 80
                    end: 443
          exclude:
            - translated:
                destinationCIDRs: [192.0.2.0/24]
```
