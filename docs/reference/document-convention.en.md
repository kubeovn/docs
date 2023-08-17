# document specification

In order to ensure a consistent document style, please follow the following style guidelines when submitting documents.

## Punctuation

All punctuation in the text content in Chinese documents should use Chinese format punctuation, and all text content in English documents should use English punctuation.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

Here is a one-click installation script that can help you quickly install a highly available, production-ready container network.

</td><td>

Here is a one-click installation script that can help you quickly install a highly available, production-ready container network.

</td></tr>
</tbody></table>

English numbers and Chinese characters should be separated by spaces.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

Kube-OVN provides a one-click installation script to install version 1.10 of Kube-OVN.

</td><td>

Kube-OVN provides a one-click installation script to install version 1.10 of Kube-OVN.

</td></tr>
</tbody></table>

Example content should start with `:`, other sentences should end with `. ` End.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

Please confirm that the environment configuration is correct before installation

Download the installation script using the command below.

```bash
wget 127.0.0.1
```

</td><td>

Please confirm that the environment configuration is correct before installation.

Download the installation script using the following command:

```bash
wget 127.0.0.1
```

</td></tr>
</tbody></table>

## code block

yaml code blocks need to be identified as yaml.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

`````markdown
````
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
     name: attach-subnet
````
`````

</td><td>

`````markdown
````yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
     name: attach-subnet
````
`````

</td></tr>
</tbody></table>

Command-line manipulation example code blocks need to be identified as bash.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

`````markdown
````
wget 127.0.0.1
````
`````

</td><td>

`````markdown
````bash
wget 127.0.0.1
````
`````

</td></tr>
</tbody></table>

If the command line operation example contains output content, the executed command needs to start with `#` to distinguish input from output.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```bash
oilbeater@macdeMac-3 ~ ping 114.114.114.114 -c 3
PING 114.114.114.114 (114.114.114.114): 56 data bytes
64 bytes from 114.114.114.114: icmp_seq=0 ttl=83 time=10.429 ms
64 bytes from 114.114.114.114: icmp_seq=1 ttl=79 time=11.360 ms
64 bytes from 114.114.114.114: icmp_seq=2 ttl=76 time=10.794 ms

--- 114.114.114.114 ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 10.429/10.861/11.360/0.383 ms
```

</td><td>

```bash
# ping 114.114.114.114 -c 3
PING 114.114.114.114 (114.114.114.114): 56 data bytes
64 bytes from 114.114.114.114: icmp_seq=0 ttl=83 time=10.429 ms
64 bytes from 114.114.114.114: icmp_seq=1 ttl=79 time=11.360 ms
64 bytes from 114.114.114.114: icmp_seq=2 ttl=76 time=10.794 ms

--- 114.114.114.114 ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 10.429/10.861/11.360/0.383 ms
```

</td></tr>
</tbody></table>

If the command line operation example only contains execution commands and no output results, multiple commands do not need to start with `#`.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```bash
# mv /etc/origin/ovn/ovnnb_db.db /tmp
# mv /etc/origin/ovn/ovnsb_db.db /tmp
```

</td><td>

```bash
mv /etc/origin/ovn/ovnnb_db.db /tmp
mv /etc/origin/ovn/ovnsb_db.db /tmp
```

</td></tr>
</tbody></table>

## Link

Links in the site use the corresponding `md` file path.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```markdown
Please refer to [Preparation](http://kubeovn.github.io/prepare) before installation.
```

</td><td>

```markdown
Please refer to [Preparation](./prepare.md) before installation.
```

</td></tr>
</tbody></table>

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```markdown
If you have any questions, please refer to [Kubernetes Documentation](http://kubernetes.io).
```

</td><td>

```markdown
If you have any questions, please refer to [Kubernetes Documentation](http://kubernetes.io){: target="_blank" }.
```

</td></tr>
</tbody></table>

## Empty line

Different logical blocks, such as title and text, text and code, text and number need to be separated by blank lines.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

````markdown
Download the script below to install it:
```bash
wget 127.0.0.1
```
````

</td><td>

````markdown
Download the script below to install it:

```bash
wget 127.0.0.1
```
````

</td></tr>
</tbody></table>

Separate logical blocks with only *one* blank line.

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

````markdown
Download the script below to install it:



```bash
wget 127.0.0.1
```
````

</td><td>

````markdown
Download the script below to install it:

```bash
wget 127.0.0.1
```
````

</td></tr>
</tbody></table>
