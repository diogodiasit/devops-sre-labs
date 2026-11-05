# Monitoramento — Comandos

Referência dos comandos usados no lab de monitoramento (minikube no WSL). Os arquivos citados estão em [helm/](./helm/) e [manifests/](./manifests/).

## Cluster

| Comando | O que faz |
|---|---|
| `minikube start --memory=2560 --cpus=2` | Sobe o cluster com 2,5 GB de RAM (`--memory`, em MB) e 2 CPUs (`--cpus`), limite seguro para um notebook de 8 GB |
| `kubectl create namespace observabilidade` | Cria a namespace da stack |
| `kubectl get pods -n kube-system` | Pods do próprio Kubernetes (confere apiserver, coredns etc.) |

## Helm

| Comando | O que faz |
|---|---|
| `helm repo add prometheus-community https://prometheus-community.github.io/helm-charts` | Registra o repositório de charts com um apelido local |
| `helm repo update` | Atualiza o índice de charts dos repositórios registrados |
| `helm install mon prometheus-community/kube-prometheus-stack -n observabilidade -f helm/valores-monitoramento-lab.yaml` | Instala o chart como release `mon` (revisão 1); `-n` = namespace, `-f` = values próprio, mesclado com os padrões |
| `helm upgrade mon prometheus-community/kube-prometheus-stack -n observabilidade -f helm/valores-monitoramento-lab.yaml` | Aplica o values alterado (no lab: inclusão do Telegram, revisão 2) |
| `helm list -n observabilidade` | Releases instalados, revisão e status |
| `helm history mon -n observabilidade` | Histórico de revisões do release |
| `helm rollback mon 1 -n observabilidade` | Volta o release para a revisão 1 |
| `helm get values mon -n observabilidade` | Mostra o values aplicado no release |

> **Pegadinha:** chave com endereço errado no values (ex.: fora do bloco certo) é ignorada sem erro. Conferir com `helm get values`.

## Secret do Telegram

```bash
kubectl create secret generic telegram-bot-alertas --from-literal=token='SEU_TOKEN' -n observabilidade
```

- `generic`: Secret de chave/valor; `--from-literal=token=...`: cria a chave `token`, que vira o arquivo `/etc/alertmanager/secrets/telegram-bot-alertas/token` no Pod.
- Aspas simples evitam que o shell interprete caracteres do token.
- O token **nunca** vai para o Git; no values fica só o caminho (`bot_token_file`).

## Regra de alerta

| Comando | O que faz |
|---|---|
| `kubectl apply -f manifests/alerta-cpu-alta.yaml` | Cria a `PrometheusRule` `alerta-cpu-alta` |
| `kubectl get prometheusrules -n observabilidade` | Lista as regras (as do chart e a própria) |
| `kubectl run carga-teste --image=busybox:1.36 -- /bin/sh -c "while true; do :; done"` | Pod com loop infinito para elevar a CPU e disparar o alerta |
| `kubectl delete pod carga-teste` | Remove a carga; o alerta é resolvido |

## Acesso local (só laboratório)

| Comando | O que faz |
|---|---|
| `kubectl port-forward svc/mon-prometheus 9090:9090 -n observabilidade > /dev/null 2>&1 &` | Prometheus em `http://localhost:9090` |
| `kubectl port-forward svc/mon-grafana 3000:80 -n observabilidade > /dev/null 2>&1 &` | Grafana em `http://localhost:3000` (Service na porta 80) |
| `kubectl port-forward svc/mon-alertmanager 9093:9093 -n observabilidade > /dev/null 2>&1 &` | Alertmanager em `http://localhost:9093` |
| `jobs` | Lista os processos em segundo plano do terminal, numerados |
| `kill %N` | Encerra o job número `N` |

- `> /dev/null`: descarta a saída; `2>&1`: manda os erros para o mesmo lugar; `&`: roda em segundo plano, liberando o terminal.
- O port-forward se liga a **um** Pod: cai quando o Pod é recriado (ex.: após `helm upgrade`) e precisa ser refeito.

## Senha do Grafana

```bash
kubectl get secret mon-grafana -n observabilidade -o jsonpath="{.data.admin-password}" | base64 -d; echo
```

- `-o jsonpath=...`: extrai só o campo `admin-password`; `base64 -d`: decodifica o valor; `echo`: quebra de linha no fim. Usuário: `admin`.

## Diagnóstico

| Comando | O que faz |
|---|---|
| `kubectl get pods -n observabilidade` | Estado dos Pods da stack |
| `kubectl get servicemonitors -n observabilidade` | Alvos que o Prometheus sabe coletar |
| `kubectl get prometheusrules -n observabilidade` | Regras carregadas |
| `kubectl logs alertmanager-mon-alertmanager-0 -c alertmanager -n observabilidade --tail=30` | Últimas 30 linhas (`--tail`) do container `alertmanager` (`-c`), útil para erro de envio ao Telegram |

## PromQL praticado

| Consulta | O que mostra |
|---|---|
| `up` | 1 = alvo coletado, 0 = alvo fora |
| `up == 0` | Só os alvos fora do ar |
| `count(kube_pod_info)` | Quantidade de Pods no cluster |
| `sum by (pod) (container_memory_working_set_bytes{namespace="observabilidade", container!=""})` | Memória em uso por Pod |
| `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="observabilidade", container!=""}[5m]))` | CPU por Pod, em núcleos (média de 5 min) |
| `kube_pod_container_status_restarts_total` | Reinícios acumulados por container |

- `container!=""` remove a série agregada do Pod inteiro, evitando contagem dobrada.
