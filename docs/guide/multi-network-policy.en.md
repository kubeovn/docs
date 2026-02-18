# Multi-network NetworkPolicy

## Overview

By default, Kube-OVN applies a NetworkPolicy to all OVN interfaces selected by `podSelector`.

For multi-network pods, you can scope a policy to specific providers with:

- `ovn.kubernetes.io/network_policy_for`

This lets one policy affect only selected interfaces instead of all interfaces on the pod.

## Annotation format

Use comma-separated entries:

```yaml
metadata:
  annotations:
    ovn.kubernetes.io/network_policy_for: "ovn,default/net-a,default/net-b"
```

Supported entry formats:

- `ovn` (default OVN provider)
- `<namespace>/<net-attach-def>`

Examples:

- `ovn`
- `default/net-a`
- `ovn,default/net-a`

## Provider matching behavior

- Annotation omitted: apply to all OVN providers (existing behavior).
- Invalid entries are ignored and logged.
- If all entries are invalid, no providers are selected, so the policy selects no ports.
- Duplicate entries are de-duplicated.

`<namespace>/<net-attach-def>` is internally mapped to the provider name format used by Kube-OVN:

- `<nad-name>.<nad-namespace>.ovn`

## Service ClusterIP behavior

When policy peers are resolved to addresses, Service ClusterIP is included only if the selected provider belongs to the **default VPC**.

For providers in custom VPCs, Service ClusterIP is not added.

## Example

Assume pods have these interfaces:

- default OVN provider (`ovn`)
- `default/net-a`
- `default/net-b`

Then:

- `network_policy_for` omitted:
  - policy applies to `ovn`, `net-a`, and `net-b`
- `network_policy_for: default/net-a`:
  - policy applies only to `net-a`
- `network_policy_for: ovn,default/net-b`:
  - policy applies to `ovn` and `net-b`

## Notes

- This annotation scopes **where** a policy is enforced (provider/interface), not Kubernetes NetworkPolicy semantics themselves.
- Keep policy names and annotation values explicit to avoid accidental over/under-scoping.
