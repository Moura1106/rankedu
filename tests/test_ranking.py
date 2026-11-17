"""Testes das regras de cálculo: RN01, RN02, RN06 e RN07."""
import pytest

from models import (AvaliacaoMercado, Curso, Instituicao, Modalidade, OfertaCurso, StatusAvaliacao,
                    TipoInstituicao)
from ranking import Ranking
from repositorios import OfertaRepositorio


def oferta(cpc=None, enade=None, notas=(), tipo=TipoInstituicao.PRIVADA, mensalidade=1000.0):
    inst = Instituicao(1, "Teste", "T", tipo, "São Paulo", "SP")
    o = OfertaCurso(1, inst, Curso(1, "CC", "TI", "pitch"), Modalidade.PRESENCIAL, enade, cpc, mensalidade)
    o.avaliacoes = [AvaliacaoMercado(i, 1, 1, *n, status=StatusAvaliacao.APROVADA) for i, n in enumerate(notas)]
    return o


# ---------------------------------------------------------------- RN01
def test_formula_60_40():
    assert Ranking.calcular_nota_final(5, 4) == pytest.approx(4.6)


def test_sem_avaliacao_nota_final_igual_oficial():
    assert Ranking.calcular_nota_final(4, None) == 4


def test_sem_nota_oficial_nao_tem_nota_final():
    assert Ranking.calcular_nota_final(None, 5) is None


# ---------------------------------------------------------------- RN02
def test_media_do_mercado_e_media_das_medias():
    o = oferta(cpc=4, notas=[(5, 5, 4), (4, 4, 5)])
    assert o.media_mercado() == pytest.approx(4.5)


def test_avaliacao_pendente_nao_conta():
    o = oferta(cpc=4, notas=[(1, 1, 1)])
    o.avaliacoes[0].status = StatusAvaliacao.PENDENTE
    assert o.media_mercado() is None
    assert o.nota_final() == 4


# ---------------------------------------------------------------- RN06
def test_sem_cpc_usa_enade():
    assert oferta(cpc=None, enade=3).nota_oficial() == 3


def test_ofertas_sem_nota_oficial_vao_para_o_fim():
    ofertas = [oferta(), oferta(cpc=2), oferta(cpc=5)]
    resultado = Ranking.gerar(ofertas)
    assert [o.cpc for o in resultado] == [5, 2, None]


# ---------------------------------------------------------------- RN07
def test_publica_mostra_gratuita():
    assert oferta(tipo=TipoInstituicao.PUBLICA, mensalidade=0).mensalidade_formatada() == "Gratuita"


def test_privada_mostra_valor_em_reais():
    assert oferta(mensalidade=1890).mensalidade_formatada() == "R$ 1.890,00"


# ------------------------------------------- com os dados do seed.sql
def test_ranking_de_ciencia_da_computacao(conexao):
    """Mesmos valores documentados na Fase 3 (seção 3c)."""
    ofertas = Ranking.gerar(OfertaRepositorio(conexao).listar(curso_id=1))
    resultado = [(o.instituicao.sigla, round(o.nota_final(), 2)) for o in ofertas]
    assert resultado == [("UFPL", 4.6), ("UNIHZ", 4.2), ("UEV", 4.0), ("FAD", 3.13), ("UPI", 3.0)]


def test_python_e_view_sql_dao_o_mesmo_resultado(conexao):
    """O cálculo em Python (classe Ranking) bate com a view vw_ranking do banco."""
    view = {l["oferta_id"]: l["nota_final"] for l in conexao.execute("SELECT * FROM vw_ranking")}
    for o in OfertaRepositorio(conexao).listar():
        if view[o.id] is None:
            assert o.nota_final() is None
        else:
            assert o.nota_final() == pytest.approx(view[o.id])


def test_filtro_por_tipo(conexao):
    ofertas = Ranking.gerar(OfertaRepositorio(conexao).listar(curso_id=1), tipo="PUBLICA")
    assert {o.instituicao.sigla for o in ofertas} == {"UFPL", "UEV"}
