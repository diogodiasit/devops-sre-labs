# Kubernetes — Conceitos

Arquitetura, rede, configuração, saúde, escala, armazenamento, segurança e AKS.

**Índice:** [Arquitetura](#arquitetura) · [Deployment e Service](#deployment-labels-e-service) · [Rede e Ingress](#rede-e-ingress) · [Configuração](#configmap-e-secret) · [Probes](#probes) · [HPA](#hpa-horizontal-pod-autoscaler) · [Volumes](#volumes-persistentes) · [Namespaces e RBAC](#namespaces-e-rbac) · [AKS](#aks-azure-kubernetes-service) · [YAML](#boas-práticas-de-yaml)

---

## Arquitetura

### Hierarquia básica

- **Pod:** menor unidade gerenciada pelo Kubernetes, geralmente com 1 container.
- **Node:** uma máquina (real ou virtual) onde os Pods rodam.
- **Cluster:** conjunto de nodes administrados por um mesmo Control Plane (pode ter um único node).

### Componentes internos

- O próprio Kubernetes roda como Pods no namespace `kube-system`: etcd, kube-apiserver, kube-scheduler, kube-controller-manager, kube-proxy, CoreDNS e o CNI (ex.: kindnet).
- **kubelet** e **containerd** **não** são Pods: são processos no sistema do node, responsáveis por criar e gerenciar todos os Pods (inclusive os do sistema).
- Control Plane e node são papéis **lógicos**; no minikube, os dois rodam no mesmo container (kicbase).
- Nenhum componente fala direto com outro: todos conversam apenas com o **kube-apiserver**.

Fluxo de qualquer mudança:

```
kubectl → kube-apiserver → etcd (grava o estado desejado)
        → controller-manager (detecta a diferença) → scheduler (escolhe o node)
        → kubelet (executa) → kube-proxy (ajusta a rede do Service)
```

### Minikube

- Aplicação que automatiza a criação de um cluster completo dentro de 1 container Docker.
- `minikube start` executa por baixo um `docker run` (1ª vez) ou `docker start` (container existente) e configura kubelet, CNI e kubeconfig.
- O **kubectl** é uma ferramenta separada: é o cliente que fala com qualquer cluster (local ou na nuvem), lendo `~/.kube/config`.
- Container do minikube parado não perde nada; `minikube delete` apaga tudo, inclusive certificados instalados manualmente.

### Pod x container x Deployment

- O Pod envolve um ou mais containers que compartilham IP e volumes. Na prática, quase sempre é 1 container por Pod; o segundo container, quando existe, costuma ser um sidecar (ex.: os sidecars do Grafana no lab de monitoramento).
- O Pod é descartável: o Kubernetes não o conserta, substitui por outro.
- **O que reinicia o container:** erro na aplicação, OOMKilled (falta de memória), falha de liveness.
- **O que substitui o Pod:** delete, queda do node, eviction, rolling update, redução de escala.
- Comandos que alteram o Deployment (`rollout restart`, `scale`) agem sobre todos os Pods.
- `exec` e `logs` com `deploy/nome` escolhem **um** Pod sem controle de qual; para um Pod específico, use o nome exato.

---

## Deployment, labels e Service

### Deployment

- Um Pod sozinho é frágil: se morre, nada sobe outro no lugar.
- O Deployment garante um número fixo de réplicas; se um Pod morre, outro é criado.
- `kubectl scale` define o número **final** desejado (não "adiciona").
- Nomes de Pods são gerados: `<deployment>-<hash-replicaset>-<sufixo-aleatório>`.
- O Deployment controla o **número** de Pods (via ReplicaSet); o kubelet controla a **saúde** do container.

### Labels e selector

- Label é um par `chave=valor` (ex.: `app=meu-app`).
- O Deployment aplica a label em cada Pod que cria.
- O Service **não** gerencia Pods: guarda só uma regra (*selector*) e roteia para os Pods que combinam com ela.
- `kubectl expose` copia o selector do Deployment automaticamente; em YAML, ele é escrito manualmente.
- Os nomes do Deployment, dos Pods e do Service são independentes: **o que liga tudo é a label**.

### Service e portas

- O IP de um Pod muda quando ele é recriado; o IP do Service (ClusterIP) é fixo.
- `port`: porta em que o Service recebe conexões. `targetPort`: porta dos Pods (se omitida, copia `port`).
- Quem decide a porta em que o Pod escuta é a aplicação dentro da imagem; o Service só direciona tráfego.
- Um Service pode ter várias portas (cada uma com `name`, `port`, `targetPort`), útil para HTTP + métricas.

### `kubectl port-forward` (ferramenta de teste)

- Cria um túnel entre uma porta local e **um** Pod do cluster.
- Usa o Service só para escolher o Pod; depois vai direto nele (sem o balanceamento real).
- Caminho: navegador → Windows → WSL → kubectl → kube-apiserver → kubelet do node → Pod.
- O túnel só existe enquanto o comando está rodando.

### Imperativo x declarativo

- **Imperativo** (`create`, `expose`, `scale`, `set image`): "faça esta ação agora".
- **Declarativo** (YAML + `kubectl apply -f`): "este é o estado desejado". Pode ser aplicado várias vezes; só muda o que for diferente.
- **Em produção:** YAML versionado no Git e aplicado por pipeline de CI/CD.

### Rolling update e rollback

- `kubectl set image` troca a imagem gradualmente: sobe 1 Pod novo, espera ficar saudável e só então remove 1 antigo. Em nenhum momento todos ficam fora do ar.
- `kubectl rollout undo` volta à versão anterior com o mesmo mecanismo gradual; ReplicaSets antigos ficam com 0 réplicas justamente para isso.
- **Atenção:** se o Deployment foi criado via `apply`, o `undo` não altera a "última configuração aplicada" — um próximo `apply` sobrescreve o rollback com o que estiver no YAML.

---

## Rede e Ingress

### DNS interno

- O CoreDNS resolve o nome do Service para o seu IP fixo; o kube-proxy distribui entre os Pods vivos com a label certa.
- Mesmo namespace: nome curto (`svc-banco`). Outro namespace: `svc-banco.dados`. Nome completo: `svc-banco.dados.svc.cluster.local`.
- Sempre apontar para o **nome do Service**, nunca para IP de Pod.

### Ingress

- O objeto Ingress só guarda **regras** (host/caminho → Service); não executa nada.
- O **Ingress Controller** (um Pod com nginx) é quem executa as regras. Sem controller, nada funciona.
- `ingressClassName` define qual controller lê aquela regra.
- Service atua na camada 4 (IP e porta); Ingress na camada 7 (host e caminho).
- Cadeia completa: DNS → IP do load balancer → node → controller → Service → Pod. O Control Plane guarda as regras, mas fica **fora** do caminho do tráfego.
- O controller é um Pod comum: o scheduler escolhe o node (pode ser forçado com nodeSelector, affinity ou taints). **Em produção:** 2 ou mais réplicas em nodes diferentes.
- O Ingress cuida só da porta de entrada; URLs internas (ex.: `/pisos/carvalho`) são da aplicação.
- `pathType: Prefix` vale para o caminho e tudo que começa com ele; a regra mais específica vence.
- **503** quase sempre = Service sem Pod pronto (label errada ou Pod não pronto). **404** = caminho sem regra, ou a aplicação não conhece o caminho.
- O ingress-nginx foi anunciado como aposentado (manutenção até março/2026); o sucessor oficial é o **Gateway API**.

### Saída do Pod para a rede externa (ex.: banco na nuvem)

- Caminho: Pod → node → rede da nuvem (VNet) → destino.
- O node faz **NAT**: troca o IP de origem pelo dele e registra a conexão numa tabela, usada para devolver a resposta ao Pod certo.
- Conexão ociosa por muito tempo perde a entrada na tabela → usar keep-alive ou connection pool.
- Precisa haver rede entre cluster e banco: mesma VNet, VNet peering ou Private Endpoint.
- Private Endpoint: o banco ganha IP privado na VNet; o nome precisa resolver para esse IP (zona de DNS privada).

**Diagnóstico de conectividade**

| Sintoma | Causa provável |
|---|---|
| Timeout | Algo bloqueando (firewall, NetworkPolicy, IP não liberado) |
| Connection refused | Chegou ao destino, mas nada escutava na porta |
| Nome não resolve | DNS |

### Produção x laboratório

- **Produção:** o IP público vem do load balancer da nuvem (Service `LoadBalancer` no AKS).
- **Minikube:** `minikube tunnel` faz o papel do load balancer; só existe no laboratório.

---

## ConfigMap e Secret

- A imagem é imutável e igual em todos os ambientes; só a configuração muda e entra de fora.
- **ConfigMap:** configuração comum (URL, nível de log). **Secret:** dado sensível (senha, token).
- **Secret não é cofre:** é só base64 (`kubectl get secret ... | base64 -d` revela o valor).
- Proteção real: RBAC (quem pode ler secrets), criptografia em repouso e cofre externo (Azure Key Vault). Secret com valor real **nunca** vai para o Git.
- O ConfigMap não sabe quem o usa: o Deployment o referencia pelo **nome** (`envFrom`).
- ConfigMap e Secret só são lidos por Pods do **mesmo namespace**.
- O nome da chave é um contrato entre o código e o ConfigMap/Secret. No .NET, a variável `Db__Server` sobrescreve `Db:Server` do `appsettings`; o valor externo vence, e o `appsettings` fica com os padrões.

### Variável de ambiente x arquivo montado

| | Variável de ambiente | Arquivo (volume) |
|---|---|---|
| Atualização | O Pod recebe uma **cópia** quando é criado; mudança exige `rollout restart` | Atualiza sozinho em ~1 minuto (a aplicação precisa reler); com `subPath` não atualiza |
| Uso recomendado | Configuração simples | Certificados e segredos sensíveis (menos exposição em logs) |

- Um volume tem duas partes: `volumes` (**de onde** vem) e `volumeMounts` (**onde** aparece no container), ligadas pelo campo `name`.
- Volume de Secret/ConfigMap não persiste dados: é uma janela para o objeto no cluster.

---

## Probes

Testes de saúde executados pelo **kubelet**.

| Probe | Pergunta | Se falhar |
|---|---|---|
| **Readiness** | O Pod está pronto para receber tráfego? | Sai da lista do Service, **sem** reiniciar (cobre app ainda iniciando ou sem acesso ao banco) |
| **Liveness** | A aplicação está viva? | O kubelet reinicia o **container** (`RESTARTS` sobe); o Pod continua o mesmo |

- Tipos de teste: `exec` (comando), `httpGet` (ex.: `/health`) e `tcpSocket` (porta).
- **Em produção:** a liveness deve testar só a própria aplicação, nunca dependências como o banco — senão o Kubernetes reinicia tudo sem resolver nada.

---

## HPA (Horizontal Pod Autoscaler)

Quem participa quando a carga sobe:

| Componente | Papel |
|---|---|
| **HPA** | Compara o uso de CPU com a meta e decide quantas réplicas o Deployment deve ter |
| **metrics-server** | Coleta o uso atual de CPU e memória de cada Pod no kubelet; é a fonte de dados do HPA |
| **Service** | Distribui as requisições entre os Pods prontos, inclusive os recém-criados |
| **Scheduler** | Escolhe o node de cada Pod novo com base nos `requests` e no espaço livre |
| **Cluster Autoscaler** | Adiciona nodes quando há Pods em `Pending` por falta de espaço, e remove nodes ociosos (no AKS, é uma opção do node pool) |
| **Pods placeholder** (overprovisioning) | Pods de baixa prioridade que reservam espaço; no pico são despejados e liberam vaga na hora, enquanto o Cluster Autoscaler sobe um node novo |

### Recursos de cada Pod

- **requests (reserva):** força garantida; base do cálculo do HPA e do Scheduler. Sem requests de CPU → HPA mostra `<unknown>`.
- **limits (teto):** máximo que o Pod pode usar, emprestando capacidade ociosa do node. CPU no teto → *throttling* (fica lento).
- O empréstimo vem só da capacidade ociosa; quando o dono da reserva precisa, recebe na hora (o kernel reajusta).
- **Pegadinha:** sem requests mas com limits, o Kubernetes copia limits para requests.
- Memória não pode ser devolvida aos poucos → falta = **OOMKilled**. Prática: limits de memória = requests.
- Sem requests e sem limits → Pod **BestEffort**, o primeiro a ser expulso.
- No teto de CPU o Pod não recusa requisições: fica lento, e a fila fica no próprio Pod (memória), não no Service.

### Regras do HPA

- `averageUtilization`: % da reserva em que cada Pod deve trabalhar (ex.: 50%). É **meta**, não gatilho.
- `minReplicas` / `maxReplicas`: mínimo 2 garante alta disponibilidade; o máximo protege custo e cluster.
- Decide pela **média** dos Pods → um Pod sobrecarregado pode se esconder na média.
- Sobe rápido e desce devagar (`stabilizationWindowSeconds: 300`) → evita *flapping*.
- Padrão de subida: a cada 15 s, dobra ou soma 4 Pods (o que for maior) → por isso 2 → 6.
- metrics-server fora do ar → o HPA congela no último número.
- **Com HPA, remover `replicas` do Deployment** — senão cada `apply`/pipeline briga com o HPA.
- O HPA olha CPU (esforço), não volume de requisições. Requisições/s exigem métricas customizadas (Prometheus, KEDA).

### Camadas de escala

- **HPA:** mais Pods · **VPA:** Pods maiores · **Cluster Autoscaler:** mais nodes.
- Pod sobe em segundos; node (VM) em minutos.
- **Custo:** na nuvem paga-se por VM (node), não por Pod → só há economia quando um node é desligado.

### Debug

- `describe hpa`: **Metrics** (esforço), **Conditions** (`ScalingActive` = enxerga a métrica? `AbleToScale` = pode agir?) e **Events** (decisões e erros).
- HPA `<unknown>`: (1) metrics-server fora; (2) falta requests de CPU (`missing request for cpu`).
- **Events x logs:** Events são o que o Kubernetes registra sobre o objeto (temporários); logs são o que a aplicação escreve. Pod não chega a rodar → `describe`; Pod roda e falha → `logs`.
- ReplicaSet: `DESIRED` (deveria ter) / `CURRENT` (existe) / `READY` (pronto). READY menor = Pod com problema.

---

## Volumes persistentes

O disco interno do container morre com o Pod. Banco de dados e arquivos importantes precisam de disco **fora** do Pod.

### Peças

| Peça | Papel |
|---|---|
| **PV** (PersistentVolume) | O disco real registrado no cluster, criado automaticamente; tem ID, tamanho, modo de acesso e política |
| **PVC** (PersistentVolumeClaim) | O **pedido** de disco (tamanho, tipo, modo de acesso), com nome fixo; é o que a aplicação referencia |
| **StorageClass** | Define o tipo de disco e quem o cria (provisionamento dinâmico) |
| **Driver CSI** | Componente que fala com a nuvem (Azure) e cria o disco |

Fluxo: escrever o PVC → o CSI pede o disco à nuvem → a nuvem cria o disco → o Kubernetes cria o PV → o PVC fica `Bound` → o Pod usa o PVC pelo nome.

### Regras

- O Pod aponta para o **PVC**, nunca para o PV: o mesmo YAML roda em qualquer cluster (teste, homologação, produção), cada um com seu disco.
- 1 PVC = 1 PV.
- Tamanho do PVC só aumenta (se a StorageClass permitir). Nome, StorageClass e modo de acesso não mudam; trocar o nome = disco novo e vazio.
- PV é do cluster; PVC é do namespace.
- Modos de acesso: `ReadWriteOnce` (1 node), `ReadWriteMany` (vários nodes), `ReadOnlyMany`. Azure Disk = RWO.
- `reclaimPolicy: Delete` apaga o disco junto com o PVC; `Retain` mantém. **Em produção, com dado importante: Retain.**
- O PVC não é liberado enquanto um Pod o usa (fica `Terminating`).

### Backup

- **Disco persistente não é backup.**
- Snapshot (`VolumeSnapshot`) = foto do disco; a restauração cria um PVC novo.
- Banco de dados: backup lógico (dump) guardado fora do disco.
- Azure Backup para AKS e Velero automatizam o processo.
- Responsabilidade compartilhada: a nuvem fornece a ferramenta; o time liga, agenda e **testa a restauração**.

### StatefulSet

- Deployment: Pods intercambiáveis.
- StatefulSet: Pods com nome fixo (`banco-0`, `banco-1`), subida em ordem e disco próprio para cada um.

### Em produção

- Banco de dados costuma ser gerenciado (Azure SQL, PostgreSQL Flexible Server).
- Secret/ConfigMap em volume entregam configuração (temporário); o PVC guarda dado da aplicação (permanente).

---

## Namespaces e RBAC

### Namespace

- Pasta lógica de organização dentro do cluster, guardada no Control Plane; não é um lugar físico.
- Um node pode ter Pods de vários namespaces, e um namespace pode ter Pods em todos os nodes.
- Permite repetir nomes em pastas diferentes e aplicar permissões e limites por pasta.
- **Não isola a rede sozinho:** para isso é preciso NetworkPolicy.

### Identidade

- O Kubernetes não tem cadastro de usuários: ele só confere um documento (token ou certificado).
- O **kubeconfig** (`clusters`, `users`, `contexts`) diz para onde ir e como obter o token; `certificate-authority-data` permite validar o apiserver.
- Com login central (OIDC), o provedor valida a senha e emite o token; o apiserver confere assinatura, `aud` e validade.

### RBAC

- **Role:** o que pode ser feito, dentro de um namespace.
- **RoleBinding:** quem recebe a Role (usuário ou grupo vindo do token).
- RBAC só **libera**: o que não está escrito é proibido. `resourceNames` limita a permissão a objetos específicos.
- `Forbidden` pode ser sintoma de referência errada (nome de Role, grupo ou namespace).
- **Em produção:** menor privilégio, atenção especial a quem pode ler `secrets` e apagar PVCs.

---

## AKS (Azure Kubernetes Service)

- Serviço gerenciado da Azure para criar e operar clusters Kubernetes. É o Kubernetes padrão: mesmo kubectl e mesmos YAMLs usados no minikube.
- Mercado prefere Kubernetes gerenciado (AKS/EKS/GKE) a self-managed, exceto em cenários on-premises ou com time de infraestrutura dedicado.

### Responsabilidade compartilhada

| Azure cuida | O cliente cuida |
|---|---|
| Control Plane (apiserver, etcd, scheduler), redundância, falhas, certificados e manutenção; publica imagem nova de node (SO) toda semana | Nodes (tamanho, quantidade, node pools, custo), atualização de versão, rede (VNet, Private Endpoint, firewall), segurança (RBAC, Entra ID, Secrets), backup, monitoramento e aplicações (réplicas, probes, HPA) |

- O AKS provisiona os nodes (VMs na assinatura do cliente), mas a responsabilidade sobre eles é do cliente.
- Sem AKS (self-managed), o time monta e mantém o Control Plane (3 servidores para alta disponibilidade), o etcd e seu backup, certificados e atualizações.
- Não é SaaS: é serviço gerenciado, mais próximo de PaaS. SaaS = software pronto; IaaS = só a VM.

### Atualizações

- Por padrão **nada** atualiza sozinho (canal `none`): o cluster fica na versão em que foi criado.
- Cada versão do Kubernetes tem cerca de 12 meses de suporte.
- Control Plane e nodes precisam ficar em versões próximas; o AKS atualiza primeiro o Control Plane, depois os nodes.
- Atualizar: manual (CLI, portal ou IaC) ou por canal automático (`patch`, `stable`, `rapid`), com janela de manutenção.
- A imagem do node (SO) é outra atualização: sai toda semana, mas nodes em execução só a recebem se aplicada (ou com o canal `NodeImage`).
- Atualizar nodes recria as VMs → a aplicação precisa de 2+ réplicas e probes.
- Testar a atualização em cluster de teste antes de produção.

### Variações e alternativas na Azure

| Opção | Quando usar |
|---|---|
| AKS Standard | Mais controle, mais trabalho operacional (modelo dos labs) |
| AKS Automatic | A Azure assume mais (nodes, escala), com boas práticas já ligadas |
| Fleet Manager | Administrar vários clusters juntos (ex.: atualizações coordenadas) |
| Container Apps | Rodar containers com escala automática sem operar Kubernetes |
| ACI | Um container isolado ou tarefa pontual, sem orquestração |

- Quanto mais a Azure gerencia, menos trabalho e menos controle.
- O **ACR** (Azure Container Registry) guarda as imagens; o AKS as puxa de lá.

### Integrações e custo

- Integrações prontas: Entra ID + RBAC, driver CSI de Azure Disk/Files (StorageClass), Service `LoadBalancer` com IP público, Cluster Autoscaler (opção do node pool), ACR e Key Vault.
- Control Plane no nível Free (sem SLA, não indicado para produção); paga-se pelas VMs dos nodes e pelos discos.
- Contas de teste/estudante têm crédito limitado e podem ter restrição de região, tamanho de VM e cota de vCPUs.
- Cuidados em lab: grupo de recursos exclusivo, 1 node pequeno, alerta de orçamento e remoção do grupo de recursos no fim.

---

## Boas práticas de YAML

- `name` identifica um objeto (único por tipo dentro do namespace); `labels` agrupam vários objetos; `selector` é o filtro que encontra objetos pelas labels.
- O filtro `-l` só encontra objetos que **têm** a label no próprio `metadata` (o selector não conta).
- Chaves fixas do Kubernetes (`name`, `labels`, `image`...) x chaves livres (valores dentro de `labels`/`selector`).
- Itens irmãos na mesma coluna · só espaços, nunca Tab · hífen = item de lista.
- `apply -f` constrói, `delete -f` desmonta: o arquivo é a planta da infraestrutura (infraestrutura como código).
