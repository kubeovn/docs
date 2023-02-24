# VIP Reservation

In some scenarios we want to dynamically reserve part of the IP but not assign it to Pods but to other infrastructure e.g:

- Kubernetes nested Kubernetes scenarios where the upper Kubernetes uses the Underlay network take up the available addresses of the underlying Subnet.
- LB or other network infrastructure requires the use of an IP within a Subnet.

## Create Random Address VIP

If you just want to set aside a number of IPs and have no requirement for the IP addresses themselves, you can use the following yaml to create them:

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: vip-dynamic-01
spec:
  subnet: ovn-default
```

- `subnet`: reserve the IP from this Subnet.

Query the VIP after creation.

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
vip-dynamic-01   10.16.0.12           00:00:00:F0:DB:25                         ovn-default   true
```

It can be seen that the VIP is assigned the IP address `10.16.0.12`, which can later be used by other network infrastructures.

## Create a fixed address VIP

The IP address of the reserved VIP can be fixed using the following yaml:

```yaml
apiVersion: kubeovn.io/v1
kind: Vip
metadata:
  name: static-vip01
spec:
  subnet: ovn-default 
  V4ip: "10.16.0.121"
```

- `subnet`: reserve the IP from this Subnet.
- `V4ip`: A fixed-assigned IP address that should within the CIDR range of `subnet`.

Query the VIP after creation:

```bash
# kubectl get vip
NAME             V4IP         PV4IP   MAC                 PMAC   V6IP   PV6IP   SUBNET        READY
static-vip01   10.16.0.121           00:00:00:F0:DB:26                         ovn-default   true
```

It can be seen that the VIP has been assigned the expected IP address.
