# =========================================================
# sistema_agendamento.py
# Agendamento de barbearia com a agenda dividida em blocos fixos
# de 30 minutos
# =========================================================

# Cada barbeiro tem uma lista dos horários (blocos de 30min) já ocupados.
# Ex: {"joao": ["09:00", "09:30"]}
agenda_ocupada = {}

DURACAO_SERVICOS = {
    "corte": 30,
    "barba": 30,          # duração real menor, arredondada para 1 bloco
    "corte+barba": 60,    # 45 min reais, arredondados para 2 blocos
}

EXPEDIENTE_INICIO = "09:00"
EXPEDIENTE_FIM = "18:00"
ALMOCO_INICIO = "12:00"
ALMOCO_FIM = "13:00"


def gerar_blocos(horario_inicio, duracao_minutos):
    # Converte início + duração na lista de blocos de 30 min que o serviço ocupa.
    # Ex: ("09:00", 60) -> ["09:00", "09:30"]
    h, m = map(int, horario_inicio.split(":"))
    total_minutos_inicio = h * 60 + m

    quantidade_blocos = duracao_minutos // 30
    blocos = []
    for i in range(quantidade_blocos):
        minutos_do_bloco = total_minutos_inicio + (i * 30)
        hora_bloco = minutos_do_bloco // 60
        min_bloco = minutos_do_bloco % 60
        blocos.append(f"{hora_bloco:02d}:{min_bloco:02d}")
    return blocos


def todos_dentro_do_expediente(blocos):
    # Todos os blocos precisam estar dentro do expediente
    return all(EXPEDIENTE_INICIO <= b < EXPEDIENTE_FIM for b in blocos)


def algum_bloco_no_almoco(blocos):
    # Basta um bloco no almoço para recusar
    return any(ALMOCO_INICIO <= b < ALMOCO_FIM for b in blocos)


def agendar(barbeiro, servico, horario_inicio):
    # 1) O serviço existe?
    if servico not in DURACAO_SERVICOS:
        return {"status": "recusado", "motivo": "servico_invalido"}

    # 2) Blocos que o serviço ocupa a partir do horário pedido
    duracao = DURACAO_SERVICOS[servico]
    blocos_necessarios = gerar_blocos(horario_inicio, duracao)

    # 3) Cabe no expediente?
    if not todos_dentro_do_expediente(blocos_necessarios):
        return {"status": "recusado", "motivo": "fora_do_expediente"}

    # 4) Cai no almoço?
    if algum_bloco_no_almoco(blocos_necessarios):
        return {"status": "recusado", "motivo": "horario_de_almoco"}

    # 5) Algum bloco já está ocupado na agenda desse barbeiro?
    ocupados_do_barbeiro = agenda_ocupada.get(barbeiro, [])
    if any(bloco in ocupados_do_barbeiro for bloco in blocos_necessarios):
        return {"status": "recusado", "motivo": "conflito_de_horario"}

    # 6) Passou em todas as regras: reserva os blocos
    agenda_ocupada.setdefault(barbeiro, []).extend(blocos_necessarios)
    return {"status": "confirmado", "motivo": None, "blocos_ocupados": blocos_necessarios}
