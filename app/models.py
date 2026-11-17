"""
models.py — As classes do DIAGRAMA DE CLASSES (Fase 2, seção 2b).

Cada classe, atributo e método abaixo tem o mesmo nome do diagrama
(convertido para o estilo do Python: notaFinal() -> nota_final()).
Os enums viram classes Enum; a herança Usuario -> Empresario/Administrador
vira herança de classes Python.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------- enums
class TipoInstituicao(str, Enum):
    PUBLICA = "PUBLICA"
    PRIVADA = "PRIVADA"


class Modalidade(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    EAD = "EAD"
    HIBRIDO = "HIBRIDO"

    @property
    def rotulo(self) -> str:
        """Texto para exibir na tela."""
        return {"PRESENCIAL": "Presencial", "EAD": "EAD", "HIBRIDO": "Híbrido"}[self.value]


class StatusAvaliacao(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADA = "APROVADA"
    REJEITADA = "REJEITADA"


# ---------------------------------------------------------- Instituicao
@dataclass
class Instituicao:
    id: int | None
    nome: str
    sigla: str | None
    tipo: TipoInstituicao
    cidade: str
    uf: str
    site: str | None = None

    def eh_publica(self) -> bool:
        return self.tipo == TipoInstituicao.PUBLICA


# ---------------------------------------------------------------- Curso
@dataclass
class Curso:
    id: int | None
    nome: str
    area: str
    pitch_texto: str
    pitch_video_url: str | None = None

    def tem_video(self) -> bool:
        return bool(self.pitch_video_url)


# ----------------------------------------------------- AvaliacaoMercado
@dataclass
class AvaliacaoMercado:
    id: int | None
    usuario_id: int
    oferta_curso_id: int
    nota_empregabilidade: int
    nota_preparo: int
    nota_soft_skills: int
    comentario: str | None = None
    data: str | None = None
    status: StatusAvaliacao = StatusAvaliacao.PENDENTE   # RN04
    autor_empresa: str | None = None                     # só para exibição

    def media(self) -> float:
        """RN02: a média de uma avaliação é a média das três notas."""
        return (self.nota_empregabilidade + self.nota_preparo + self.nota_soft_skills) / 3


# ---------------------------------------------------------- OfertaCurso
@dataclass
class OfertaCurso:
    id: int | None
    instituicao: Instituicao
    curso: Curso
    modalidade: Modalidade
    conceito_enade: int | None
    cpc: int | None
    mensalidade: float
    # Composição do diagrama: OfertaCurso 1 *-- 0..* AvaliacaoMercado
    avaliacoes: list[AvaliacaoMercado] = field(default_factory=list)

    def avaliacoes_aprovadas(self) -> list[AvaliacaoMercado]:
        """RN04: só avaliações aprovadas contam e aparecem publicamente."""
        return [a for a in self.avaliacoes if a.status == StatusAvaliacao.APROVADA]

    def nota_oficial(self) -> float | None:
        """RN06: CPC; se não houver, conceito ENADE; se não houver nenhum, None."""
        if self.cpc is not None:
            return float(self.cpc)
        if self.conceito_enade is not None:
            return float(self.conceito_enade)
        return None

    def media_mercado(self) -> float | None:
        """RN02: média das avaliações aprovadas (None se não houver)."""
        aprovadas = self.avaliacoes_aprovadas()
        if not aprovadas:
            return None
        return sum(a.media() for a in aprovadas) / len(aprovadas)

    def nota_final(self) -> float | None:
        """RN01 — a fórmula fica na classe Ranking, em um só lugar."""
        from ranking import Ranking
        return Ranking.calcular_nota_final(self.nota_oficial(), self.media_mercado())

    def mensalidade_formatada(self) -> str:
        """RN07: instituição pública mostra 'Gratuita'."""
        if self.instituicao.eh_publica():
            return "Gratuita"
        valor = f"{self.mensalidade:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor}"


# -------------------------------------------------- Usuario (abstrata)
ITERACOES_HASH = 100_000


def gerar_hash_senha(senha: str, salt: str | None = None) -> str:
    """Gera 'pbkdf2_sha256$iteracoes$salt$hash' (mesmo formato do seed.sql).
    A senha NUNCA é guardada em texto puro (RNF de segurança)."""
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), ITERACOES_HASH).hex()
    return f"pbkdf2_sha256${ITERACOES_HASH}${salt}${digest}"


@dataclass
class Usuario(ABC):
    id: int | None
    nome: str
    email: str
    senha_hash: str

    perfil = ""   # sobrescrito nas subclasses (coluna 'perfil' da tabela única)

    def autenticar(self, senha: str) -> bool:
        try:
            _, iteracoes, salt, esperado = self.senha_hash.split("$")
        except ValueError:
            return False
        calculado = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), int(iteracoes)).hex()
        return hmac.compare_digest(calculado, esperado)


@dataclass
class Empresario(Usuario):
    empresa: str = ""
    cargo: str = ""

    perfil = "EMPRESARIO"

    def avaliar(self, oferta: OfertaCurso, notas: tuple[int, int, int],
                comentario: str | None) -> AvaliacaoMercado:
        """Cria o objeto AvaliacaoMercado (status PENDENTE — RN04).
        Quem valida e grava é o AvaliacaoController (diagrama de sequência)."""
        emp, prep, soft = notas
        return AvaliacaoMercado(None, self.id, oferta.id, emp, prep, soft, comentario)


@dataclass
class Administrador(Usuario):
    perfil = "ADMIN"

    def aprovar(self, avaliacao: AvaliacaoMercado) -> None:
        avaliacao.status = StatusAvaliacao.APROVADA

    def rejeitar(self, avaliacao: AvaliacaoMercado) -> None:
        avaliacao.status = StatusAvaliacao.REJEITADA
