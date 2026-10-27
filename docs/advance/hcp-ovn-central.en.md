# Hosted OVN Central

The hosted control plane (HCP) mode runs `ovn-central` as a dedicated,
PVC-backed StatefulSet for workload clusters. It keeps the OVN northbound and
southbound databases outside the workload cluster and exposes their addresses
through the HCP configuration.

HCP mode is available in both chart layouts:

- Classic chart: `ovn-central.hcp.*`
- v2 chart: `central.hcp.*`

## Configuration

Create the HCP namespace before installing the chart. The Helm release can
remain in the regular Kube-OVN namespace while HCP resources are rendered in
the namespace selected by `hcp.namespace`.

```bash
kubectl create namespace hcp
```

The following is a classic chart example. `nbAddress` and `sbAddress` must be
set when HCP is enabled. Include the connection scheme and port in each
address, and use an address reachable by workload clusters.

```yaml
namespace: kube-system

ovn-central:
  hcp:
    enabled: true
    namespace: hcp
    replicas: 3
    nbAddress: tcp:ovn-nb.example.com:6641
    sbAddress: tcp:ovn-sb.example.com:6642
    service:
      type: NodePort
      nbNodePort: 30641
      sbNodePort: 30642
    storage:
      size: 5Gi
      storageClassName: ""
```

The v2 chart uses the same settings under `central.hcp`:

```yaml
central:
  hcp:
    enabled: true
    namespace: hcp
    replicas: 3
    nbAddress: tcp:ovn-nb.example.com:6641
    sbAddress: tcp:ovn-sb.example.com:6642
    service:
      type: NodePort
      nbNodePort: 30641
      sbNodePort: 30642
    storage:
      size: 5Gi
      storageClassName: ""
```

Install the chart with the values file after the namespace exists:

```bash
helm upgrade --install kube-ovn ./charts/kube-ovn -n kube-system -f hcp-values.yaml
```

Use the v2 chart path instead of `./charts/kube-ovn` when installing the v2
chart.

## Resources and scheduling

When HCP is enabled, the chart creates the following resources in
`hcp.namespace`:

- An `ovn-central` StatefulSet with `hcp.replicas` pods. The default is three.
- A PVC-backed `ovn-data` volume for every StatefulSet pod. The default request
  is 5Gi and `ReadWriteOnce`; set `storageClassName` when the cluster does not
  have a suitable default StorageClass.
- A headless `ovn-central` Service for the internal Raft ports 6643 and 6644.
- `ovn-nb` and `ovn-sb` Services for client traffic on ports 6641 and 6642.

Each HCP pod has required pod anti-affinity on `kubernetes.io/hostname`, so the
scheduler will not place two `ovn-central` pods on the same node. The pods
also tolerate `NoSchedule`, `NoExecute`, and `CriticalAddonsOnly` taints and
are restricted to Linux nodes by the chart. The classic chart additionally
accepts `ovn-central.nodeSelector`. The v2 chart accepts user-defined
`central.nodeAffinity` rules; HCP mode does not add the normal master-node
affinity, so use these values to select the nodes that should host the
StatefulSet.

## Service exposure

The HCP `service.type` defaults to `NodePort`. The default node ports are
30641 for NB and 30642 for SB. Set `service.type` to `LoadBalancer` when the
cluster provides an external load balancer. The `nbNodePort` and `sbNodePort`
values are used for the NB/SB Services when the type is `NodePort` or
`LoadBalancer`.

Only the NB and SB Services are intended for workload-cluster connections.
The headless `ovn-central` Service is for the StatefulSet's internal Raft
traffic, and `ovn-northd` remains a ClusterIP Service for in-cluster use.
Make sure the host and port in `nbAddress` and `sbAddress` resolve to the
exposed NB/SB Services from every workload cluster.

## Boundaries

HCP mode only changes how `ovn-central` is deployed and exposed. It does not
install the workload-cluster agents or CRDs into a separate cluster. Install
the workload cluster's Kube-OVN components with the data-plane configuration
and point their OVN NB/SB endpoints at the HCP `nbAddress` and `sbAddress`.

The HCP namespace, storage class, node placement, and externally reachable
NB/SB addresses are operator-managed prerequisites. Verify that all three
replicas can bind their PVCs and that workload-cluster nodes can reach both
service ports before creating network resources.
