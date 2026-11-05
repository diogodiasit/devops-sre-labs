# Monitoramento — Prometheus, Grafana e Alertmanager com alerta no Telegram

Stack de observabilidade instalada com Helm (`kube-prometheus-stack`) em cluster local (minikube no WSL), com regra de alerta própria e notificação entregue no Telegram. O values foi dimensionado para um notebook com 8 GB de RAM.

## Problema

Sem métricas e alertas, a falha só aparece quando alguém reclama. O objetivo era:

- coletar métricas de nodes, containers e objetos do Kubernetes;
- visualizar consumo por namespace e por Pod;
- disparar um alerta próprio e entregá-lo fora do cluster, avisando também a resolução;
- manter o token do bot fora do Git;
- caber num minikube com `--memory=2560 --cpus=2`.

## Solução

| Arquivo | O que define |
|---|---|
| [`helm/valores-monitoramento-lab.yaml`](./helm/valores-monitoramento-lab.yaml) | Values do `kube-prometheus-stack`: nomes curtos, recursos enxutos, componentes ocultos desligados e roteamento do Alertmanager para o Telegram |
| [`manifests/alerta-cpu-alta.yaml`](./manifests/alerta-cpu-alta.yaml) | `PrometheusRule` com o alerta `PodComCPUAlta` |

Decisões do values:

| Configuração | Motivo |
|---|---|
| `fullnameOverride: mon` | Nomes curtos e previsíveis (`svc/mon-prometheus`, `svc/mon-grafana`, `svc/mon-alertmanager`) |
| `retention: 6h` e `requests` enxutos | Reduzir disco e memória num cluster de 2,5 GB |
| `kubeEtcd`, `kubeControllerManager`, `kubeScheduler`, `kubeProxy` desligados | No minikube esses endpoints não são expostos; ligados, viram alvos `DOWN` |
| `route` → `telegram`, `group_by: ['namespace']`, `group_wait: 30s`, `group_interval: 5m`, `repeat_interval: 12h` | Agrupar alertas por namespace e evitar repetição excessiva |
| `Watchdog` e `InfoInhibitor` → receiver `'null'` | Alertas internos do chart, descartados no lab |
| `bot_token_file` + `alertmanagerSpec.secrets` | O token é lido do Secret `telegram-bot-alertas` montado no Pod; nunca aparece no values |
| `send_resolved: true` | Notifica também quando o alerta volta ao normal |

Regra `PodComCPUAlta` (label `release: mon`, exigida para o Prometheus carregar a regra):

```promql
sum by (pod, namespace) (rate(container_cpu_usage_seconds_total{container!=""}[1m])) > 0.5
```

- `for: 1m` e `severity: warning`: dispara quando um Pod passa de meio núcleo por mais de 1 minuto.

## Como rodar

```bash
minikube start --memory=2560 --cpus=2
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

cd monitoramento
kubectl create namespace observabilidade
kubectl create secret generic telegram-bot-alertas --from-literal=token='SEU_TOKEN' -n observabilidade
helm install mon prometheus-community/kube-prometheus-stack -n observabilidade -f helm/valores-monitoramento-lab.yaml
kubectl apply -f manifests/alerta-cpu-alta.yaml
kubectl get pods -n observabilidade
```

- Antes de instalar, troque `chat_id: 000000000` pelo ID real do chat. O token entra só no Secret, nunca no Git.
- `-n observabilidade`: namespace da stack; `-f`: arquivo de values aplicado por cima dos padrões do chart.

Acesso local (só laboratório):

```bash
kubectl port-forward svc/mon-prometheus 9090:9090 -n observabilidade > /dev/null 2>&1 &
kubectl port-forward svc/mon-grafana 3000:80 -n observabilidade > /dev/null 2>&1 &
kubectl port-forward svc/mon-alertmanager 9093:9093 -n observabilidade > /dev/null 2>&1 &
kubectl get secret mon-grafana -n observabilidade -o jsonpath="{.data.admin-password}" | base64 -d; echo
```

Disparar o alerta com um Pod que consome CPU sem parar:

```bash
kubectl run carga-teste --image=busybox:1.36 -- /bin/sh -c "while true; do :; done"
kubectl delete pod carga-teste    # encerra a carga; o Telegram recebe a resolução
```

Referência completa: [comandos.md](./comandos.md) · fundamentos: [conceitos.md](./conceitos.md).

## Resultado

- **Stack:** 6 Pods saudáveis na namespace `observabilidade`. O Telegram entrou com `helm upgrade` (revisão 2) sobre a instalação inicial.
- **Consumo em repouso:** o Grafana foi o maior consumidor de CPU (~10% de um núcleo), por causa dos 2 sidecars.
- **Dashboard Namespace (Pods):** o Pod `carga-teste` apareceu em ~1,9 núcleo, e o Grafana em 326% do próprio `requests`.
- **Alerta:** `PodComCPUAlta` passou por `Inactive → Pending → Firing`, chegou ao Alertmanager e foi entregue no Telegram. Depois de remover a carga, chegou a notificação de resolvido.

Mensagem recebida no Telegram:

```
Alerts Firing:
Labels:
 - alertname = PodComCPUAlta
 - namespace = default
 - pod = carga-teste
 - prometheus = observabilidade/mon-prometheus
 - severity = warning
Annotations:
 - description = O pod carga-teste na namespace default passou de meio núcleo por mais de 1 minuto.
 - summary = Pod carga-teste usando muita CPU
```
