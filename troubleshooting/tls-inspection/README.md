# Troubleshooting — Falha de pull de imagens por inspeção TLS

Diagnóstico e correção de `x509: certificate signed by unknown authority` ao baixar imagens no Docker e no Kubernetes (minikube), em uma estação atrás de um gateway com inspeção de tráfego HTTPS (Cloudflare Gateway).

## Problema

**Sintoma no Docker:**

```
$ docker run hello-world
... x509: certificate signed by unknown authority
```

**Sintoma no Kubernetes (minikube):** node `NotReady`, ou Pods em `ErrImagePull` / `ImagePullBackOff` com o mesmo erro x509 nos Events.

## Investigação

O Docker baixa imagens em duas etapas, com hosts diferentes:

| Host | Função | Situação |
|---|---|---|
| `registry-1.docker.io` | Metadados (manifest) | OK |
| `production.cloudfront.docker.com` | Camadas da imagem (conteúdo pesado) | **Falhando** |

Os hosts foram testados um a um, eliminando hipóteses: `registry-1.docker.io` primeiro (descartado) e depois o host de conteúdo, onde estava o problema.

```bash
openssl s_client -connect production.cloudfront.docker.com:443 -showcerts \
  </dev/null 2>/dev/null | grep -E "subject=|issuer="
```

- `openssl s_client -connect host:443`: abre uma conexão TLS de teste com o host.
- `-showcerts`: exibe a cadeia de certificados recebida.
- `</dev/null`: envia entrada vazia para a conexão encerrar logo; `2>/dev/null` descarta mensagens de erro.
- `grep -E "subject=|issuer="`: mostra só quem o certificado **diz ser** e quem o **assinou**.

Resultado:

```
subject=CN = production.cloudfront.docker.com
issuer=... O = "Cloudflare, Inc." ... CN = Gateway CA - Cloudflare Managed G2
```

O *subject* dizia ser do Docker, mas o *issuer* era o Cloudflare Gateway. **A divergência entre os dois indica interceptação do tráfego.**

## Causa raiz

A rede tinha um **Cloudflare Gateway fazendo inspeção TLS**: ele intercepta a conexão, fala com o destino real em nome do cliente e devolve a resposta com um certificado **gerado na hora**, assinado pela CA do próprio gateway. Como essa CA não estava na lista de confiança do Linux (nem do node do minikube), a conexão era recusada.

Em resumo: o *subject* diz para qual host o certificado foi emitido, e o *issuer* diz qual CA o assinou. O cliente só aceita a conexão se o issuer estiver na sua lista de CAs confiáveis. Na interceptação, o subject continua sendo o do Docker, mas o issuer passa a ser a CA do gateway, que o sistema não conhecia. A correção é adicionar essa CA à lista de confiança.

Ponto-chave: o certificado **não** é um arquivo pronto para baixar de um site oficial. Ele é **capturado ao vivo** da própria conexão interceptada e então adicionado à lista de confiança local.

## Solução

### Docker (host Linux/WSL)

```bash
# 1. Capturar a cadeia de certificados de uma conexão real
openssl s_client -connect production.cloudfront.docker.com:443 -showcerts \
  </dev/null 2>/dev/null | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' > /tmp/chain.pem

# 2. Conferir quantos certificados vieram (esperado: poucos, ex.: 2)
grep -c "BEGIN CERTIFICATE" /tmp/chain.pem

# 3. Registrar como confiável no sistema
cp /tmp/chain.pem /usr/local/share/ca-certificates/cloudflare-gateway.crt
update-ca-certificates

# 4. Reiniciar o Docker para carregar a nova lista de confiança
service docker restart

# 5. Validar
docker run hello-world
```

- `awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/'`: extrai só os blocos de certificado da saída do openssl.
- `grep -c`: conta as linhas que contêm o padrão (`-c` = *count*).
- `update-ca-certificates`: recompila a lista de CAs confiáveis do sistema a partir de `/usr/local/share/ca-certificates/`.

### Kubernetes (node do minikube)

O node do minikube é um container com sua própria lista de CAs, e quem baixa as imagens é o **containerd**:

```bash
minikube ssh
openssl s_client -connect production.cloudfront.docker.com:443 -showcerts </dev/null 2>/dev/null \
  | openssl x509 -outform PEM > /tmp/cloudflare.crt
sudo cp /tmp/cloudflare.crt /usr/local/share/ca-certificates/cloudflare.crt
sudo update-ca-certificates
sudo systemctl restart containerd
exit
kubectl delete pod <nome-do-pod-com-erro>    # o controlador recria o Pod, que agora consegue baixar a imagem
```

- `openssl x509 -outform PEM`: converte o certificado do servidor para o formato PEM.

Automatizado em [`instala-ca-minikube.sh`](./instala-ca-minikube.sh), que captura, instala e reinicia o containerd em um único comando:

```bash
./troubleshooting/tls-inspection/instala-ca-minikube.sh
```

Verificação:

```bash
minikube ssh -- "openssl x509 -in /usr/local/share/ca-certificates/cloudflare.crt -noout -subject -issuer -dates"
minikube ssh -- sudo crictl pull busybox:1.36    # testa o pull direto no containerd
```

> O certificado se perde quando o minikube é recriado (`minikube delete`) e precisa ser reinstalado; por isso o script existe.

## Resultado

- `docker run hello-world` voltou a funcionar no host.
- No minikube, o node voltou a `Ready` e os Pods saíram de `ImagePullBackOff` após o restart do containerd.
- Procedimento reprodutível via script para cada recriação do cluster.

## Lições para produção

- TLS inspection é comum em redes corporativas (proxies, antivírus, SASE/Cloudflare Gateway).
- **Nunca confie só no *subject*; sempre verifique o *issuer*.** Issuer desconhecido = alguém no meio do caminho.
- Diagnóstico por eliminação: testar host por host em vez de assumir que "o Docker Hub está fora".
- Em frota corporativa, o ideal é distribuir a CA da organização pelo gerenciamento de dispositivos ou pela imagem base, em vez de capturá-la manualmente em cada máquina.
