# 生产就绪？

Kube-OVN 是否生产就绪？如果你问出这个问题，那就说明你尚未生产就绪。有的人可以轻松将 pre-v0.0.1 版本运行到上千节点的关键业务生产环境还觉得没什么压力，有的人只是在自己的开发环境部署最新版本就已经焦头烂额。生产就绪更多的是对使用者的要求而不是软件本身的标准。不要轻信各种市场营销术语，也不要相信别人的案例，他们都不会来解决你生产环境中的问题，你自己要准备好面对这一切。这篇文档将会介绍我们认为在上生产环境前的一些必要准备工作，帮助你在生产环境中更有信心且自如地使用 Kube-OVN。

## 下载完整制品

开源软件可能会突然停止版本发布、限制使用方式、删除代码仓库、删除镜像或删除文档：

- [Linkerd 停止发行稳定版本](https://linkerd.io/2024/02/21/announcing-linkerd-2.15/index.html#a-new-model-for-stable-releases){: target="_blank" }
- [Elasticsearch 停止开源镜像发布](https://github.com/elastic/elasticsearch/issues/70840){: target = "_blank" }
- [EMQX 社区用户生产环境仅允单节点部署](https://www.emqx.com/en/news/emqx-adopts-business-source-license){: target = "_blank" }
- [KubeSphere 停止开源下载](https://github.com/kubesphere/kubesphere/issues/6550){: target = "_blank" }

你需要一份离线完整的代码，镜像和文档，并保证你能够在自己环境里重新构建完整的镜像。请使用[备份脚本](https://github.com/kubeovn/kube-ovn/blob/master/hack/backup.sh){: target = "_blank" }下载对应版本的代码、镜像和文档。并参考[开发和贡献指导](../reference/dev-env.md)学习如何从代码构建镜像。

## OpenVswitch/OVN 学习

Kube-OVN 底层的数据平面大部分由 OpenVswitch 和 OVN 实现，了解底层原理会让你对复杂问题更有信心。

- [OVN 参考文档](https://docs.ovn.org/en/latest/ref/index.html){: target = "_blank" }
- [OpenVswitch 参考文档](https://www.openvswitch.org/support/dist-docs/){: target = "_blank" }

其中我们推荐 ovn-architecture 文档必读，其他文档只需了解大概框架，可在实际使用中再去了解细节内容。

## Kube-OVN 文档学习

我们建议详细阅读[技术参考](../reference/architecture.md)和[运维指南](../ops/kubectl-ko.md)部分下的全部文档。技术参考部分可以帮助你建立对 Kube-OVN 整体架构，技术选型的一些概念，运维指南里包含了我们认为日常可能会使用到的复杂操作和一系列工具的使用。

其中运维指南里的操作可在开发测试环境提前进行演练，包括灾备，节点切换，地址变更等复杂操作，平日的操作可以增强你在生产环境使用的信心，也更加熟悉和了解 Kube-OVN 的原理。其中 kubectl 插件使用 bash 编写了大量简化日常操作的命令，但我们强烈推荐了解每个命令背后的具体执行过程，这可以帮助你对 Kube-OVN 的整体架构有更深刻的理解。

## 了解具体功能

Kube-OVN 中包含了大量功能，并且还在快速迭代。针对你使用的功能我们建议你在了解如何使用时还要了解其局限性和背后的原理，我们也会在每个功能的文档中不断完善相关内容。

同时我们建议你构建一个自己所使用到功能的测试集合，在 Kube-OVN 新版本发布后可以快速验证新版本对自己的影响。如果你的功能使用场景目前没有包含在 Kube-OVN 的 E2E 测试代码中，我们欢迎你能贡献相关的测试，帮助项目更好的成长。

## 正确反馈问题

Kube-OVN 社区的维护者无法 7*24 小时实时响应问题，我们更倾向于使用 Github Issue 的方式进行异步沟通。为了提升效率，请尽可能详细的提供问题出现的环境、复现步骤以及你的分析，这可以帮助我们更好的了解问题，避免多轮对话迭代。

我们在 Github Issue 中提供了 AI 机器人会对问题进行初步的分析，你也可以使用自己熟悉的 AI 工具对代码仓库提问，有时可能会得到超出预期的结果。
