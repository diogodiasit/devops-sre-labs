# =========================================================
# test_agendamento.py
# Testes do sistema_agendamento.py
# =========================================================

import pytest
from sistema_agendamento import agendar, agenda_ocupada


# ---------------------------------------------------------
# Limpa a agenda antes de cada teste, para que um teste não
# dependa do estado deixado pelo anterior
# ---------------------------------------------------------
@pytest.fixture(autouse=True)
def limpar_agenda():
    agenda_ocupada.clear()


# ---------------------------------------------------------
# TESTE 1: agendamento simples, horário livre
# ---------------------------------------------------------
def test_agendamento_confirmado():
    resultado = agendar(barbeiro="joao", servico="corte", horario_inicio="09:00")
    assert resultado["status"] == "confirmado"


# ---------------------------------------------------------
# TESTE 2: mesmo barbeiro, mesmo horário -> conflito
# ---------------------------------------------------------
def test_conflito_mesmo_barbeiro_mesmo_horario():
    agendar(barbeiro="joao", servico="corte", horario_inicio="09:00")

    resultado = agendar(barbeiro="joao", servico="corte", horario_inicio="09:00")

    assert resultado["status"] == "recusado"
    assert resultado["motivo"] == "conflito_de_horario"


# ---------------------------------------------------------
# TESTE 3: barbeiros diferentes, mesmo horário -> sem conflito
# (é aqui que a regra de "agenda por barbeiro" é testada de verdade)
# ---------------------------------------------------------
def test_sem_conflito_barbeiros_diferentes():
    agendar(barbeiro="joao", servico="corte", horario_inicio="09:00")

    resultado = agendar(barbeiro="marcelo", servico="corte", horario_inicio="09:00")

    assert resultado["status"] == "confirmado"


# ---------------------------------------------------------
# TESTE 4: corte+barba (2 blocos) bloqueia um agendamento
# que cairia no segundo bloco dele
# ---------------------------------------------------------
def test_conflito_servico_que_ocupa_dois_blocos():
    # corte+barba às 09:00 ocupa os blocos 09:00 e 09:30
    agendar(barbeiro="joao", servico="corte+barba", horario_inicio="09:00")

    # corte às 09:30 cai no segundo bloco -> deve recusar
    resultado = agendar(barbeiro="joao", servico="corte", horario_inicio="09:30")

    assert resultado["status"] == "recusado"
    assert resultado["motivo"] == "conflito_de_horario"


# ---------------------------------------------------------
# TESTE 5: fora do expediente
# ---------------------------------------------------------
def test_recusado_fora_do_expediente():
    resultado = agendar(barbeiro="joao", servico="corte", horario_inicio="19:00")

    assert resultado["status"] == "recusado"
    assert resultado["motivo"] == "fora_do_expediente"


# ---------------------------------------------------------
# TESTE 6: cai no horário de almoço
# ---------------------------------------------------------
def test_recusado_horario_de_almoco():
    resultado = agendar(barbeiro="joao", servico="corte", horario_inicio="12:00")

    assert resultado["status"] == "recusado"
    assert resultado["motivo"] == "horario_de_almoco"


# ---------------------------------------------------------
# TESTE 7: serviço que não existe no catálogo
# ---------------------------------------------------------
def test_recusado_servico_invalido():
    resultado = agendar(barbeiro="joao", servico="manicure", horario_inicio="09:00")

    assert resultado["status"] == "recusado"
    assert resultado["motivo"] == "servico_invalido"
