# Services Served by a VPC NAT Gateway

A VPC NAT gateway can use nftables to provide DNAT for Kubernetes Services. The controller watches Services and EndpointSlices, then programs the gateway backends, VIPs, return routes, and hairpin SNAT. A `LoadBalancer` Service is reachable through its EIP, while traffic inside the VPC can use the Service ClusterIP.

This feature is disabled by default.

## Enable the feature

The controller exposes two independent gates:

| Flag | Purpose | Default |
| --- | --- | --- |
| `--enable-gw-nftable-lb-svc` | Serve the ingress address of a `LoadBalancer` Service through its EIP | `false` |
| `--enable-gw-nftable-svc-cluster-ip` | Hold and serve Service ClusterIPs on the gateway | `false` |

The install script variables are `ENABLE_GW_NFTABLE_LB_SVC` and `ENABLE_GW_NFTABLE_SVC_CLUSTER_IP`. Helm v1/v2 use `func.ENABLE_GW_NFTABLE_LB_SVC`/`features.enableGwNftableLoadbalancerService` and `func.ENABLE_GW_NFTABLE_SVC_CLUSTER_IP`/`features.enableGwNftableServiceClusterIp` respectively.

- `--enable-gw-nftable-svc-cluster-ip` is mutually exclusive with `--enable-lb`; both own the ClusterIP data plane.
- `--enable-gw-nftable-lb-svc` is mutually exclusive with `--enable-lb-svc`; both own the `LoadBalancer` Service ingress address.
- Both gateway gates can be enabled together, or the gateway can serve the EIP while an OVN load balancer serves the ClusterIP.
- `--enable-lb-svc` still needs `--enable-lb` or the gateway ClusterIP gate to provide a ClusterIP data plane.

The old `--enable-nftable-lb-svc` flag defaulted to `true`. It is now split into the two flags above, both defaulting to `false`, with no compatibility alias. Update controller arguments, install script variables, or Helm values before upgrading.

## Configure a Service

A `LoadBalancer` Service must name the gateway and EIP. A ClusterIP Service only needs the gateway annotation:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  annotations:
    ovn.kubernetes.io/vpc_nat_gw: gw1
    ovn.kubernetes.io/eip: eip1 # required for a LoadBalancer Service
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
```

After programming completes, the controller writes `status.loadBalancer.ingress`. Admission does not require the EIP to exist or be Ready; the controller requeues the Service and programs it when the EIP becomes available. Backends come only from EndpointSlices, and all Ready backends participate in load balancing. An in-place Multus interface address change on a running Pod does not trigger an EndpointSlice update.

`IptablesDnatRule` objects with `type: share` are controller-owned accounting records. Operators cannot create, edit, or delete them, and they do not directly drive the data plane. Inspect the programmed state with:

```bash
kubectl get iptables-dnat-rules -l ovn.kubernetes.io/nftable-lb-svc-name=web
kubectl -n kube-system exec <vpc-nat-gw-pod> -- nft list table ip kube-ovn
kubectl -n kube-system exec <vpc-nat-gw-pod> -- ip -4 addr show dev lo label lo:ko-vip
kubectl ko nbctl lr-policy-list <vpc>
```

## Constraints and upgrade notes

- One EIP, port, and protocol identity can belong to only one Service; webhook validation rejects conflicts.
- The Service EIP must belong to the annotated gateway. An EIP in use cannot be deleted before the Service is removed.
- The gateway and EIP binding is immutable; delete and recreate the Service to change it. Clear both the gateway and EIP annotations to leave this mode; the controller releases records, VIP routes, loopback addresses, and the finalizer.
- `ovn.kubernetes.io/vpc_nat_gw` and `ovn.kubernetes.io/service_external_ip_from_subnet` are mutually exclusive so a Service cannot publish two ingress addresses.
- Deleting a gateway releases its Service records, published ingress state, and finalizer. Normally the webhook rejects deleting a gateway that still has EIP or ClusterIP bindings.
- Only IPv4, TCP/UDP, and `Cluster` traffic policy are supported. Node-local traffic policy, topology-aware routing, and client source address preservation are not supported.
- `ClientIP` session affinity is supported for the whole VIP identity. Multi-NIC backends must have an available NIC in the gateway VPC.
