"""
controllers.py — O participante "AvaliacaoController" do DIAGRAMA DE
SEQUÊNCIA do UC07 (Fase 2, seção 2c), mais a moderação (UC11).

Leia o método avaliar() de cima para baixo junto com o diagrama:
cada bloco comentado é uma mensagem (ou um fragmento alt) dele.
"""
from __future__ import annotations

import sqlite3

from models import Administrador, AvaliacaoMercado, Empresario, StatusAvaliacao, Usuario
from repositorios import AvaliacaoRepositorio, OfertaRepositorio


class RegraNegocioErro(Exception):
    """Erro de regra de negócio, com mensagem pronta para mostrar na tela."""


class AvaliacaoController:
    def __init__(self, conexao: sqlite3.Connection):
        self.avaliacoes = AvaliacaoRepositorio(conexao)
        self.ofertas = OfertaRepositorio(conexao)

    def avaliar(self, usuario: Usuario | None, oferta_id: int, notas: tuple, comentario: str | None) -> str:
        # 1. verificarLogin()  — alt: não logado -> UC06 (a rota redireciona ao login)
        if usuario is None:
            raise RegraNegocioErro("Faça login para avaliar.")
        # RN05: só empresário avalia
        if not isinstance(usuario, Empresario):
            raise RegraNegocioErro("Somente empresários podem avaliar ofertas.")

        oferta = self.ofertas.buscar(oferta_id)
        if oferta is None:
            raise RegraNegocioErro("Oferta de curso não encontrada.")

        # 2. validarNotas()  — alt: nota inválida -> mensagem de erro (RN02)
        try:
            notas = tuple(int(n) for n in notas)
        except (TypeError, ValueError):
            raise RegraNegocioErro("As notas devem ser números inteiros de 1 a 5.")
        if len(notas) != 3 or any(n < 1 or n > 5 for n in notas):
            raise RegraNegocioErro("As notas devem ser números inteiros de 1 a 5.")
        comentario = (comentario or "").strip()[:1000] or None

        # 3. buscarAvaliacao(empresario, oferta)  (RN03)
        existente = self.avaliacoes.buscar_do_usuario(usuario.id, oferta_id)

        nova = usuario.avaliar(oferta, notas, comentario)   # status = PENDENTE (RN04)
        if existente:
            # alt [já avaliou] -> UPDATE avaliacao_mercado
            nova.id = existente.id
            self.avaliacoes.atualizar(nova)
            return "Sua avaliação foi atualizada e voltou para moderação."
        # alt [primeira vez] -> INSERT avaliacao_mercado
        self.avaliacoes.inserir(nova)
        # 5. confirmação na tela
        return "Avaliação enviada para moderação."

    # ---------------------------------------------------- UC11 – Moderar
    def moderar(self, usuario: Usuario | None, avaliacao_id: int, aprovar: bool) -> AvaliacaoMercado:
        if not isinstance(usuario, Administrador):
            raise RegraNegocioErro("Somente administradores podem moderar.")
        avaliacao = self.avaliacoes.buscar(avaliacao_id)
        if avaliacao is None:
            raise RegraNegocioErro("Avaliação não encontrada.")
        if aprovar:
            usuario.aprovar(avaliacao)
        else:
            usuario.rejeitar(avaliacao)
        self.avaliacoes.alterar_status(avaliacao)
        return avaliacao

    def pendentes(self) -> list[AvaliacaoMercado]:
        return self.avaliacoes.listar_por_status(StatusAvaliacao.PENDENTE)
