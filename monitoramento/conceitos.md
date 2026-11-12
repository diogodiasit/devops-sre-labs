# Monitoramento — Conceitos

Observabilidade com Prometheus, Grafana e Alertmanager no Kubernetes, do lab local ao desenho de produção.

**Índice:** [Observabilidade](#observabilidade) · [Componentes](#componentes-da-stack) · [Origem das métricas](#origem-das-métricas) · [PromQL](#promql) · [Helm](#helm) · [Alertas](#alertas) · [Recursos e HPA](#requests-limits-e-hpa) · [Boas práticas](#boas-práticas) · [Laboratório x produção](#laboratório-x-produção)

---

## Observabilidade

| Sinal | Responde | Exemplo |
|---|---|---|
| **Métricas** | Quanto? Está piorando? | CPU, memória, requisições/s, taxa de erro |
| **Logs** | O que aconteceu? | Linha de erro da aplicação |
| **Traces** | Onde a requisição demorou? | Caminho de uma requisição entre serviços |

- **Modelo pull:** o Prometheus busca (*scrape*) as métricas em cada alvo, em intervalos fixos; a aplicação só expõe um endpoint `/metrics`.
- **Labels:** cada série é identificada pelo nome da métrica + labels (`pod`, `namespace`, `container`). É por elas que se filtra e agrupa.

---

## Componentes da stack

| Componente | Papel |
|---|---|
| **Prometheus** | Coleta, armazena (séries temporais) e avalia as regras |
| **Alertmanager** | Recebe os alertas, agrupa, silencia e entrega (Telegram, Slack, e-mail) |
| **Grafana** | Dashboards sobre o Prometheus |
| **Prometheus Operator** | Traduz CRDs (`ServiceMonitor`, `PrometheusRule`) em configuração do Prometheus |
| **node-exporter** | Métricas do node |
| **kube-state-metrics** | Estado dos objetos do Kubernetes |

### ServiceMonitor

- Diz ao Prometheus **o que** coletar: seleciona Services por label e define porta e caminho.
- O ServiceMonitor só descreve a coleta, ele não é o alvo. `mon-apiserver` é o nome do ServiceMonitor criado pelo chart; o apiserver, o coredns e o kubelet já existiam no cluster, e o chart apenas passou a coletá-los.
- Componentes do Control Plane que o minikube não expõe (etcd, scheduler, controller-manager, kube-proxy) foram desligados no values para não gerar alvos `DOWN`.

---

## Origem das métricas

| Prefixo | Fonte | Quantidade | O que mede |
|---|---|---|---|
| `node_` | node-exporter | 1 por node | CPU, memória, disco e rede da máquina |
| `container_` | kubelet (cAdvisor) | 1 por node | Consumo de cada container |
| `kube_` | kube-state-metrics | 1 por cluster | Estado dos objetos (réplicas, reinícios, fase do Pod) |

- **Metrics Server** é outra coisa: lê do kubelet só o valor **atual** de CPU e memória, para o HPA e o `kubectl top`. Não guarda histórico.

---

## PromQL

- **`rate()`:** contadores só crescem (`_total`); `rate(x[5m])` transforma em taxa por segundo. Para CPU, o resultado é em núcleos.
- **`by()`:** define o nível de detalhe da soma — `sum by (pod)` = um valor por Pod; `sum by (namespace)` = um por namespace.
- **`container!=""`:** remove a série que representa o Pod inteiro e evita contar em dobro.
- **Recording rules:** consultas pesadas pré-calculadas pelo Prometheus; os dashboards do chart usam várias.

---

## Helm

| Conceito | Definição |
|---|---|
| **Chart** | Pacote de manifestos com templates |
| **Values** | Parâmetros do chart; o arquivo próprio é **mesclado** com os padrões (só o que muda precisa ser escrito) |
| **Release** | Uma instalação do chart com nome (`mon`); cada `upgrade` gera uma nova revisão |
| **Umbrella chart** | Chart que agrega outros (`kube-prometheus-stack` inclui Grafana, kube-state-metrics, node-exporter); cada subchart tem seu bloco no values |
| **`fullnameOverride`** | Substitui o prefixo gerado nos nomes dos objetos |
| **`upgrade` / `rollback`** | Aplica um values novo / volta para uma revisão anterior |

- Chave com endereço errado no values é **ignorada sem erro**: o chart simplesmente não a lê.

---

## Alertas

### Estados

| Estado | Significado |
|---|---|
| **Inactive** | A condição do `expr` é falsa |
| **Pending** | A condição é verdadeira, mas ainda não durou o `for` |
| **Firing** | Durou o `for`: o alerta vai para o Alertmanager |

- O `for` filtra picos rápidos e evita alerta falso.
- O `namespace` no `metadata` da `PrometheusRule` é só onde o objeto fica; o **escopo** do alerta vem do `expr` (no lab, todas as namespaces).
- A label `release: mon` é obrigatória: o Prometheus só carrega regras com o seletor do release.

### Roteamento no Alertmanager

- `route`: árvore de decisão (receiver padrão + exceções em `routes`).
- `group_by`: alertas com as mesmas labels viram uma única notificação.
- `group_wait` / `group_interval` / `repeat_interval`: espera inicial, intervalo entre atualizações do grupo e reenvio enquanto o alerta continuar ativo.
- `send_resolved`: avisa também a resolução.

---

## Requests, limits e HPA

- `requests` e `limits` são definidos **por container**; o Pod é a soma.
- O HPA compara o uso com a **soma dos requests** dos containers: Pod com sidecars tem requests maior.
- Percentual acima de 100% do `requests` é possível (uso de capacidade ociosa até o `limits`). No lab, o Grafana chegou a 326% do requests.

---

## Boas práticas

- **4 sinais de ouro:** latência, tráfego, erros e saturação.
- **Alertar sintoma, não causa:** o usuário sente latência e erro, não CPU alta.
- **Runbook:** cada alerta com link para o procedimento (o que verificar, como mitigar).
- **Fadiga de alerta:** alerta sem ação é ignorado, e o importante se perde no meio. Todo alerta precisa ser acionável.

---

## Laboratório x produção

| Item | Laboratório | Produção |
|---|---|---|
| Acesso | `kubectl port-forward` | Ingress com TLS e autenticação |
| Senha do Grafana | Secret padrão do chart | Cofre (Azure Key Vault) e login central (Entra ID) |
| Alertmanager | 1 réplica | 3 réplicas em cluster |
| Retenção | 6 h, disco local | Armazenamento de longo prazo: Thanos/Mimir ou Azure Managed Prometheus + Azure Managed Grafana |
| Destino dos alertas | Telegram | Slack/Teams e PagerDuty, por severidade |
| Watchdog | Descartado (`null`) | Enviado a um serviço externo (*dead man's switch*): se parar de chegar, o monitoramento está fora do ar |
