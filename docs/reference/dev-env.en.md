# Development and Contribution Guide

## Contribution Process  

Kube-OVN does not have a complex contribution process—all work happens on GitHub. If you want to submit a new feature or fix a bug, simply create an Issue and Pull Request (PR) on GitHub. After maintainers review and all GitHub Actions pass, the code will be merged.  

## Environmental Preparation

Kube-OVN uses [Golang](https://golang.org/){: target="_blank" } to develop and [Go Modules](https://github.com/golang/go/wiki/Modules){: target="_blank" }
to manage dependency, please check env `GO111MODULE="on"`.

[golangci-lint](https://golangci-lint.run){: target="_blank" } is used to scan code for compliance issues. It needs to be installed in the development environment. Please refer to [local-installation](https://golangci-lint.run/welcome/install/#local-installation){: target="_blank" }.

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

## Building the Base Image

If you need to change the operating system version, dependencies, OVS/OVN code, etc., you need to rebuild the base image.

The Dockerfile used for the base image is `dist/images/Dockerfile.base`.

Build instructions:

```bash
# build x86 base image
make base-amd64

# build arm base image
make base-arm64
```

## Run E2E

Kube-OVN uses:

- [KIND](https://kind.sigs.k8s.io/) to build local Kubernetes cluster: `go install sigs.k8s.io/kind@latest`
- [jinjanator](https://github.com/kpfleming/jinjanator) to render templates: `pip install jinjanator`
- [Ginkgo](https://onsi.github.io/ginkgo/) to run test cases: `go install github.com/onsi/ginkgo/v2/ginkgo; go get github.com/onsi/gomega/...`

> Please refer to the relevant documentation for dependency installation.

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

To run the ovn vpc nat gw eip, fip, snat, dnat E2E test, run the following commands:

```bash
make kind-init
make kind-install
make ovn-vpc-nat-gw-conformance-e2e
```

To run the iptables vpc nat gw eip, fip, snat, dnat E2E test, run the following commands:

```bash
make kind-init
make kind-install
make iptables-vpc-nat-gw-conformance-e2e
```

To run the loadbalancer service E2E test, run the following commands:

```bash
make kind-init
make kind-install
make kube-ovn-lb-svc-conformance-e2e
```

To clean, run the following commands:

```bash
make kind-clean
```
