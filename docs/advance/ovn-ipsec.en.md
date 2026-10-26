# Encrypt Node Traffic with IPsec

Kube-OVN can use the IPsec capability built into OVN/OVS to encrypt Geneve,
VXLAN, and STT tunnels between nodes. The IPsec runtime now runs in a separate
`ipsec` container in the `kube-ovn-cni` Pod. The CNI container no longer issues
certificates, starts IKE/strongSwan, watches the CA Secret, or flushes host XFRM
state.

## Prerequisites

- Allow UDP 500 (IKE) and UDP 4500 (NAT-T) between nodes.
- Enable kernel modules such as `xfrm` and `af_key`, and provide the
  strongSwan or libreswan runtime required by OVN/OVS IPsec.
- Use an image that contains the IPsec agent and the matching OVN/OVS output
  protection patch. The agent rejects an image that does not advertise this
  capability before it issues an identity or allocates a lease.

## Certificates and the initial enable sequence

Keep IPsec disabled while preparing the certificate path and the ordinary Pod
network:

1. Install or upgrade Kube-OVN with `ENABLE_OVN_IPSEC=false` (or the equivalent
   Helm value).
2. If using an external signer, deploy cert-manager and its CA injector, create
   a dedicated ClusterIssuer, and wait for cert-manager and the ClusterIssuer to
   become `Ready`.
3. Confirm that the controller and CNI DaemonSet are ready and that the ordinary
   Pod network can reach the Kubernetes API. No `hostNetwork` override is needed
   for cert-manager.
4. Enable IPsec on the controller and CNI, then wait for the rollout to finish.

The built-in signer does not require cert-manager, but the controller and the
ordinary network should still be prepared while IPsec is disabled. Nodes always
submit a Kubernetes CSR. The controller validates the bound Pod, Node UID,
chassis, and requested CN/SAN before signing it or forwarding it to cert-manager.
The CNI ServiceAccount cannot create CertificateRequests; only the controller can
forward an authorized CSR to the configured ClusterIssuer.

## Enable IPsec

The install script can enable IPsec with:

```bash
ENABLE_OVN_IPSEC=true
```

The v1 chart uses `ENABLE_OVN_IPSEC`; the v2 chart uses
`features.enableOvnIpsec`. For cert-manager signing, also enable
`--cert-manager-ipsec-cert=true` (v1) or the chart's
`ipsec.certManager.enabled` and set the dedicated issuer name. Certificate
duration, request timeout, priority, and resource limits are in the chart's
`ipsec` section.

When enabled, the CNI Pod renders an `ipsec` container from the same image and
runs `/kube-ovn/kube-ovn-ipsec`. This container owns the IPsec key directory and
gets `NET_ADMIN`, `NET_BIND_SERVICE`, and `SYS_NICE` for the IPsec runtime. The
CNI container explicitly drops `SYS_NICE`; enabling IPsec does not grant it extra
scheduling or key-directory privileges. The Pod still shares host networking,
the host PID namespace, and its ServiceAccount, so the `ipsec` container is not a
separate Kubernetes identity.

The controller coordinates the initial enable: it freezes the DaemonSet UID, Pod
template, trust bundle, and target Node UIDs; waits for every node to prepare its
identity and pass the local agent gate; then installs protection and starts the
runtime before switching the global OVN IPsec setting. Pod readiness or an
unsigned Node annotation cannot satisfy this barrier. The CNI DaemonSet uses
`maxSurge: 0` and `maxUnavailable: 1` so only one node is replaced at a time and
existing protection remains armed.

## Runtime and renewal

The IPsec agent persists pending private keys, CSR bindings, and the active
identity generation. It activates a complete key, certificate, and trust
generation in one OVSDB update while preserving unrelated `other_config` entries.
Renewal is jittered between 40% and 60% of the leaf lifetime so nodes do not all
renew at the same midpoint. A failed renewal does not replace an existing valid
identity. The agent supervises foreground IKE and monitor processes and backs off
runtime failures from one to thirty seconds.

Status and readiness expose only the Node UID, chassis, generation, and public
certificate/trust digests. They never expose PEM data, private keys, or SA keys.
`readyz` requires an unexpired certificate, healthy processes, read-back kernel
protection, and acknowledgement of the current trust digest by the local monitor.
This confirms a configuration refresh, not that every old peer SA has been
recreated. An IPsec readiness failure makes the Pod NotReady without restarting
the CNI container.

Check a node with:

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=kube-ovn-cni
kubectl get csr
kubectl get clusterissuer
kubectl exec -n kube-system <kube-ovn-cni-pod> -c ipsec -- \
  ovs-appctl ipsec/show
```

## Disable and bounded cleanup

Disabling IPsec is not just removing the `ipsec` container. Set the controller and
CNI IPsec switches to `false`. The controller persists a `Disabling` challenge and
uses synchronous NB/SB reads to confirm that both database switches are off. The
chart and install script then replace the `ipsec` container with a one-shot
`ipsec-cleanup` init container:

- It exits successfully when no previous IPsec state exists. It never starts
  IKE/monitor, reads a CA, issues a certificate, or imports a legacy identity.
- It runs as root only during initialization, with `NET_ADMIN` and
  `NET_BIND_SERVICE`, without `SYS_NICE`. It has no `restartPolicy`, probes, or
  resident cleanup process.
- It checks local tunnel convergence, owned connections and SAs, and the current
  Node UID, Pod UID, CSR, template, and controller challenge. Missing evidence,
  foreign owners, or an incomplete drain retain protection and make that node
  retry later.
- Only after live checks pass does it withdraw its own output lease and protection
  guards, write a signed release receipt, and exit. It never removes SAs, policies,
  or interfaces owned by another actor.

The controller records `Disabled` only after verifying every frozen node receipt,
which supports a serial `maxUnavailable: 1` rollout. A completed init result is
reusable only for the same live Pod, template, and Release epoch; running or failed
init containers cannot satisfy the Release barrier. The controller creates no
extra DaemonSet and requires no additional Kubernetes permissions. A local cleanup
failure keeps that node protected for a controlled retry.

## Troubleshooting and privilege boundaries

- An IPsec CSR from `kubectl get csr` must belong to the current
  `kube-ovn-cni` Pod and Node UID; never identify it by request name alone.
- With cert-manager, dedicate the ClusterIssuer to Kube-OVN IPsec. The controller
  validates the issuer, namespace, requester ServiceAccount, usages, lifetime, and
  returned chain. Generic cert-manager auto-approval cannot bypass this path.
- Controller Secret, CSR, and cert-manager permissions are restricted to its
  configured namespace. CNI must not be allowed to create CertificateRequests.
- When `ovs-appctl ipsec/show` or agent `readyz` fails, check certificate digests,
  monitor read-back, kernel guards, and UDP 500/4500 connectivity before reading
  OVN/OVS logs.
- Do not manually delete XFRM SAs, the IPsec key directory, or the
  `ovn-ipsec-coordination` ConfigMap. They are managed together by the protected
  controller and agent lifecycle.
