# =========================================================
# sistema_acesso.py
# Simulação simplificada de um sistema de controle de acesso
# (usuários, credenciais, horário permitido e controladora)
# =========================================================

# Armazenamento em memória no lugar de um banco de dados, suficiente para os testes.
usuarios = {}
credenciais = {}


def criar_usuario(nome, cargo):
    # Gera um ID novo contando quantos usuários já existem
    novo_id = len(usuarios) + 1
    # Guarda o usuário no "banco" (dicionário) usando o ID como chave
    usuarios[novo_id] = {"id": novo_id, "nome": nome, "cargo": cargo}
    return usuarios[novo_id]


def criar_credencial(usuario_id, numero_cartao):
    # Associa um cartão a um usuário, já nascendo com status "ativa"
    credenciais[numero_cartao] = {
        "usuario_id": usuario_id,
        "numero_cartao": numero_cartao,
        "status": "ativa"
    }
    return credenciais[numero_cartao]


def verificar_horario(hora_tentativa, hora_inicio, hora_fim):
    # Confere se a hora da tentativa está dentro da janela permitida
    # Ex: "10:00" está entre "08:00" e "18:00"? Devolve True ou False
    return hora_inicio <= hora_tentativa <= hora_fim


class MockControladora:
    # Mock da controladora de acesso: substitui o hardware (catraca) nos testes
    # e devolve a resposta configurada no teste ("liberado" ou "negado").

    def __init__(self, resposta="liberado"):
        # Executado ao criar uma nova controladora falsa
        self.resposta = resposta          # o que ela vai "responder"
        self.comando_enviado = None       # guarda o último comando recebido

    def enviar_comando(self, comando):
        # Simula o envio de um comando físico (ex: "destravar")
        self.comando_enviado = comando
        return self.resposta


def processar_tentativa_acesso(numero_cartao, hora_tentativa, controladora):
    # Função principal: junta todas as regras, na ordem certa
    # (mais barato/rápido primeiro, hardware por último)

    # 1) A credencial existe e está ativa?
    credencial = credenciais.get(numero_cartao)
    if credencial is None or credencial["status"] != "ativa":
        return {"status": "acesso_negado", "motivo": "credencial_invalida"}

    # 2) Está dentro do horário permitido (08:00 às 18:00)?
    if not verificar_horario(hora_tentativa, "08:00", "18:00"):
        return {"status": "acesso_negado", "motivo": "fora_de_horario"}

    # 3) Só agora "fala" com a controladora (real ou falsa)
    resposta = controladora.enviar_comando("destravar")

    # 4) Decide o resultado final com base na resposta da controladora
    if resposta == "liberado":
        return {"status": "acesso_concedido", "motivo": None}
    else:
        return {"status": "acesso_negado", "motivo": "controladora_negou"}
