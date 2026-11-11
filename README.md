# DevOps & SRE Labs

Laboratórios práticos de infraestrutura, automação, CI/CD, containers, infraestrutura como código e confiabilidade — com pipelines funcionando, manifestos versionados e troubleshooting real documentado.

![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black) ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) ![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white) ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white) ![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white) ![Terraform](https://img.shields.io/badge/Terraform-844FBA?logo=terraform&logoColor=white) ![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoftazure&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white) ![Azure DevOps](https://img.shields.io/badge/Azure_DevOps-0078D7?logo=azuredevops&logoColor=white)

## Projetos em destaque

| Projeto | Entrega |
|---|---|
| [**CI/CD com GitHub Actions**](./cicd/projeto-agendamento/) | Testes em container a cada Pull Request, branch protection e publicação automática da imagem no Docker Hub após o merge |
| [**Azure DevOps**](./azure-devops/) | Migração do mesmo pipeline para Azure Repos e Azure Pipelines, com Service Connection e Build Validation na `main` |
| [**Kubernetes**](./kubernetes/) | Deploy, Ingress, ConfigMap/Secret, probes, HPA (2 → 6 Pods sob carga) e volumes persistentes, com manifestos declarativos |
| [**Monitoramento**](./monitoramento/) | Prometheus, Grafana e Alertmanager via Helm, regra de alerta própria (`PrometheusRule`) e notificação de disparo e resolução no Telegram |
| [**Terraform na Azure**](./terraform/) | IaC com `azurerm` (Resource Group, VNet, Storage Account) parametrizada e validada, mais o ciclo completo aplicado em lab local |
| [**Troubleshooting de TLS**](./troubleshooting/tls-inspection/) | Diagnóstico de `x509: unknown authority` causado por inspeção TLS e correção no Docker e no containerd do Kubernetes |

## Stack

**SO e scripting:** Linux · Bash · Python  
**Versionamento e CI/CD:** Git · GitHub Actions · Azure DevOps  
**Containers e orquestração:** Docker · Docker Compose · Kubernetes · Nginx  
**Cloud e IaC:** Azure · Terraform  
**Observabilidade:** Prometheus · Grafana · Alertmanager · Helm

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| [`cicd/`](./cicd/) | Pipelines do GitHub Actions, apps Python com `pytest` e conceitos de CI/CD |
| [`azure-devops/`](./azure-devops/) | Azure Repos, Pipelines, Service Connections, Branch Policies e equivalência com o GitHub Actions |
| [`kubernetes/`](./kubernetes/) | Manifestos, comandos e conceitos (rede, configuração, probes, HPA, volumes, RBAC, AKS) |
| [`monitoramento/`](./monitoramento/) | Values do Helm, `PrometheusRule`, comandos, PromQL e conceitos de observabilidade e alertas |
| [`terraform/`](./terraform/) | Labs `lab-local` e `lab-azure`, comandos e fluxo de IaC em equipe |
| [`docker/`](./docker/) | Dockerfile, Compose (Nginx + PostgreSQL), imagem no Docker Hub e troubleshooting de containers |
| [`troubleshooting/`](./troubleshooting/) | Casos de incidentes reais com investigação, causa raiz e correção |
| [`redes/`](./redes/) | DNS e TTL, portas, HTTP/HTTPS e códigos de status, TLS e SSH com chaves |
| [`linux/`](./linux/) | Processos, permissões, systemd, journald, busca em arquivos, variáveis de ambiente e apt |
| [`git/`](./git/) | Configuração, branches, merge, `.gitignore` e investigação de histórico |
| [`.github/workflows/`](./.github/workflows/) | Workflows de CI (testes em PR) e CD (publicação no Docker Hub) |

Padrão de documentação: `README.md` em cada projeto (problema, solução, como rodar e resultado), `comandos.md` (cada comando e flag explicados) e `conceitos.md` (fundamentos e implicações em produção).
