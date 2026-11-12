# Terraform — Conceitos

Infraestrutura como código (IaC) com Terraform, do ciclo local ao fluxo de equipe.

## Fundamentos

| Conceito | Definição |
|---|---|
| **IaC** | Infraestrutura descrita em código (`.tf`) e versionada no Git. É **declarativo**: descreve *o que* se quer, não *como* fazer |
| **Provider** | Plugin que fala com a plataforma: `azurerm` (Azure), `aws`, `google`, `local` (arquivos na máquina), `random` |
| **Resource** | Item a ser criado. Formato: `resource "TIPO" "APELIDO" { campos }` |
| **Variable e tfvars** | Campos parametrizáveis (`variables.tf`) e seus valores (`terraform.tfvars`) |
| **Output** | Valores exibidos ao fim do `apply` |
| **Referência `TIPO.APELIDO.CAMPO`** | Lê o valor de outro recurso e cria **dependência implícita** (o outro é criado antes) |

## State

- O `terraform.tfstate` registra qual recurso real corresponde a cada bloco do código (IDs, atributos, dependências). É gerado no primeiro `apply`, e é com ele que o `plan` calcula o que criar, alterar ou destruir.
- **Nunca** editar manualmente e **nunca** versionar no Git — pode conter segredos.
- **Em produção:** o state fica num *remote backend* com lock (na Azure, Storage Account), para que duas pessoas não apliquem ao mesmo tempo.

## Drift

Diferença entre a realidade e o código (alguém alterou o recurso fora do Terraform). O `plan` detecta.

## Ciclo

`init` → `validate` → `plan` → `apply` → `destroy`. O `plan` é a prévia e não altera nada.

## Fluxo em equipe

1. Branch e push.
2. Pull Request: a esteira roda `init`, `validate` e `plan`; o revisor lê o plan.
3. Merge na `main`.
4. A esteira de deploy roda o `apply` (em produção, com aprovação via *Environment*).

- O gatilho de cada esteira (`push`, `pull_request`, push na `main`) é definido no YAML do pipeline.
- A branch guarda o trabalho até o dia de aplicar; o plan é refeito antes do merge, porque um plan antigo fica desatualizado.
- **Ninguém roda `apply` do próprio notebook em ambiente compartilhado.**

## Ecossistema

- **Terraform x Bicep:** Bicep só funciona na Azure; Terraform é multi-nuvem.
- **Terraform x Ansible:** Terraform cria a infraestrutura; Ansible configura o que roda dentro dela.
- **OpenTofu:** fork open source, criado após a mudança de licença da HashiCorp em 2023.
- **Próximos passos naturais:** remote state com lock, módulos, ambientes (dev, homologação, produção) e `import`.

## Labs deste repositório

- **[lab-local](./lab-local/):** providers `local` e `random`. Cria arquivos de texto na máquina, sem nuvem — exercita o ciclo completo e o state.
- **[lab-azure](./lab-azure/):** provider `azurerm`. Resource Group, VNet e Storage Account. Validado com `terraform validate`; **não aplicado**, porque a subscription estava com o crédito de teste expirado (estado `Warned`) e não cria recursos.

> O crédito de avaliação da Azure (US$ 200) vale 30 dias; depois, só com upgrade para pay-as-you-go. Uma subscription em estado `Warned` não aparece em `az account list` sem `--all`.
