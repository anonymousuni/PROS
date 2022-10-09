# SKS


This tutorial provides information regarding the SKS service of a cloud provider:

https://community.exoscale.com/documentation/sks/quick-start/

https://www.youtube.com/watch?v=P_uR4dSorLM



The first steps:

PS C:\Users\anon> C:\exoscale\exo.exe compute sks kubeconfig zsla kubernetes-admin -t 600000 --group system:masters > ~/.kube/config

PS C:\Users\anon> .\kubectl.exe --kubeconfig .\.kube\config get pods -o wide

