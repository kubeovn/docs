# 文档规范

为了保证文档风格一致，请在提交文档时遵循下列的风格规范。

## 标点

中文文档中文本内容所有标点应使用中文格式标点，英文文档中所有文本内容中应使用英文标点。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

这里提供了一键安装脚本,可以帮助你快速安装一个高可用,生产就绪的容器网络.

</td><td>

这里提供了一键安装脚本，可以帮助你快速安装一个高可用，生产就绪的容器网络。

</td></tr>
</tbody></table>

英文数字和中文应该用空格进行分隔。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

Kube-OVN提供了一键安装脚本来安装1.10版本Kube-OVN。

</td><td>

Kube-OVN 提供了一键安装脚本来安装 1.10 版本 Kube-OVN。

</td></tr>
</tbody></table>

示例内容应该以 `：` 开启，其他句尾需要用 `。` 结束。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

安装前请确认环境配置正确

使用下面的命令下载安装脚本。

```bash
wget 127.0.0.1
```

</td><td>

安装前请确认环境配置正确。

使用下面的命令下载安装脚本：

```bash
wget 127.0.0.1
```

</td></tr>
</tbody></table>

## 代码块

yaml 代码块需要标识为 yaml。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

`````
````
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
    name: attach-subnet
````
`````

</td><td>

`````
````yaml
apiVersion: kubeovn.io/v1
kind: Subnet
metadata:
    name: attach-subnet
````
`````

</td></tr>
</tbody></table>

命令行操作示例代码块需要标识为 bash。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

`````
````
wget 127.0.0.1
````
`````

</td><td>

`````
````bash
wget 127.0.0.1
````
`````

</td></tr>
</tbody></table>

如果命令行操作示例中包含输出内容，则所执行命令需要以 `#` 开始，以区分输入与输出。

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

如果命令行操作示例中只包含执行命令，没有输出结果，则多条命令无需 `#` 开始。

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

## 链接

站内链接使用对应 `md` 文件路径。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```
安装前请参考[准备工作](http://kubeovn.github.io/prepare)。
```

</td><td>

```
安装前请参考[准备工作](./prepare.md)。
```

</td></tr>
</tbody></table>

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```
如有问题请参考 [Kubernetes 文档](http://kubernetes.io)。
```

</td><td>

```
如有问题请参考 [Kubernetes 文档](http://kubernetes.io){: target="_blank" }。
```

</td></tr>
</tbody></table>

## 空行

不同逻辑块，例如标题和文本，文本和代码，文本和编号之间需要用空行分隔。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

````
下载下面的脚本，进行安装：
```bash
wget 127.0.0.1
```
````

</td><td>

````
下载下面的脚本，进行安装：

```bash
wget 127.0.0.1
```
````

</td></tr>
</tbody></table>

不同逻辑块之间只使用*一个*空行进行分隔。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

````
下载下面的脚本，进行安装：



```bash
wget 127.0.0.1
```
````

</td><td>

````
下载下面的脚本，进行安装：

```bash
wget 127.0.0.1
```
````

</td></tr>
</tbody></table>
