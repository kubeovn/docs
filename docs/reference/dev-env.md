# 开发环境构建

## 环境准备

Kube-OVN 使用 [Go](https://golang.org/){: target="_blank" } 1.18 开发并使用 [Go Modules](https://github.com/golang/go/wiki/Modules){: target="_blank" } 管理依赖，
请确认环境变量 `GO111MODULE="on"`。

[gosec](https://github.com/securego/gosec){: target="_blank" } 被用来扫描代码安全相关问题，需要在开发环境安装：

```bash
go get github.com/securego/gosec/v2/cmd/gosec
```

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

Kube-OVN 使用 [KIND](https://kind.sigs.k8s.io/){: target="_blank" } 构建本地 Kubernetes 集群，[j2cli](https://github.com/kolypto/j2cli){: target="_blank" } 渲染模板，
[Ginkgo](https://onsi.github.io/ginkgo/){: target="_blank" } 来运行测试代码。请参考相关文档进行依赖安装。

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
