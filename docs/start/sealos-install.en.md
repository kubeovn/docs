# One-Click Deployment of Kubernetes and Kube-OVN with sealos

[sealos](https://github.com/labring/sealos), a distribution of Kubernetes, helps users quickly initialize a container cluster from scratch.
By using sealos, users can deploy a Kubernetes cluster with Kube-OVN installed in minutes with a single command.

## Download sealos

=== ":octicons-file-code-16: AMD64"

    ```bash
    wget https://github.com/labring/sealos/releases/download/v4.0.0/sealos_4.0.0_linux_amd64.tar.gz \
      && tar zxvf sealos_4.0.0_linux_amd64.tar.gz sealos && chmod +x sealos && mv sealos /usr/bin
    ```

=== ":octicons-file-code-16: ARM64"

    ```bash
    wget https://github.com/labring/sealos/releases/download/v4.0.0/sealos_4.0.0_linux_arm64.tar.gz \
      && tar zxvf sealos_4.0.0_linux_arm64.tar.gz sealos && chmod +x sealos && mv sealos /usr/bin
    ```

## Deploy Kubernetes and Kube-OVN

    ```bash
    sealos run labring/kubernetes:v1.24.3 labring/kube-ovn:v1.10.5 \
      --masters [masters ips seperated by comma] \
      --nodes [nodes ips seperated by comma] -p [your-ssh-passwd]
    ```

## Wait to finish

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
