"""
ranking.py — A classe Ranking do diagrama de classes e o fluxo do
DIAGRAMA DE ATIVIDADES "Consultar ranking" (Fase 2, seção 2d).

Os pesos (RN01) ficam aqui, em UM só lugar: se o grupo decidir mudar
para 70/30, basta alterar as duas constantes.
"""
from __future__ import annotations

from models import OfertaCurso


class Ranking:
    PESO_OFICIAL = 0.6
    PESO_MERCADO = 0.4

    @classmethod
    def calcular_nota_final(cls, nota_oficial: float | None,
                            media_mercado: float | None) -> float | None:
        """RN01 + RN06:
        - sem nota oficial        -> None (vai para o fim do ranking)
        - sem avaliação aprovada  -> nota final = nota oficial
        - com as duas             -> 0,6 x oficial + 0,4 x mercado
        """
        if nota_oficial is None:
            return None
        if media_mercado is None:
            return nota_oficial
        return cls.PESO_OFICIAL * nota_oficial + cls.PESO_MERCADO * media_mercado

    @staticmethod
    def gerar(ofertas: list[OfertaCurso], tipo: str | None = None, uf: str | None = None,
              modalidade: str | None = None) -> list[OfertaCurso]:
        """Passos do diagrama de atividades:
        1. recebe as ofertas do curso escolhido;
        2. aplica os filtros que o visitante informou (RF02);
        3. calcula a nota final de cada uma (RF12);
        4. ordena da maior para a menor; sem nota oficial vai para o fim (RN06).
        """
        filtradas = [
            o for o in ofertas
            if (not tipo or o.instituicao.tipo.value == tipo)
            and (not uf or o.instituicao.uf == uf)
            and (not modalidade or o.modalidade.value == modalidade)
        ]

        def chave(o: OfertaCurso):
            nota = o.nota_final()
            # Tupla: primeiro quem TEM nota (False < True), depois a maior nota.
            return (nota is None, -(nota or 0), o.instituicao.nome)

        return sorted(filtradas, key=chave)
