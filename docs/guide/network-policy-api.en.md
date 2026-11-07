# Network Policy API

Kube-OVN uses `network-policy-api v0.3.0` to provide the `v1beta1`
`ClusterNetworkPolicy` (CNP) API. To enable ANP/CNP and DNS-name-based access
control, see [Domain-based Access Control](./egress-firewall.en.md) for the
controller and DNS resolver configuration.

## Port Matching with `protocols`

CNP ingress and egress rules use `protocols` to express transport protocols and
destination ports. For example:

```yaml
protocols:
  - tcp:
      destinationPort:
        number: 443
  - udp:
      destinationPort:
        range:
          start: 8000
          end: 9000
```

TCP, UDP, and SCTP numeric ports and port ranges are supported.
`destinationNamedPort` resolves a named port against the destination Pods
selected by the rule and supports every protocol and port number exposed by
that name. Named ports can target Pods or Namespaces; Node, Network, and
domain-name peers do not provide destination Pods for named-port resolution.

Omitting `protocols` leaves the rule unrestricted by transport protocol and
destination port. Domain-name peers require the DNS resolver and an `Accept`
action.

## Priority and tiers

`spec.priority` accepts values from `0` through `399`; lower values have higher
priority. Multiple CNPs in the same tier may use the same priority. The
controller creates separate ACLs for each policy and rule. ANP and BANP keep
their own priority constraints from the Network Policy API specification; the
CNP same-tier rule does not make shared priorities valid for those policies.

## Migration from Older Versions

Convert existing CNP manifests from `ports` to `protocols` before using the
`network-policy-api v0.3.0` controller and CRD. This release does not migrate
objects automatically, does not accept the legacy `ports` format, and does not
provide reverse migration.

The v0.3.0 CRD serves both `v1alpha2` and `v1beta1`, with `v1beta1` as the
storage version. Both versions use the same v0.3.0 `protocols` schema and
require no conversion webhook. Existing `v1alpha2` objects that use this
schema remain readable and writable through `v1beta1`; updating the CRD alone
does not rewrite stored objects or convert the legacy `ports` field to
`protocols`. CNP objects from v1.16 and earlier may still use `ports` and must
be converted explicitly; `apiVersion: v1alpha2` alone does not prove that an
object can be upgraded directly.

ANP and BANP continue to use their independent `v1alpha1` CRDs;
`network-policy-api v0.3.0` publishes only the CNP conformance profile and does
not change the ANP/BANP version constraints.
