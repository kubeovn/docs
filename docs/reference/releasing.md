# 版本管理

Kube-OVN 目前主要发布 Minor 版本和 Patch 版本。Minor 版本中会有新功能的增加，OVN/OVS 大版本升级，内部架构调整，API 变化。Patch 版本主要进行 Bug 修复，安全漏洞修复，依赖升级，同时兼容之前的 API。

## 维护策略

Kube-OVN 目前会持续维护主干分支和最近两个发版分支，例如 `master`, `release-1.12`，`release-1.11`。其中最新发版分支（例如 `release-1.12`）会进行较为频繁的迭代和发版，所有 Bug 修复，安全漏洞和依赖升级都会尽可能 backport 到最新发版分支。

前一个发版分支（例如 `release-1.11`）会 backport 较为重大的 Bug 修复以及影响面较大的安全漏洞修复。

## 发版周期

Minor 版以主干分支是否有重大新功或重大的架构调整完成为契机按需发版，目前约为半年一次发布。Patch 版本根据分支 Bug 修复情况触发，一般会在 Bug 修复进入后一周内发布。

## Patch 版本发布方式

目前 Patch 版本大部分工作都可以通过 [hack/release.sh](https://github.com/kubeovn/kube-ovn/blob/release-1.12/hack/release.sh) 脚本以自动化的方式来实现，主要发布步骤描述如下：

1. 检查当前分支 Build 情况（自动化）
2. 推送新 tag 镜像到 Docker Hub（自动化）
3. 推送新 tag 代码到 Github（自动化）
4. 修改代码中的版本信息（自动化）
5. 修改文档仓库版本信息（自动化）
6. 生成 Release Note PR（自动化）
7. 合并 Release Note (手动)
   1. 手动 Merge github action 生成的 Release Note PR
8. 修改 Github Release 信息（手动）
   1. 在 Github Release 页面编辑新生成的 Release，将标题修改为对应版本号（例如 `v1.12.12`），并复制上一步生成的 Release Note 到 Release 详情

## Minor 版本发布方式

目前 Minor 分支主要工作还需要通过手动的方式来完成，主要发布步骤描述如下：

1. 在 Github 上推送一个新的发布分支，例如 `release-1.13` (手动)
2. 将主干分支的 `VERSION`, `dist/images/install.sh`, `charts/kube-ovn/values.yaml` 和 `charts/kube-ovn/Chart.yaml` 中的版本信息修改为下个 Minor 版本，例如 `v1.14.0` (手动)
3. 推送新 tag 镜像到 Docker Hub (手动)
4. 在发版分支推送新 tag 代码到 Github (手动)
5. 在文档仓库新建发版分支，例如 `v1.13`，修改 `mkdocs.yml` 文件中的 `version` 和 `branch` 信息 (手动)
6. 生成 Release Note PR（自动化）
7. 合并 Release Note (手动)
   1. 手动 Merge github action 生成的 Release Note PR
8. 修改 Github Release 信息（手动）
   1. 在 Github Release 页面编辑新生成的 Release，将标题修改为对应版本号（例如 `v1.13.0`），并复制上一步生成的 Release Note 到 Release 详情
9. 修改发版分支的 `VERSION` 文件版本信息为下一个 Patch 版本，例如 `v1.13.1`
