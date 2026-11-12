# Kubernetes — Comandos

Referência dos comandos usados nos labs de Kubernetes (minikube no WSL) e da referência de AKS. Os manifestos citados estão em [manifests/](./manifests/).

## Instalação (minikube e kubectl)

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

- `curl -LO`: baixa o arquivo seguindo redirecionamentos (`-L`) e salvando com o nome original (`-O`).
- `$(curl -L -s .../stable.txt)`: consulta, em modo silencioso (`-s`), a versão estável atual do kubectl.
- `install -o root -g root -m 0755`: copia o binário definindo dono (`-o`), grupo (`-g`) e permissão de execução (`-m 0755`).

## Cluster

| Comando | O que faz |
|---|---|
| `minikube start --force` | Sobe (ou religa) o cluster; `--force` é necessário quando logado como root |
| `minikube status` | Estado dos componentes do cluster |
| `minikube ssh` | Abre um shell dentro do node do minikube |
| `minikube delete` | Apaga o cluster inteiro (inclusive certificados instalados manualmente) |
| `minikube ip` | IP do container do minikube |
| `kubectl get nodes` | Lista os nodes e o status (Ready/NotReady) |
| `kubectl get pods -n kube-system -o wide` | Pods do próprio Kubernetes (`-n` = namespace; `-o wide` = mostra node e IP) |
| `kubectl get namespaces` | Lista os namespaces do cluster |

## Contexto do kubectl

| Comando | O que faz |
|---|---|
| `kubectl config current-context` | Qual cluster o kubectl está usando agora |
| `kubectl cluster-info` | Endereço do kube-apiserver em uso |
| `minikube update-context` | Corrige o endereço do apiserver no kubeconfig (a porta muda a cada start) |

## Pods e Deployments

| Comando | O que faz |
|---|---|
| `kubectl run pod-teste --image=nginx` | Cria um Pod avulso, sem auto-recuperação (só para teste) |
| `kubectl describe pod pod-teste` | Detalhes do Pod, incluindo a seção **Events** |
| `kubectl delete pod pod-teste` | Remove o Pod |
| `kubectl create deployment loja-frontend --image=nginx --replicas=3` | Cria um Deployment com 3 réplicas (forma correta, com auto-recuperação) |
| `kubectl scale deployment loja-frontend --replicas=5` | Define o número **final** de réplicas |
| `kubectl get deployment loja-frontend -o wide` | Estado do Deployment |
| `kubectl get pods --show-labels` | Lista os Pods com suas labels |

## Service e DNS interno

| Comando | O que faz |
|---|---|
| `kubectl expose deployment loja-frontend --port=80 --type=ClusterIP --name=svc-loja-frontend` | Cria um Service com IP interno fixo para o Deployment |
| `kubectl get service svc-loja-frontend -o wide` | Mostra o Service e o selector |
| `kubectl describe service svc-loja-frontend` | Detalhes do Service |
| `kubectl get endpoints svc-loja-frontend` | IPs dos Pods que o Service está atendendo |
| `kubectl port-forward service/svc-loja-frontend 8080:80` | Túnel de teste da porta local 8080 para o Service (não usar em produção) |

Testar o DNS interno (Pod falando com Pod pelo nome do Service):

```bash
kubectl run teste --rm -it --image=busybox --restart=Never -- wget -qO- svc-loja-frontend
```

- `--rm`: apaga o Pod ao terminar; `-it`: modo interativo com terminal.
- `--restart=Never`: cria um Pod simples (não um Deployment).
- `-- wget -qO- svc-loja-frontend`: tudo depois de `--` é o comando do container; `-q` silencioso, `-O-` imprime a resposta na tela.

## Manifestos declarativos (YAML)

| Comando | O que faz |
|---|---|
| `kubectl apply -f manifests/webserver.yaml` | Cria/atualiza o que o arquivo descreve (idempotente) |
| `kubectl get all -l app=loja-frontend` | Todos os objetos com a label (`-l` = selector de label) |
| `kubectl apply -f arquivo.yaml --dry-run=client` | Valida o YAML sem aplicar |
| `kubectl create deployment teste --image=nginx --dry-run=client -o yaml` | Gera o esqueleto do YAML sem criar nada |
| `kubectl delete -f arquivo.yaml` | Remove do cluster tudo que o arquivo descreve |
| `kubectl delete deployment app1 app2` | Remove vários objetos pelo nome |
| `kubectl delete configmap/a secret/b ingress/c` | Remove tipos diferentes (formato `tipo/nome`) |
| `kubectl get deploy,svc,hpa,pods -o name` | Lista no formato `tipo/nome` |

> **Em produção:** YAML versionado no Git é o padrão (revisão, histórico, sem drift). Comandos imperativos ficam para teste e diagnóstico.

## Rolling update e rollback

| Comando | O que faz |
|---|---|
| `kubectl set image deployment/loja-frontend nginx=nginx:1.26` | Troca a imagem do container `nginx`, gradualmente e sem downtime |
| `kubectl rollout status deployment/loja-frontend` | Acompanha a troca até o fim |
| `kubectl rollout undo deployment/loja-frontend` | Volta para a versão anterior |
| `kubectl rollout history deployment/loja-frontend` | Lista as revisões |
| `kubectl rollout restart deployment vitrine` | Recria os Pods do Deployment, um a um |
| `kubectl get rs` | ReplicaSets (o atual e os antigos, mantidos para rollback) |

## Ingress

| Comando | O que faz |
|---|---|
| `minikube addons enable ingress` | Instala o ingress-nginx como Ingress Controller (só no minikube) |
| `kubectl get pods -n ingress-nginx` | Pods do controller |
| `kubectl get jobs -n ingress-nginx` | Jobs `admission-create` e `admission-patch`, que preparam o certificado do webhook |
| `kubectl logs job/ingress-nginx-admission-create -n ingress-nginx` | Logs de um Job |
| `kubectl apply -f manifests/apps-teste.yaml` | Cria app1 e app2 com seus Services (ClusterIP) |
| `kubectl apply -f manifests/ingress-teste.yaml` | Cria as regras `/app1 → svc-app1` e `/app2 → svc-app2` |
| `kubectl get ingress` | Classe, regras e ADDRESS do Ingress |
| `kubectl get svc -n ingress-nginx` | Tipo do Service do controller (NodePort no minikube) |

Acesso no laboratório (não existe em produção, onde o IP vem do load balancer da nuvem):

| Comando | O que faz |
|---|---|
| `minikube tunnel` | Faz o papel do load balancer da nuvem (o terminal fica preso) |
| `curl http://192.168.49.2/app1` | Testa a regra do Ingress pelo IP do minikube |
| `sudo ss -tlnp \| grep ':80 '` | Mostra quem escuta na porta 80 (`-t` TCP, `-l` em escuta, `-n` numérico, `-p` processo) |

> **Pegadinha:** `curl` em `localhost` pode bater num nginx instalado no próprio WSL (rodapé `nginx/1.24.0 (Ubuntu)`), e não no cluster.

## ConfigMap e Secret

| Comando | O que faz |
|---|---|
| `kubectl apply -f manifests/config-teste.yaml` | Cria o ConfigMap `config-app` e o Secret `segredo-app` |
| `kubectl get configmap config-app -o yaml` | Valores em texto puro |
| `kubectl get secret segredo-app -o yaml` | Valores em base64 |
| `kubectl get configmap config-app -o jsonpath='{.data.DB_SERVER}'; echo` | Extrai um único campo |
| `kubectl get secret segredo-app -o jsonpath='{.data.DB_PASSWORD}' \| base64 -d; echo` | Decodifica o valor do Secret (`-d` = decode) |
| `kubectl apply -f manifests/vitrine.yaml` | Deployment que recebe ConfigMap e Secret como variáveis (`envFrom`) |
| `kubectl exec deploy/vitrine -- env \| grep DB_` | Lista as variáveis recebidas pelo container |
| `kubectl apply -f manifests/vitrine-arq.yaml` | Deployment com o Secret montado como **arquivos** em `/etc/segredos` |
| `kubectl exec deploy/vitrine-arq -- ls /etc/segredos` | Cada chave do Secret vira um arquivo |
| `kubectl exec deploy/vitrine-arq -- cat /etc/segredos/DB_PASSWORD; echo` | Conteúdo do arquivo |

- Erro `NotFound`: conferir tipo, nome e namespace (ConfigMap e Secret são tipos diferentes).
- Pod em execução **não** percebe mudança no ConfigMap entregue por variável: é preciso `rollout restart` ou recriar o Pod.

Equivalentes imperativos (referência, não executados no lab):

```bash
kubectl create configmap ajustes-loja --from-literal=DB_SERVER=banco-prod --from-literal=DB_USER=app_loja
kubectl create secret generic credenciais-loja --from-literal=DB_PASSWORD=<senha>
kubectl create deployment vitrine-cmd --image=busybox:1.36 -- sleep 3600
kubectl set env deployment/vitrine-cmd --from=configmap/config-app   # liga o ConfigMap ao Deployment
```

## Probes

**Readiness:** o Pod só entra no Service quando `/tmp/pronto` existe.

| Comando | O que faz |
|---|---|
| `kubectl apply -f manifests/readiness-probe.yaml` | Cria o Deployment `demo-readiness`; o Pod nasce `0/1` porque o arquivo ainda não existe |
| `kubectl exec deploy/demo-readiness -- touch /tmp/pronto` | Cria o arquivo: a probe passa e o Pod vai para `1/1` (entra no Service) |
| `kubectl exec deploy/demo-readiness -- rm /tmp/pronto` | Remove o arquivo: o Pod volta para `0/1` e sai do Service, mas RESTARTS continua em 0 |
| `kubectl exec deploy/demo-readiness -- cat /tmp/pronto; echo $?` | Roda o mesmo teste da probe na mão; `$?` mostra o código de saída (0 = sucesso) |
| `kubectl get pods -l app=demo-readiness -w` | Acompanha a coluna READY mudando |

**Liveness:** a aplicação simula uma trava após 20 s e o kubelet reinicia o container.

| Comando | O que faz |
|---|---|
| `kubectl apply -f manifests/liveness-probe.yaml` | Cria o Deployment `demo-liveness` |
| `kubectl get pods -l app=demo-liveness -w` | RESTARTS sobe a cada ciclo de trava e reinício |
| `kubectl describe pod -l app=demo-liveness` | Events mostram `Liveness probe failed` e `Container ... will be restarted` |
| `kubectl scale deployment demo-liveness --replicas=0` | Pausa o teste sem apagar o Deployment |
| `kubectl get pod -l app=demo-readiness -o jsonpath='{.items[0].spec.containers[*].name}'; echo` | Lista os nomes dos containers do Pod |

## HPA (Horizontal Pod Autoscaler)

| Comando | O que faz |
|---|---|
| `minikube addons enable metrics-server` | Liga a coleta de CPU/memória (no AKS já vem habilitado) |
| `kubectl top pods -A` | Consumo de todos os Pods, em todos os namespaces (`-A`) |
| `kubectl top pods -l app=api-catalogo` | Consumo de cada Pod da aplicação |
| `watch -n 5 kubectl top pods -l app=api-catalogo` | Repete o comando a cada 5 segundos (`-n 5`) |
| `kubectl apply -f manifests/api-catalogo-deploy.yaml` | Deployment + Service usados no teste de carga |
| `kubectl apply -f manifests/escalador-catalogo-hpa.yaml` | HPA declarativo (com `behavior`) |
| `kubectl autoscale deployment api-catalogo --name=escalador-catalogo --cpu-percent=50 --min=2 --max=8` | Alternativa imperativa (não configura `behavior`) |
| `kubectl get hpa escalador-catalogo` | Estado: TARGETS (uso/meta) e REPLICAS |
| `kubectl get hpa escalador-catalogo --watch` | Acompanha ao vivo |
| `kubectl describe hpa escalador-catalogo` | Metrics, Conditions e Events |
| `kubectl rollout status deployment/api-catalogo` | Acompanha o rolling update |

Gerador de carga:

```bash
kubectl run gerador-carga --rm -it --image=busybox:1.36 --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://svc-catalogo; done"
```

- Um Pod temporário dispara requisições contínuas (a cada 0,01 s) contra o Service, elevando a CPU dos Pods da API.

## Volumes persistentes

| Comando | O que faz |
|---|---|
| `kubectl get storageclass` | Tipos de disco que o cluster sabe provisionar |
| `kubectl apply -f manifests/pvc-dados.yaml` | Cria o PVC `pvc-dados`; o PV é criado automaticamente |
| `kubectl get pvc` | Lista os PVCs; `STATUS Bound` = ligado a um disco |
| `kubectl get pv` | Lista os discos (PV) criados pelo cluster |
| `kubectl describe pv <nome-do-pv>` | Claim (dono), Reclaim Policy, Source |
| `kubectl describe pvc <nome-do-pvc>` | Volume ligado, Used By (Pod que usa), Events |
| `kubectl apply -f manifests/gravador-de-notas.yaml` | Pod que grava `/dados/nota.txt` no disco |
| `kubectl apply -f manifests/leitor-de-notas.yaml` | Pod novo que monta o mesmo PVC |
| `kubectl exec <pod> -- cat /dados/nota.txt` | Lê o arquivo (prova de que o dado sobreviveu ao Pod) |
| `kubectl delete pod <pod>` | Remove o Pod; PVC e PV continuam |
| `kubectl delete pvc <nome-do-pvc>` | Remove o PVC; com `reclaimPolicy: Delete`, o disco vai junto |

## Troubleshooting de Pods

| Comando | O que faz |
|---|---|
| `kubectl describe pod NOME` | Events: problemas ao redor do Pod (imagem, vaga, OOM, probe) |
| `kubectl describe pod -l app=vitrine` | Mesmo, filtrando por label |
| `kubectl get pods -l app=vitrine -w` | `-w` (*watch*) imprime cada mudança de status |
| `kubectl get pods -l app=vitrine -o wide` | Mostra node e IP de cada Pod |
| `kubectl logs NOME` | O que a aplicação escreveu |
| `kubectl logs NOME --previous` | Log da execução anterior (Pod que reiniciou) |
| `kubectl delete pod <nome-exato-do-pod>` | Remove um Pod; o Deployment cria outro |

## Certificado de inspeção TLS no minikube

Sintoma: node `NotReady` ou Pod em `ErrImagePull` / `ImagePullBackOff` com `x509: certificate signed by unknown authority`. Análise completa em [troubleshooting/tls-inspection](../troubleshooting/tls-inspection/).

```bash
kubectl get nodes
kubectl get pods -n kube-system
kubectl describe pod -n kube-system <nome-do-pod-com-erro>

minikube ssh
openssl s_client -connect production.cloudfront.docker.com:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM > /tmp/cloudflare.crt
sudo cp /tmp/cloudflare.crt /usr/local/share/ca-certificates/cloudflare.crt
sudo update-ca-certificates
sudo systemctl restart containerd
exit

kubectl delete pod <nome-do-pod-com-erro>
```

| Comando | O que faz |
|---|---|
| `minikube ssh -- ls -l /usr/local/share/ca-certificates/` | Verifica se o certificado está instalado |
| `minikube ssh -- "openssl x509 -in /usr/local/share/ca-certificates/cloudflare.crt -noout -subject -issuer -dates"` | Mostra subject, issuer e validade do certificado |
| `minikube ssh -- sudo crictl pull busybox:1.36` | Testa o download de imagem direto no containerd |
| `../troubleshooting/tls-inspection/instala-ca-minikube.sh` | Automatiza captura, instalação e restart do containerd |

> O certificado se perde quando o container do minikube é recriado (`minikube delete`) e precisa ser reinstalado.

## AKS (referência, não executado)

```bash
az login                                                   # autentica na Azure (abre o navegador)
az group create --name rg-teste-aks --location <regiao>    # grupo de recursos do teste (apagar o grupo = apagar tudo)
az aks create --resource-group rg-teste-aks --name aks-teste --node-count 1
                                                           # cluster com 1 node; conferir o tamanho de VM na documentação
az aks get-credentials --resource-group rg-teste-aks --name aks-teste
                                                           # baixa o kubeconfig e aponta o kubectl para o cluster
kubectl get nodes                                          # mesmo comando usado no minikube
az aks upgrade --resource-group rg-teste-aks --name aks-teste --kubernetes-version <versao>
                                                           # atualiza a versão (Control Plane e nodes)
az aks update --resource-group rg-teste-aks --name aks-teste --auto-upgrade-channel stable
                                                           # canal de atualização automática (none, patch, stable, rapid)
az group delete --name rg-teste-aks                        # limpeza: apaga o grupo e tudo dentro (evita custo esquecido)
```

> Conferir os parâmetros na documentação atual antes de usar: a CLI `az` muda entre versões.

## Utilitários de edição (nano)

| Comando / atalho | O que faz |
|---|---|
| `nano -l arquivo.yaml` | Abre com número das linhas (`-l`) |
| `Alt+U` / `Alt+E` | Desfaz / refaz |
| `Ctrl+_` | Vai para uma linha |
| `Alt+P` | Mostra espaços e tabs (essencial para YAML) |
| `Alt+/` | Vai para o fim do arquivo |

`~/.nanorc` recomendado para YAML:

```
set linenumbers
set autoindent
set tabstospaces
set tabsize 2
include "/usr/share/nano/*.nanorc"
```
