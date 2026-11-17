"""
repositorios.py — Acesso às TABELAS do modelo físico (Fase 3, seção 3c).

Cada repositório cuida de uma tabela e converte linhas do banco em
objetos do diagrama de classes (models.py). Todo SQL usa parâmetros (?)
para evitar SQL injection.
"""
from __future__ import annotations

import sqlite3

from models import (Administrador, AvaliacaoMercado, Curso, Empresario, Instituicao,
                    Modalidade, OfertaCurso, StatusAvaliacao, TipoInstituicao, Usuario)


# ------------------------------------------------------------ conversões
def _instituicao(linha: sqlite3.Row, prefixo: str = "") -> Instituicao:
    return Instituicao(linha[prefixo + "id"], linha[prefixo + "nome"], linha[prefixo + "sigla"],
                       TipoInstituicao(linha[prefixo + "tipo"]), linha[prefixo + "cidade"],
                       linha[prefixo + "uf"], linha[prefixo + "site"])


def _curso(linha: sqlite3.Row, prefixo: str = "") -> Curso:
    return Curso(linha[prefixo + "id"], linha[prefixo + "nome"], linha[prefixo + "area"],
                 linha[prefixo + "pitch_texto"], linha[prefixo + "pitch_video_url"])


def _avaliacao(linha: sqlite3.Row) -> AvaliacaoMercado:
    return AvaliacaoMercado(linha["id"], linha["usuario_id"], linha["oferta_curso_id"],
                            linha["nota_empregabilidade"], linha["nota_preparo"],
                            linha["nota_soft_skills"], linha["comentario"], linha["data"],
                            StatusAvaliacao(linha["status"]), linha["empresa"])


def _usuario(linha: sqlite3.Row) -> Usuario:
    if linha["perfil"] == "ADMIN":
        return Administrador(linha["id"], linha["nome"], linha["email"], linha["senha_hash"])
    return Empresario(linha["id"], linha["nome"], linha["email"], linha["senha_hash"],
                      linha["empresa"], linha["cargo"])


# ----------------------------------------------------------- instituição
class InstituicaoRepositorio:
    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def listar(self) -> list[Instituicao]:
        linhas = self.conexao.execute("SELECT * FROM instituicao ORDER BY nome").fetchall()
        return [_instituicao(l) for l in linhas]

    def buscar(self, id_: int) -> Instituicao | None:
        linha = self.conexao.execute("SELECT * FROM instituicao WHERE id = ?", (id_,)).fetchone()
        return _instituicao(linha) if linha else None

    def salvar(self, i: Instituicao) -> int:
        dados = (i.nome, i.sigla, i.tipo.value, i.cidade, i.uf, i.site)
        if i.id is None:
            cursor = self.conexao.execute(
                "INSERT INTO instituicao (nome, sigla, tipo, cidade, uf, site) VALUES (?, ?, ?, ?, ?, ?)",
                dados)
            i.id = cursor.lastrowid
        else:
            self.conexao.execute(
                "UPDATE instituicao SET nome = ?, sigla = ?, tipo = ?, cidade = ?, uf = ?, site = ? "
                "WHERE id = ?", dados + (i.id,))
        self.conexao.commit()
        return i.id

    def remover(self, id_: int) -> None:
        """Falha (IntegrityError) se houver ofertas: FK com ON DELETE RESTRICT."""
        self.conexao.execute("DELETE FROM instituicao WHERE id = ?", (id_,))
        self.conexao.commit()

    def ufs(self) -> list[str]:
        return [l["uf"] for l in self.conexao.execute(
            "SELECT DISTINCT uf FROM instituicao ORDER BY uf")]


# ----------------------------------------------------------------- curso
class CursoRepositorio:
    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def listar(self) -> list[Curso]:
        return [_curso(l) for l in self.conexao.execute("SELECT * FROM curso ORDER BY nome")]

    def buscar(self, id_: int) -> Curso | None:
        linha = self.conexao.execute("SELECT * FROM curso WHERE id = ?", (id_,)).fetchone()
        return _curso(linha) if linha else None

    def salvar(self, c: Curso) -> int:
        dados = (c.nome, c.area, c.pitch_texto, c.pitch_video_url)
        if c.id is None:
            cursor = self.conexao.execute(
                "INSERT INTO curso (nome, area, pitch_texto, pitch_video_url) VALUES (?, ?, ?, ?)", dados)
            c.id = cursor.lastrowid
        else:
            self.conexao.execute(
                "UPDATE curso SET nome = ?, area = ?, pitch_texto = ?, pitch_video_url = ? WHERE id = ?",
                dados + (c.id,))
        self.conexao.commit()
        return c.id

    def remover(self, id_: int) -> None:
        self.conexao.execute("DELETE FROM curso WHERE id = ?", (id_,))
        self.conexao.commit()


# ---------------------------------------------------------- oferta_curso
SQL_OFERTA = """
SELECT o.*,
       i.id AS i_id, i.nome AS i_nome, i.sigla AS i_sigla, i.tipo AS i_tipo,
       i.cidade AS i_cidade, i.uf AS i_uf, i.site AS i_site,
       c.id AS c_id, c.nome AS c_nome, c.area AS c_area,
       c.pitch_texto AS c_pitch_texto, c.pitch_video_url AS c_pitch_video_url
FROM oferta_curso o
JOIN instituicao i ON i.id = o.instituicao_id
JOIN curso c       ON c.id = o.curso_id
"""


class OfertaRepositorio:
    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def _montar(self, linha: sqlite3.Row) -> OfertaCurso:
        oferta = OfertaCurso(linha["id"], _instituicao(linha, "i_"), _curso(linha, "c_"),
                             Modalidade(linha["modalidade"]), linha["conceito_enade"],
                             linha["cpc"], float(linha["mensalidade"]))
        oferta.avaliacoes = AvaliacaoRepositorio(self.conexao).listar_por_oferta(oferta.id)
        return oferta

    def listar(self, curso_id: int | None = None) -> list[OfertaCurso]:
        if curso_id is None:
            linhas = self.conexao.execute(SQL_OFERTA + " ORDER BY c.nome, i.nome").fetchall()
        else:
            linhas = self.conexao.execute(SQL_OFERTA + " WHERE o.curso_id = ?", (curso_id,)).fetchall()
        return [self._montar(l) for l in linhas]

    def buscar(self, id_: int) -> OfertaCurso | None:
        linha = self.conexao.execute(SQL_OFERTA + " WHERE o.id = ?", (id_,)).fetchone()
        return self._montar(linha) if linha else None

    def salvar(self, instituicao_id: int, curso_id: int, modalidade: str, conceito_enade: int | None,
               cpc: int | None, mensalidade: float, id_: int | None = None) -> int:
        dados = (instituicao_id, curso_id, modalidade, conceito_enade, cpc, mensalidade)
        if id_ is None:
            cursor = self.conexao.execute(
                "INSERT INTO oferta_curso (instituicao_id, curso_id, modalidade, conceito_enade, cpc, "
                "mensalidade) VALUES (?, ?, ?, ?, ?, ?)", dados)
            id_ = cursor.lastrowid
        else:
            self.conexao.execute(
                "UPDATE oferta_curso SET instituicao_id = ?, curso_id = ?, modalidade = ?, "
                "conceito_enade = ?, cpc = ?, mensalidade = ? WHERE id = ?", dados + (id_,))
        self.conexao.commit()
        return id_

    def remover(self, id_: int) -> None:
        """As avaliações da oferta somem junto (ON DELETE CASCADE = composição)."""
        self.conexao.execute("DELETE FROM oferta_curso WHERE id = ?", (id_,))
        self.conexao.commit()


# --------------------------------------------------------------- usuário
class UsuarioRepositorio:
    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def buscar(self, id_: int) -> Usuario | None:
        linha = self.conexao.execute("SELECT * FROM usuario WHERE id = ?", (id_,)).fetchone()
        return _usuario(linha) if linha else None

    def buscar_por_email(self, email: str) -> Usuario | None:
        linha = self.conexao.execute("SELECT * FROM usuario WHERE email = ?",
                                     (email.strip().lower(),)).fetchone()
        return _usuario(linha) if linha else None

    def cadastrar_empresario(self, e: Empresario) -> int:
        cursor = self.conexao.execute(
            "INSERT INTO usuario (nome, email, senha_hash, perfil, empresa, cargo) "
            "VALUES (?, ?, ?, 'EMPRESARIO', ?, ?)",
            (e.nome, e.email.strip().lower(), e.senha_hash, e.empresa, e.cargo))
        self.conexao.commit()
        e.id = cursor.lastrowid
        return e.id


# ------------------------------------------------------ avaliacao_mercado
SQL_AVALIACAO = """
SELECT a.*, u.empresa
FROM avaliacao_mercado a
JOIN usuario u ON u.id = a.usuario_id
"""


class AvaliacaoRepositorio:
    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def listar_por_oferta(self, oferta_id: int) -> list[AvaliacaoMercado]:
        linhas = self.conexao.execute(SQL_AVALIACAO + " WHERE a.oferta_curso_id = ? ORDER BY a.data DESC",
                                      (oferta_id,)).fetchall()
        return [_avaliacao(l) for l in linhas]

    def listar_por_status(self, status: StatusAvaliacao) -> list[AvaliacaoMercado]:
        linhas = self.conexao.execute(SQL_AVALIACAO + " WHERE a.status = ? ORDER BY a.data",
                                      (status.value,)).fetchall()
        return [_avaliacao(l) for l in linhas]

    def buscar(self, id_: int) -> AvaliacaoMercado | None:
        linha = self.conexao.execute(SQL_AVALIACAO + " WHERE a.id = ?", (id_,)).fetchone()
        return _avaliacao(linha) if linha else None

    def buscar_do_usuario(self, usuario_id: int, oferta_id: int) -> AvaliacaoMercado | None:
        """Usado para a RN03 (uma avaliação por empresário por oferta)."""
        linha = self.conexao.execute(SQL_AVALIACAO + " WHERE a.usuario_id = ? AND a.oferta_curso_id = ?",
                                     (usuario_id, oferta_id)).fetchone()
        return _avaliacao(linha) if linha else None

    def inserir(self, a: AvaliacaoMercado) -> int:
        cursor = self.conexao.execute(
            "INSERT INTO avaliacao_mercado (usuario_id, oferta_curso_id, nota_empregabilidade, "
            "nota_preparo, nota_soft_skills, comentario) VALUES (?, ?, ?, ?, ?, ?)",
            (a.usuario_id, a.oferta_curso_id, a.nota_empregabilidade, a.nota_preparo,
             a.nota_soft_skills, a.comentario))
        self.conexao.commit()
        a.id = cursor.lastrowid
        return a.id

    def atualizar(self, a: AvaliacaoMercado) -> None:
        """RN03: reavaliar atualiza a avaliação e ela volta para PENDENTE."""
        self.conexao.execute(
            "UPDATE avaliacao_mercado SET nota_empregabilidade = ?, nota_preparo = ?, "
            "nota_soft_skills = ?, comentario = ?, data = CURRENT_TIMESTAMP, status = 'PENDENTE' "
            "WHERE id = ?",
            (a.nota_empregabilidade, a.nota_preparo, a.nota_soft_skills, a.comentario, a.id))
        self.conexao.commit()

    def alterar_status(self, a: AvaliacaoMercado) -> None:
        self.conexao.execute("UPDATE avaliacao_mercado SET status = ? WHERE id = ?",
                             (a.status.value, a.id))
        self.conexao.commit()
