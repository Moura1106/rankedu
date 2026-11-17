"""Testes do fluxo do UC07 (diagrama de sequência) e da moderação (UC11):
RN02, RN03, RN04 e RN05."""
import pytest

from controllers import AvaliacaoController, RegraNegocioErro
from models import StatusAvaliacao
from repositorios import OfertaRepositorio, UsuarioRepositorio


@pytest.fixture
def controller(conexao):
    return AvaliacaoController(conexao)


@pytest.fixture
def carlos(conexao):
    return UsuarioRepositorio(conexao).buscar(2)     # empresário do seed


@pytest.fixture
def marina(conexao):
    return UsuarioRepositorio(conexao).buscar(1)     # administradora do seed


def test_senha_do_seed_autentica(carlos):
    assert carlos.autenticar("senha123")
    assert not carlos.autenticar("errada")


def test_sem_login_nao_avalia(controller):
    with pytest.raises(RegraNegocioErro):
        controller.avaliar(None, 5, (5, 5, 5), None)


def test_admin_nao_avalia_rn05(controller, marina):
    with pytest.raises(RegraNegocioErro):
        controller.avaliar(marina, 5, (5, 5, 5), None)


@pytest.mark.parametrize("notas", [(0, 3, 3), (6, 3, 3), ("a", 3, 3), (3, 3)])
def test_notas_invalidas_rn02(controller, carlos, notas):
    with pytest.raises(RegraNegocioErro):
        controller.avaliar(carlos, 5, notas, None)


def test_nova_avaliacao_entra_pendente_rn04(controller, carlos, conexao):
    controller.avaliar(carlos, 5, (5, 5, 5), "Ótimos alunos")
    nova = controller.avaliacoes.buscar_do_usuario(carlos.id, 5)
    assert nova.status == StatusAvaliacao.PENDENTE
    # pendente não muda o ranking: UPI continua com a nota oficial (3,0)
    assert OfertaRepositorio(conexao).buscar(5).nota_final() == 3.0


def test_reavaliar_atualiza_e_volta_para_pendente_rn03(controller, carlos):
    # Carlos já tem a avaliação 1 (APROVADA) para a oferta 3
    mensagem = controller.avaliar(carlos, 3, (1, 1, 1), "mudei de ideia")
    assert "atualizada" in mensagem
    avaliacao = controller.avaliacoes.buscar_do_usuario(carlos.id, 3)
    assert avaliacao.id == 1                    # mesma linha, não duplicou
    assert avaliacao.status == StatusAvaliacao.PENDENTE
    assert avaliacao.nota_preparo == 1


def test_aprovar_faz_a_avaliacao_entrar_no_ranking(controller, carlos, marina, conexao):
    controller.avaliar(carlos, 5, (5, 5, 5), None)
    nova = controller.avaliacoes.buscar_do_usuario(carlos.id, 5)
    controller.moderar(marina, nova.id, aprovar=True)
    # 0,6 x 3 + 0,4 x 5 = 3,8
    assert OfertaRepositorio(conexao).buscar(5).nota_final() == pytest.approx(3.8)


def test_empresario_nao_modera(controller, carlos):
    with pytest.raises(RegraNegocioErro):
        controller.moderar(carlos, 7, aprovar=True)
