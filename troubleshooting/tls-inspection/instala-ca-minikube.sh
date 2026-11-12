#!/bin/bash
# Captura o certificado apresentado pelo gateway de inspeção TLS, instala como CA confiável
# no node do minikube e reinicia o containerd. Rodar de novo sempre que o cluster for recriado.
minikube ssh -- "openssl s_client -connect production.cloudfront.docker.com:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | sudo tee /usr/local/share/ca-certificates/cloudflare.crt >/dev/null && sudo update-ca-certificates && sudo systemctl restart containerd"
