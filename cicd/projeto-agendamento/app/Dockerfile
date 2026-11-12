# Imagem usada pelo CI para rodar os testes no mesmo ambiente em que a aplicação é empacotada.
FROM python:3.12-slim

WORKDIR /app

# requirements.txt entra antes do código para aproveitar o cache de camadas:
# se só o código mudar, o pip install não é refeito no próximo build.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY sistema_agendamento.py test_agendamento.py ./

CMD ["pytest"]
