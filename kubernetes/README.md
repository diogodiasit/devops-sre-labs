# Kubernetes — Labs de deploy, rede, configuração, saúde, autoscaling e armazenamento

Conjunto de labs em cluster local (minikube no WSL) cobrindo o ciclo de vida de aplicações no Kubernetes, com manifestos declarativos versionados e troubleshooting real. Inclui o estudo de arquitetura do AKS.

## Problema

Operar aplicações em Kubernetes exige dominar mais do que `kubectl apply`:

- manter réplicas saudáveis e atualizar versões sem downtime;
- expor serviços internamente e para fora do cluster;
- separar configuração e segredos da imagem;
- detectar e recuperar aplicações travadas;
- escalar sob carga e preservar dados quando os Pods morrem.

## Solução

Cada lab tem manifesto próprio em [`manifests/`](./manifests/):

| Lab | Manifestos | O que demonstra |
|---|---|---|
| Deploy e Service | [`webserver.yaml`](./manifests/webserver.yaml) | Deployment com 3 réplicas + Service ClusterIP; DNS interno; rolling update e rollback |
| Ingress | [`apps-teste.yaml`](./manifests/apps-teste.yaml), [`ingress-teste.yaml`](./manifests/ingress-teste.yaml) | Roteamento por caminho (`/app1`, `/app2`) com ingress-nginx para dois Services |
| ConfigMap e Secret | [`config-teste.yaml`](./manifests/config-teste.yaml), [`vitrine.yaml`](./manifests/vitrine.yaml), [`vitrine-arq.yaml`](./manifests/vitrine-arq.yaml) | Configuração entregue como variáveis (`envFrom`) e como arquivos montados em volume |
| Readiness probe | [`readiness-probe.yaml`](./manifests/readiness-probe.yaml) | Verifica se o Pod está pronto para receber tráfego. Quando a probe falha, o Service para de enviar requisições ao Pod (READY `0/1`), mas o container continua rodando, sem reinício |
| Liveness probe | [`liveness-probe.yaml`](./manifests/liveness-probe.yaml) | Verifica se a aplicação continua respondendo. A aplicação simula uma trava após 20 s, a probe falha e o kubelet reinicia o container (RESTARTS sobe) |
| HPA | [`api-catalogo-deploy.yaml`](./manifests/api-catalogo-deploy.yaml), [`escalador-catalogo-hpa.yaml`](./manifests/escalador-catalogo-hpa.yaml) | Autoscaling por CPU (meta de 50% do `requests`, 2 a 8 réplicas, janela de estabilização de 5 min) |
| Volumes persistentes | [`pvc-dados.yaml`](./manifests/pvc-dados.yaml), [`gravador-de-notas.yaml`](./manifests/gravador-de-notas.yaml), [`leitor-de-notas.yaml`](./manifests/leitor-de-notas.yaml) | PVC com provisionamento dinâmico; dado sobrevive à remoção do Pod |

Estudo de arquitetura (conceitual, sem cluster provisionado): **Namespaces e RBAC** e **AKS** (responsabilidade compartilhada, atualizações, alternativas e custo) — ver [conceitos.md](./conceitos.md#namespaces-e-rbac).

## Como rodar

```bash
minikube start --force                            # sobe o cluster local
minikube addons enable ingress                    # Ingress Controller (lab de Ingress)
minikube addons enable metrics-server             # métricas de CPU/memória (lab de HPA)
kubectl apply -f kubernetes/manifests/webserver.yaml
kubectl get all -l app=loja-frontend              # -l filtra pela label
```

Exemplo — HPA sob carga:

```bash
kubectl apply -f kubernetes/manifests/api-catalogo-deploy.yaml
kubectl apply -f kubernetes/manifests/escalador-catalogo-hpa.yaml
kubectl run gerador-carga --rm -it --image=busybox:1.36 --restart=Never -- \
  /bin/sh -c "while sleep 0.01; do wget -q -O- http://svc-catalogo; done"
kubectl get hpa escalador-catalogo --watch         # em outro terminal: acompanha TARGETS e REPLICAS
```

- `kubectl run ... --rm -it --restart=Never`: Pod temporário e interativo, removido ao sair.
- `--watch`: imprime cada mudança de estado do HPA.

Exemplo — persistência de dados:

```bash
kubectl apply -f kubernetes/manifests/pvc-dados.yaml            # PVC; o PV é criado automaticamente
kubectl apply -f kubernetes/manifests/gravador-de-notas.yaml    # Pod grava /dados/nota.txt
kubectl delete pod gravador-de-notas                             # Pod removido; PVC e PV continuam
kubectl apply -f kubernetes/manifests/leitor-de-notas.yaml      # Pod novo monta o mesmo PVC
kubectl exec leitor-de-notas -- cat /dados/nota.txt              # a nota continua lá
```

Referência completa: [comandos.md](./comandos.md).

## Resultado

- **HPA:** sob carga, o Deployment escalou de **2 → 6 Pods** e voltou para 2 após a janela de estabilização de 5 minutos. O caso de `requests` ausente (HPA em `<unknown>`) foi reproduzido e diagnosticado com `kubectl describe hpa`.
- **Volumes:** PVC de 1 Gi ficou `Bound`; a nota gravada por um Pod foi lida por outro Pod criado depois da remoção do primeiro; a limpeza com `reclaimPolicy: Delete` removeu o disco.
- **Probes:** criando e apagando `/tmp/pronto`, o Pod da readiness alternou entre READY `1/1` e `0/1` com RESTARTS em 0, ou seja, saiu e voltou do Service sem reiniciar. Na liveness, os Events mostraram `Liveness probe failed` e o RESTARTS subiu a cada trava simulada.
- **Ingress:** `/app1` e `/app2` roteados para Services distintos via `minikube tunnel`.
- **Rolling update e rollback** executados sem downtime.
- **Troubleshooting:** falha de pull de imagem (`x509: certificate signed by unknown authority`) causada por inspeção TLS, resolvida dentro do node do minikube — ver [troubleshooting/tls-inspection](../troubleshooting/tls-inspection/).
