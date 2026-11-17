"""Testes das telas (rotas do Flask), simulando um navegador."""
from conftest import entrar


def test_ranking_abre_com_o_primeiro_curso(cliente):
    resposta = cliente.get("/ranking?curso=1")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Universidade Federal do Planalto" in html
    assert html.index("Planalto") < html.index("Horizonte")      # UFPL antes da UNIHZ


def test_filtro_privada_esconde_publicas(cliente):
    html = cliente.get("/ranking?curso=1&tipo=PRIVADA").get_data(as_text=True)
    assert "Planalto" not in html and "Horizonte" in html


def test_detalhes_mostra_pitch_e_gratuita(cliente):
    html = cliente.get("/oferta/1").get_data(as_text=True)
    assert "Gratuita" in html and "algoritmos" in html


def test_avaliar_exige_login(cliente):
    resposta = cliente.get("/oferta/5/avaliar")
    assert resposta.status_code == 302 and "/login" in resposta.headers["Location"]


def test_login_com_senha_errada(cliente):
    html = entrar(cliente, "carlos@techbr.com", "errada").get_data(as_text=True)
    assert "inválidos" in html


def test_fluxo_completo_avaliar_e_moderar(cliente):
    entrar(cliente, "carlos@techbr.com")
    resposta = cliente.post("/oferta/5/avaliar", data={
        "nota_empregabilidade": "5", "nota_preparo": "5", "nota_soft_skills": "5",
        "comentario": "Excelente"}, follow_redirects=True)
    assert "moderação" in resposta.get_data(as_text=True)
    cliente.get("/logout")

    entrar(cliente, "admin@rankedu.com")
    painel = cliente.get("/admin").get_data(as_text=True)
    assert "Excelente" in painel
    assert cliente.get("/admin").status_code == 200


def test_empresario_nao_acessa_admin(cliente):
    entrar(cliente, "carlos@techbr.com")
    assert cliente.get("/admin").status_code == 403


def test_cadastro_exige_empresa_e_cargo(cliente):
    html = cliente.post("/cadastro", data={"nome": "Ana", "email": "ana@x.com", "senha": "123456",
                                           "empresa": "", "cargo": ""}).get_data(as_text=True)
    assert "RN05" in html


def test_cadastro_e_login_automatico(cliente):
    resposta = cliente.post("/cadastro", data={"nome": "Ana", "email": "ana@x.com", "senha": "123456",
                                               "empresa": "Acme", "cargo": "RH"}, follow_redirects=True)
    assert "Bem-vindo(a), Ana" in resposta.get_data(as_text=True)


def test_admin_nao_remove_instituicao_com_ofertas(cliente):
    entrar(cliente, "admin@rankedu.com")
    html = cliente.post("/admin/instituicoes/1/remover", follow_redirects=True).get_data(as_text=True)
    assert "RESTRICT" in html


def test_admin_cadastra_oferta(cliente):
    entrar(cliente, "admin@rankedu.com")
    cliente.post("/admin/ofertas", data={"instituicao_id": "4", "curso_id": "3", "modalidade": "EAD",
                                         "cpc": "3", "conceito_enade": "", "mensalidade": "350"})
    html = cliente.get("/ranking?curso=3").get_data(as_text=True)
    assert "Atlântica" in html
