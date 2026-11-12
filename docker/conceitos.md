# Docker — Conceitos

Como imagens e containers se comportam, e como isso orienta o troubleshooting em produção.

## RUN x CMD

- **RUN:** executa durante o **build** da imagem. Roda uma vez e o resultado fica gravado numa camada. Usado para instalar dependências, ajustar permissões etc.
- **CMD:** executa quando o container **inicia** (`docker run`). Roda toda vez; é o processo principal que mantém o container vivo.
- Exemplo (imagem oficial do nginx): `CMD ["nginx", "-g", "daemon off;"]`. O `daemon off` mantém o nginx em primeiro plano — necessário porque o container termina no instante em que o processo principal termina.

## Políticas de restart

```bash
docker run -d --restart unless-stopped -p 8080:80 nginx
```

| Política | Comportamento |
|---|---|
| `no` | Nunca reinicia (padrão) |
| `always` | Sempre reinicia, inclusive após reboot do host |
| `unless-stopped` | Sempre reinicia, exceto se tiver sido parado manualmente |
| `on-failure` | Só reinicia se o processo terminar com erro |

## Camada gravável (writable layer)

- Uma imagem é composta de camadas **somente leitura**.
- Ao iniciar um container, o Docker adiciona uma camada fina e **gravável** por cima.
- Alterações manuais feitas dentro do container ficam só nessa camada, não na imagem.

### O que sobrevive e o que não sobrevive

- `docker start` (religar o **mesmo** container parado): a camada gravável continua → alterações manuais sobrevivem.
- Container removido e recriado a partir da imagem (ex.: Kubernetes substituindo um container com problema): a camada gravável é descartada → o estado volta ao da imagem.

## Infraestrutura imutável ("cattle, not pets")

- Servidor tradicional (VM, físico) = **pet**: é cuidado individualmente, corrigido no lugar, e a correção permanece.
- Container = **cattle**: descartável por natureza. Corrigir "no lugar" não é confiável, porque o container pode ser substituído a qualquer momento.
- **Prática correta:** nunca corrigir de forma permanente dentro de um container em execução. Corrigir na **origem** (código ou configuração), gerar uma imagem nova e substituir o container antigo.

## Fluxo de troubleshooting em containers

1. Diagnosticar dentro do container em execução (`docker exec`, `docker stats`, `docker logs`).
2. Identificar **onde** está a causa:
   - código da aplicação → encaminhar ao time de desenvolvimento e gerar imagem nova;
   - Dockerfile (dependência, variável, permissão) → corrigir o Dockerfile;
   - configuração de execução (`docker run`/compose: limite de recurso, porta, variável de ambiente) → ajustar o compose ou o comando.
3. Se necessário, aplicar correção temporária no container para estancar o incidente, sabendo que ela **não** é permanente.
4. Corrigir na origem e gerar imagem nova (`docker build`).
5. Substituir o container antigo pelo novo.

## Problema de imagem x problema de código

| | Problema de **imagem** (ambiente) | Problema de **código** (aplicação) |
|---|---|---|
| Exemplos | Versão errada de dependência; variável de ambiente faltando; pacote/lib do sistema ausente; limite de recurso não configurado (sem `--memory`); porta errada exposta; permissão de arquivo errada (faltou `RUN chmod`) | Vazamento de memória; query mal otimizada; erro de lógica; falta de tratamento de erro; vulnerabilidade (ex.: SQL injection) |
| Sinal típico | Falha **já na inicialização** (arquivo não encontrado, permission denied) | O container sobe normalmente e o problema aparece **sob uso** |

Pergunta rápida para diferenciar: *"isso aconteceria se a aplicação rodasse direto na máquina, sem Docker?"*

- Sim → problema de código.
- Não (só acontece pela forma como o container foi montado/configurado) → problema de imagem.

## Permissões no Dockerfile

| Instrução | Uso |
|---|---|
| `RUN chmod 644 /caminho/arquivo` | Ajusta a permissão depois de copiar |
| `COPY --chown=usuario:grupo origem destino` | Já define o dono no momento da cópia |
| `USER nome_usuario` | Faz o processo final rodar sem root — boa prática que limita o impacto de uma invasão |

## Divisão de responsabilidades

- **DevOps/SRE** é dono do "**como** isso roda": ambiente, dependências, permissões, recursos e configuração de deploy (tudo que vive no Dockerfile/compose).
- **Desenvolvimento** é dono do "**o que** isso faz": regras de negócio e bugs de código.
- Em produção, DevOps/SRE diagnostica o problema e direciona a correção para o lugar certo, sem tentar corrigir a lógica da aplicação sozinho.
