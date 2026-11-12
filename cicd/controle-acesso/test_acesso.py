# =========================================================
# test_acesso.py
# Testes automatizados do sistema_acesso.py
# =========================================================

import pytest
from sistema_acesso import (
    criar_usuario,
    criar_credencial,
    processar_tentativa_acesso,
    MockControladora,
    usuarios,
    credenciais,
)


# ---------------------------------------------------------
# FIXTURE: roda automaticamente ANTES de cada teste abaixo.
# Sem isso, um teste poderia "sujar" os dados do próximo.
# Os dicionários em memória são limpos antes de cada teste.
# ---------------------------------------------------------
@pytest.fixture(autouse=True)
def limpar_dados():
    usuarios.clear()
    credenciais.clear()


# ---------------------------------------------------------
# TESTE 1: cadastro básico de usuário e credencial
# ---------------------------------------------------------
def test_criar_usuario_e_credencial():
    usuario = criar_usuario(nome="Diogo Dias", cargo="Analista")
    credencial = criar_credencial(usuario_id=usuario["id"], numero_cartao="111")

    assert usuario["nome"] == "Diogo Dias"
    assert credencial["usuario_id"] == usuario["id"]
    assert credencial["status"] == "ativa"


# ---------------------------------------------------------
# TESTE 2: acesso válido, dentro do horário, controladora libera
# ---------------------------------------------------------
def test_acesso_liberado_dentro_do_horario():
    usuario = criar_usuario(nome="Diogo Dias", cargo="Analista")
    criar_credencial(usuario_id=usuario["id"], numero_cartao="111")

    # O horário é simulado via parâmetro, sem depender do relógio real
    controladora_falsa = MockControladora(resposta="liberado")
    resultado = processar_tentativa_acesso(
        numero_cartao="111",
        hora_tentativa="10:00",
        controladora=controladora_falsa,
    )

    assert resultado["status"] == "acesso_concedido"
    # Confere também se o comando "destravar" chegou à controladora
    assert controladora_falsa.comando_enviado == "destravar"


# ---------------------------------------------------------
# TESTE 3: credencial que não existe
# ---------------------------------------------------------
def test_acesso_negado_credencial_inexistente():
    controladora_falsa = MockControladora(resposta="liberado")
    resultado = processar_tentativa_acesso(
        numero_cartao="999",  # nunca foi cadastrado
        hora_tentativa="10:00",
        controladora=controladora_falsa,
    )

    assert resultado["status"] == "acesso_negado"
    assert resultado["motivo"] == "credencial_invalida"


# ---------------------------------------------------------
# TESTE 4: fora do horário permitido
# ---------------------------------------------------------
def test_acesso_negado_fora_de_horario():
    usuario = criar_usuario(nome="Diogo Dias", cargo="Analista")
    criar_credencial(usuario_id=usuario["id"], numero_cartao="111")

    controladora_falsa = MockControladora(resposta="liberado")
    resultado = processar_tentativa_acesso(
        numero_cartao="111",
        hora_tentativa="22:00",  # fora das 08:00-18:00
        controladora=controladora_falsa,
    )

    assert resultado["status"] == "acesso_negado"
    assert resultado["motivo"] == "fora_de_horario"


# ---------------------------------------------------------
# TESTE 5: dentro do horário, credencial válida, mas a
# controladora (hardware) recusa mesmo assim
# ---------------------------------------------------------
def test_acesso_negado_pela_controladora():
    usuario = criar_usuario(nome="Diogo Dias", cargo="Analista")
    criar_credencial(usuario_id=usuario["id"], numero_cartao="111")

    controladora_falsa = MockControladora(resposta="negado")
    resultado = processar_tentativa_acesso(
        numero_cartao="111",
        hora_tentativa="10:00",
        controladora=controladora_falsa,
    )

    assert resultado["status"] == "acesso_negado"
    assert resultado["motivo"] == "controladora_negou"
