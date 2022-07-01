# Development Setup

## Environmental Preparation

Kube-OVN uses [Golang](https://golang.org/){: target="_blank" } 1.17 to develop and [Go Modules](https://github.com/golang/go/wiki/Modules){: target="_blank" } 
to manage dependency, please check env `GO111MODULE="on"`。

[gosec](https://github.com/securego/gosec){: target="_blank" } is used to scan for code security related issues 
and requires to be installed in the development environment:

```bash
go get github.com/securego/gosec/v2/cmd/gosec
```

To reduce the size of the final generated image, Kube-OVN uses some of the Docker buildx experimental features, 
please update Docker to the latest version and enable buildx:

```bash
docker buildx create --use
```

## Build Image

Use the following command to download the code and generate the image required to run Kube-OVN:

```bash
git clone https://github.com/kubeovn/kube-ovn.git
cd kube-ovn
make release
```

To build an image to run in an ARM environment, run the following command:

```bash
make release-arm
```

## Run E2E

Kube-OVN uses [KIND](https://kind.sigs.k8s.io/){: target="_blank" } to build local Kubernetes cluster, [j2cli](https://github.com/kolypto/j2cli){: target="_blank" } to render templates，
and [Ginkgo](https://onsi.github.io/ginkgo/){: target="_blank" } to run test cases. Please refer to the relevant documentation for dependency installation.

Run E2E locally:

```bash
make kind-init
make kind-install
make e2e
```

To run the Underlay E2E test, run the following commands:

```bash
make kind-init
make kind-install-underlay
make e2e-underlay-single-nic
```
