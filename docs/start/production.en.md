# Production Ready?

Is Kube-OVN production ready? If you're asking this question, it means you are not yet production ready. Some people can effortlessly run pre-v0.0.1 versions in critical production environments with thousands of nodes and feel no pressure, while others struggle just deploying the latest version in their development environment. Being production ready is more about the user's preparedness than a standard of the software itself. Don't blindly trust marketing jargon or others' success stories—they won't be there to solve the problems in your production environment. You must be prepared to face it all yourself. This document will introduce what we consider essential preparations before going into production, helping you use Kube-OVN in production with greater confidence and ease.

## Download Complete Artifacts

Open-source software may suddenly stop releasing versions, restrict usage, delete code repositories, remove images, or delete documentation:

- [Linkerd stops releasing stable versions](https://linkerd.io/2024/02/21/announcing-linkerd-2.15/index.html#a-new-model-for-stable-releases){: target = "_blank" }
- [Elasticsearch stops releasing open-source images](https://github.com/elastic/elasticsearch/issues/70840){: target = "_blank" }
- [EMQX restricts community users to single-node deployments in production](https://www.emqx.com/en/news/emqx-adopts-business-source-license){: target = "_blank" }
- [KubeSphere stops open-source downloads](https://github.com/kubesphere/kubesphere/issues/6550){: target = "_blank" }

You need a complete offline copy of the code, images, and documentation, and you must ensure you can rebuild the images in your own environment. Use the [backup script](https://github.com/kubeovn/kube-ovn/blob/master/hack/backup.sh){: target = "_blank" } to download the code, images, and documentation for the corresponding version. Refer to the [Development and Contribution Guide](../reference/dev-env.md) to learn how to build images from the code.

## Learn OpenVswitch/OVN

Kube-OVN's underlying data plane is largely implemented by OpenVswitch and OVN. Understanding the underlying principles will give you more confidence in handling complex issues.

- [OVN Reference Documentation](https://docs.ovn.org/en/latest/ref/index.html){: target = "_blank" }
- [OpenVswitch Reference Documentation](https://www.openvswitch.org/support/dist-docs/){: target = "_blank" }

We highly recommend reading the ovn-architecture document. For other documents, a general understanding of the framework is sufficient; you can delve into details as needed during actual use.

## Study Kube-OVN Documentation

We recommend thoroughly reading all documents under the [Technical Reference](../reference/architecture.en.md) and [Operations Guide](../ops/kubectl-ko.en.md) sections. The Technical Reference section helps you build an understanding of Kube-OVN's overall architecture and technical choices, while the Operations Guide includes complex operations and tools we believe you may use daily.

Practice the operations in the Operations Guide in a development or testing environment beforehand, including disaster recovery, node switching, address changes, and other complex tasks. Regular practice will boost your confidence in using Kube-OVN in production and deepen your familiarity with its principles. The kubectl plugin includes many Bash commands to simplify daily operations, but we strongly recommend understanding the specific execution process behind each command. This will help you gain a deeper understanding of Kube-OVN's overall architecture.

## Understand Specific Features

Kube-OVN includes a wide range of features and is rapidly evolving. For the features you use, we recommend not only understanding how to use them but also their limitations and underlying principles. We are continuously improving the related content in each feature's documentation.

We also suggest building a test suite for the features you use, so you can quickly validate the impact of new Kube-OVN releases. If your use case is not covered in Kube-OVN's end-to-end (E2E) test code, we welcome contributions to the test suite to help the project grow better.

## Provide Effective Feedback

Kube-OVN community maintainers cannot respond to issues 24/7 in real-time. We prefer asynchronous communication via GitHub Issues. To improve efficiency, please provide as much detail as possible about the environment where the issue occurred, reproduction steps, and your analysis. This helps us understand the problem better and avoid multiple rounds of back-and-forth.

We have an AI bot in GitHub Issues that performs preliminary analysis of problems. You can also use your preferred AI tool to ask questions about the code repository—sometimes, you may get unexpectedly helpful results.
