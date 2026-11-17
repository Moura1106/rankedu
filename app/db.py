"""
db.py — Conexão com o SQLite e criação do banco.

O banco é criado a partir dos scripts da pasta banco/
(schema_sqlite.sql e seed.sql): o código não tem um "segundo modelo"
escondido, ele usa exatamente o modelo físico documentado.

Uso direto:  python db.py --recriar   (apaga e recria o banco de exemplo)
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PASTA_APP = Path(__file__).resolve().parent
PASTA_SQL = PASTA_APP.parent / "banco"
SCHEMA = PASTA_SQL / "schema_sqlite.sql"
SEED = PASTA_SQL / "seed.sql"
BANCO_PADRAO = PASTA_APP / "rankedu.db"


def conectar(caminho: str | Path) -> sqlite3.Connection:
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row             # linhas acessíveis por nome: linha["nome"]
    conexao.execute("PRAGMA foreign_keys = ON")   # o SQLite liga as FKs por conexão
    return conexao


def criar_banco(caminho: str | Path, com_dados_exemplo: bool = True) -> None:
    """Executa o schema (e o seed) num banco novo."""
    conexao = conectar(caminho)
    try:
        conexao.executescript(SCHEMA.read_text(encoding="utf-8"))
        if com_dados_exemplo:
            conexao.executescript(SEED.read_text(encoding="utf-8"))
        conexao.commit()
    finally:
        conexao.close()


def garantir_banco(caminho: str | Path) -> None:
    """Cria o banco só se ele ainda não existir."""
    if not Path(caminho).exists():
        criar_banco(caminho)


if __name__ == "__main__":
    if "--recriar" in sys.argv and BANCO_PADRAO.exists():
        BANCO_PADRAO.unlink()
    garantir_banco(BANCO_PADRAO)
    print(f"Banco pronto em {BANCO_PADRAO}")
