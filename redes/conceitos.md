# Redes — Conceitos

Fundamentos de rede aplicados a troubleshooting de aplicações e infraestrutura.

> **Por que isso importa em produção:** boa parte dos incidentes chega como "a aplicação não responde", "não consigo acessar o servidor" ou "o site caiu". Resolver exige entender como a informação viaja entre duas máquinas. Toda rede resolve três coisas: **um endereço, um caminho e uma linguagem combinada**.

## DNS (Domain Name System)

- Traduz nome (`google.com`) em endereço IP. Sem DNS, seria preciso saber o IP de cada serviço, e qualquer troca de IP quebraria os clientes.
- Teste: `dig google.com` (a seção `ANSWER` traz o IP e o TTL).

### TTL (Time To Live)

- Cada resposta de DNS tem um tempo de cache (visível no `dig`, ex.: 300 segundos).
- Mudanças de DNS **não** são instantâneas: cada máquina/rede mantém a resposta antiga até o TTL expirar.
- Por isso, após alterar um registro, algumas máquinas atualizam antes de outras. Parece aleatório, mas é o TTL de cada uma vencendo em momentos diferentes.
- **Em produção:** explica sintomas como "a aplicação foi atualizada, mas só parou de funcionar em algumas máquinas". Antes de uma migração, reduza o TTL com antecedência.

## Endereço IP

- Número que identifica um host na rede (ex.: `142.250.218.14`).
- Parte do endereço identifica a rede e parte identifica o host; a máscara (ex.: `/24`) define onde fica a divisão. É isso que permite rotear o pacote até a rede certa.

## Portas

- Um mesmo IP pode rodar vários serviços; a porta indica **para qual serviço** a conexão vai. O IP leva até a máquina, e a porta leva até o processo que está escutando nela.
- Para ver quem escuta em cada porta: `sudo ss -tlnp`.

| Porta | Serviço |
|---|---|
| 22 | SSH (acesso remoto seguro) |
| 80 | HTTP (sem criptografia) |
| 443 | HTTPS (com criptografia) |

## HTTP e HTTPS

- **HTTP:** protocolo de requisição e resposta entre cliente e servidor. Trafega em texto puro: qualquer equipamento no caminho consegue ler e alterar o conteúdo.
- **HTTPS:** o mesmo HTTP dentro de uma conexão TLS. O conteúdo vai criptografado, e o certificado prova que o servidor é quem diz ser.

Handshake TLS, de forma simplificada:

1. O cliente pede uma conexão segura na porta 443.
2. O servidor envia seu certificado (prova de identidade).
3. Os dois negociam uma chave **temporária**, válida só para aquela sessão.
4. Toda a conversa passa a ser criptografada com essa chave.

Veja um caso real de falha de TLS em [troubleshooting/tls-inspection](../troubleshooting/tls-inspection/).

### Códigos de status HTTP

| Faixa | Significado | Exemplos |
|---|---|---|
| 2xx | Sucesso | 200 OK |
| 3xx | Redirecionamento | 301 permanente, 302 temporário |
| 4xx | Erro do **cliente** | 400 requisição malformada, 401 não autenticado, 403 sem permissão, 404 não encontrado |
| 5xx | Erro do **servidor** | 500 erro na aplicação, 502 Bad Gateway, 503 serviço indisponível |

**401 x 403**

- 401 = "não sei quem você é, identifique-se".
- 403 = "sei quem você é, mas você não tem permissão".

**500 x 502** (relevante para Application Gateway e proxy reverso)

- 500 = a aplicação respondeu, mas falhou internamente (bug no código).
- 502 = o proxy/gateway não recebeu resposta válida do backend (VM fora do ar, health probe reprovando, timeout).

## SSH (Secure Shell)

- Acesso remoto **dentro** do servidor (não só "olhar de fora", como no HTTP).
- Uma vez conectado, os comandos Linux rodam no servidor remoto.
- Porta 22, com toda a comunicação criptografada.
- Comando: `ssh usuario@ip-do-servidor`

### Autenticação por par de chaves

- **Chave privada:** fica só na máquina do usuário; nunca é compartilhada.
- **Chave pública:** pode ser distribuída livremente; vai para o servidor.
- O que é cifrado ou verificado com a chave pública só pode ser respondido por quem tem a chave privada correspondente. Por isso a pública pode ser distribuída sem risco.
- A chave privada **nunca trafega pela rede**: o servidor envia um desafio matemático, só quem tem a chave privada correta consegue resolver, e apenas a **resposta** volta.

### Como a chave pública chega ao servidor

1. Gerar o par localmente: `ssh-keygen`
2. Guardar a chave privada com segurança.
3. Levar a chave pública ao servidor, de uma destas formas:
   - `ssh-copy-id usuario@ip-do-servidor` (usa senha só nessa primeira vez);
   - colar manualmente em `~/.ssh/authorized_keys` no servidor;
   - informar na criação da VM na nuvem (Azure, AWS etc.) — a forma mais comum em produção.
4. A partir daí, `ssh usuario@ip-do-servidor` conecta sem senha.

> Depois de configurado, quem guarda a informação de confiança é o **servidor** (diferente de uma senha salva no navegador, que fica no computador do usuário).

## Fluxo completo: acessar um site HTTPS

1. O DNS traduz o nome do site em IP.
2. O IP leva a conexão até o servidor certo.
3. A porta 443 leva a conexão até o serviço certo dentro do servidor.
4. O handshake TLS estabelece uma chave temporária de criptografia.
5. A comunicação segue protegida até o fim da sessão.
