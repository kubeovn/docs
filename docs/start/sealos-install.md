# 使用 sealos 一键部署 Kubernetes 和 Kube-OVN

[sealos](https://github.com/labring/sealos) 作为 Kubernetes 的一个发行版，通过极简的使用方式和国内的镜像仓库，可以帮助用户快速从零初始化一个容器集群。
通过使用 sealos 用户可以通过一条命令在几分钟内部署出一个安装好 Kube-OVN 的 Kubernetes 集群。

## 下载安装 sealos

=== ":octicons-file-code-16: AMD64"

    ```bash
    wget  https://github.com/labring/sealos/releases/download/v4.1.4/sealos_4.1.4_linux_amd64.tar.gz  && \
    tar -zxvf sealos_4.1.4_linux_amd64.tar.gz sealos &&  chmod +x sealos && mv sealos /usr/bin
    ```

=== ":octicons-file-code-16: ARM64"

    ```bash
    wget  https://github.com/labring/sealos/releases/download/v4.1.4/sealos_4.1.4_linux_arm64.tar.gz  && \
    tar -zxvf sealos_4.1.4_linux_arm64.tar.gz sealos &&  chmod +x sealos && mv sealos /usr/bin
    ```

## 部署 Kubernetes 和 Kube-OVN

    ```bash
    sealos run labring/kubernetes:v1.24.3 labring/kube-ovn:v1.10.5 \
      --masters [masters ips seperated by comma] \
      --nodes [nodes ips seperated by comma] -p [your-ssh-passwd]
    ```

## 等待部署完成

    ```bash
    [Step 6/6] Finish
    
                        ,,,,
                        ,::,
                       ,,::,,,,
                ,,,,,::::::::::::,,,,,
             ,,,::::::::::::::::::::::,,,
           ,,::::::::::::::::::::::::::::,,
         ,,::::::::::::::::::::::::::::::::,,
        ,::::::::::::::::::::::::::::::::::::,
       ,:::::::::::::,,   ,,:::::,,,::::::::::,
     ,,:::::::::::::,       ,::,     ,:::::::::,
     ,:::::::::::::,   :x,  ,::  :,   ,:::::::::,
    ,:::::::::::::::,  ,,,  ,::, ,,  ,::::::::::,
    ,:::::::::::::::::,,,,,,:::::,,,,::::::::::::,    ,:,   ,:,            ,xx,                            ,:::::,   ,:,     ,:: :::,    ,x
    ,::::::::::::::::::::::::::::::::::::::::::::,    :x: ,:xx:        ,   :xx,                          :xxxxxxxxx, :xx,   ,xx:,xxxx,   :x
    ,::::::::::::::::::::::::::::::::::::::::::::,    :xxxxx:,  ,xx,  :x:  :xxx:x::,  ::xxxx:           :xx:,  ,:xxx  :xx, ,xx: ,xxxxx:, :x
    ,::::::::::::::::::::::::::::::::::::::::::::,    :xxxxx,   :xx,  :x:  :xxx,,:xx,:xx:,:xx, ,,,,,,,,,xxx,    ,xx:   :xx:xx:  ,xxx,:xx::x
    ,::::::,,::::::::,,::::::::,,:::::::,,,::::::,    :x:,xxx:  ,xx,  :xx  :xx:  ,xx,xxxxxx:, ,xxxxxxx:,xxx:,  ,xxx,    :xxx:   ,xxx, :xxxx
    ,::::,    ,::::,   ,:::::,   ,,::::,    ,::::,    :x:  ,:xx,,:xx::xxxx,,xxx::xx: :xx::::x: ,,,,,,   ,xxxxxxxxx,     ,xx:    ,xxx,  :xxx
    ,::::,    ,::::,    ,::::,    ,::::,    ,::::,    ,:,    ,:,  ,,::,,:,  ,::::,,   ,:::::,            ,,:::::,        ,,      :x:    ,::
    ,::::,    ,::::,    ,::::,    ,::::,    ,::::,
     ,,,,,    ,::::,    ,::::,    ,::::,    ,:::,             ,,,,,,,,,,,,,
              ,::::,    ,::::,    ,::::,    ,:::,        ,,,:::::::::::::::,
              ,::::,    ,::::,    ,::::,    ,::::,  ,,,,:::::::::,,,,,,,:::,
              ,::::,    ,::::,    ,::::,     ,::::::::::::,,,,,
               ,,,,     ,::::,     ,,,,       ,,,::::,,,,
                        ,::::,
                        ,,::,
    
    Thanks for choosing Kube-OVN!
    For more advanced features, please read https://github.com/kubeovn/kube-ovn#documents
    If you have any question, please file an issue https://github.com/kubeovn/kube-ovn/issues/new/choose
    2022-08-10T16:31:34 info succeeded in creating a new cluster, enjoy it!
    2022-08-10T16:31:34 info
          ___           ___           ___           ___       ___           ___
         /\  \         /\  \         /\  \         /\__\     /\  \         /\  \
        /::\  \       /::\  \       /::\  \       /:/  /    /::\  \       /::\  \
       /:/\ \  \     /:/\:\  \     /:/\:\  \     /:/  /    /:/\:\  \     /:/\ \  \
      _\:\~\ \  \   /::\~\:\  \   /::\~\:\  \   /:/  /    /:/  \:\  \   _\:\~\ \  \
     /\ \:\ \ \__\ /:/\:\ \:\__\ /:/\:\ \:\__\ /:/__/    /:/__/ \:\__\ /\ \:\ \ \__\
     \:\ \:\ \/__/ \:\~\:\ \/__/ \/__\:\/:/  / \:\  \    \:\  \ /:/  / \:\ \:\ \/__/
      \:\ \:\__\    \:\ \:\__\        \::/  /   \:\  \    \:\  /:/  /   \:\ \:\__\
       \:\/:/  /     \:\ \/__/        /:/  /     \:\  \    \:\/:/  /     \:\/:/  /
        \::/  /       \:\__\         /:/  /       \:\__\    \::/  /       \::/  /
         \/__/         \/__/         \/__/         \/__/     \/__/         \/__/
    
                      Website :https://www.sealos.io/
                      Address :github.com/labring/sealos
    ```
