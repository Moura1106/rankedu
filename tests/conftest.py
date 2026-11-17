"""Configuração comum dos testes: cada teste ganha um banco NOVO e temporário,
criado com o schema e o seed da Fase 3. O banco de verdade nunca é tocado."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import db  # noqa: E402
from app import create_app  # noqa: E402


@pytest.fixture
def caminho_banco(tmp_path):
    caminho = tmp_path / "teste.db"
    db.criar_banco(caminho)
    return caminho


@pytest.fixture
def conexao(caminho_banco):
    c = db.conectar(caminho_banco)
    yield c
    c.close()


@pytest.fixture
def cliente(caminho_banco):
    app = create_app(str(caminho_banco))
    app.config["TESTING"] = True
    return app.test_client()


def entrar(cliente, email, senha="senha123"):
    return cliente.post("/login", data={"email": email, "senha": senha})
