# 双栈网络

在 KubeVirt 的 Bridge 网络模式下，DHCP 服务由 virt-launcher 提供。然而，当前 KubeVirt 仅实现了 IPv4 单栈的 DHCP，导致 Bridge 模式的 KubeVirt VM 无法通过 RA 协议动态获取 IPv6 地址。尽管 Kube-OVN 提供了 DHCP 和 RA 功能，但由于 KubeVirt 提前拦截了 DHCP/RA 请求，这些功能无法生效。

在 KubeVirt 1.4.0 之后的版本，新的 Network Binding Plugin 提供了类似 Bridge 的网络模式 `managedTap`，该模式下 KubeVirt 不会做 DHCP 拦截。因此通过新的 `managedTap` 模式和 Kube-OVN 的 DHCP/RA 能力，可以实现 VM 的双栈网络地址自动获取。

## 配置双栈 DHCP

在 Kube-OVN 的 Subnet 中开启 DHCP 和 IPv6 RA 功能，如下面的 YAML 配置所示：

```yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
  name: dual-stack-subnet
spec:
  cidrBlock: "10.244.0.0/16,fd00:10:244::/64"
  enableDHCP: true
  enableIPv6RA: true
```

## 配置 `managedTap` 类型网络

在 KubeVirt 中注册 `managedTap` 的 Network Binding Plugin:

```bash
# kubectl patch kubevirts -n kubevirt kubevirt --type=json -p=\
'[{"op": "add", "path": "/spec/configuration/network",   "value": {
    "binding": {
        "managedtap": {
            "domainAttachmentType": "managedTap"
        }
    }
}}]'
```

## 创建虚拟机，指定使用 `managedTap` 类型网络

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: dual-stack-vm
  namespace: default
spec:
  running: false
  template:
    spec:
      domain:
        devices:
          interfaces:
            - name: default
              binding:
                name: managedtap
      networks:
      - name: default
        pod: {}
```

通过以上步骤，就可以实现 VM 通过 DHCP 和 IPv6 RA 协议来获取对应的 IPv4/IPv6 地址。
