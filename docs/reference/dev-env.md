# 开发和贡献指导

## 贡献流程

Kube-OVN 并没有复杂的贡献流程，一切工作都可以在 Github 上发生。当你想提交新的功能/修复某个问题，只需要在 Github 上创建 Issue 和 PR，经过 Maintainer 的 Review 且所有 Github Action 通过，代码就可以被合并。

## 环境准备

Kube-OVN 使用 [Go](https://golang.org/){: target="_blank" } 开发并使用 [Go Modules](https://github.com/golang/go/wiki/Modules){: target="_blank" } 管理依赖，
请确认环境变量 `GO111MODULE="on"`。

[golangci-lint](https://golangci-lint.run){: target="_blank" } 被用来扫描代码规范性问题，需要在开发环境安装，请参考[local-installation](https://golangci-lint.run/welcome/install/#local-installation){: target="_blank" }。

为了降低最终生成镜像大小，Kube-OVN 使用了部分 Docker buildx 试验特性，请更新 Docker 至最新版本
并开启 buildx:

```bash
docker buildx create --use
```

## 构建镜像

使用下面的命令下载代码，并生成运行 Kube-OVN 所需镜像：

```bash
git clone https://github.com/kubeovn/kube-ovn.git
cd kube-ovn
make release
```

如需构建在 ARM 环境下运行的镜像，请执行下面的命令：

```bash
make release-arm
```

## 构建 base 镜像

如需要更改操作系统版本，依赖库，OVS/OVN 代码等，需要对 base 镜像进行重新构建。

base 镜像使用的 Dockerfile 为 `dist/images/Dockerfile.base`。

构建方法：

```bash
# build x86 base image
make base-amd64

# build arm base image
make base-arm64
```

## 运行 E2E

Kube-OVN 使用:

- [KIND](https://kind.sigs.k8s.io/) 来构建本地 Kubernetes 集群：` go install sigs.k8s.io/kind@latest `
- [jinjanator](https://github.com/kpfleming/jinjanator) 来渲染模板: ` pip install jinjanator `
- [Ginkgo](https://onsi.github.io/ginkgo/) 来运行测试代码：` go install github.com/onsi/ginkgo/v2/ginkgo; go get github.com/onsi/gomega/... `

> 详情请参考相关文档进行依赖安装。

本地执行 E2E 测试：

```bash
make kind-init
make kind-install
make e2e
```

如需运行 Underlay E2E 测试，执行下列命令：

```bash
make kind-init
make kind-install-underlay
make e2e-underlay-single-nic
```

如需运行 ovn vpc nat gw eip, fip, snat, dnat 测试，执行下列命令：

```bash
make kind-init
make kind-install
make ovn-vpc-nat-gw-conformance-e2e
```

如需运行 iptables vpc nat gw eip, fip, snat, dnat 测试，执行下列命令：

```bash
make kind-init
make kind-install-vpc-nat-gw
make iptables-vpc-nat-gw-conformance-e2e
```

如需运行 loadbalancer service 测试，执行下列命令：

```bash
make kind-init
make kind-install-lb-svc
make kube-ovn-lb-svc-conformance-e2e
```

如需清理，执行下列命令：

```bash
make kind-clean
```
