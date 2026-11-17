-- =====================================================================
-- RankEdu - Modelo Físico para SQLite 3
-- Mesma estrutura do schema_mysql.sql, adaptada aos tipos do SQLite.
-- =====================================================================

PRAGMA foreign_keys = ON;   -- no SQLite as FKs vêm desligadas por padrão

CREATE TABLE instituicao (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  nome    VARCHAR(150) NOT NULL,
  sigla   VARCHAR(20),
  tipo    VARCHAR(10)  NOT NULL CHECK (tipo IN ('PUBLICA', 'PRIVADA')),
  cidade  VARCHAR(100) NOT NULL,
  uf      CHAR(2)      NOT NULL,
  site    VARCHAR(200)
);

CREATE TABLE curso (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  nome             VARCHAR(150) NOT NULL UNIQUE,
  area             VARCHAR(100) NOT NULL,
  pitch_texto      TEXT         NOT NULL,
  pitch_video_url  VARCHAR(300)
);

CREATE TABLE oferta_curso (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  instituicao_id  INTEGER       NOT NULL REFERENCES instituicao (id) ON DELETE RESTRICT,
  curso_id        INTEGER       NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
  modalidade      VARCHAR(12)   NOT NULL CHECK (modalidade IN ('PRESENCIAL', 'EAD', 'HIBRIDO')),
  conceito_enade  INTEGER       CHECK (conceito_enade BETWEEN 1 AND 5),
  cpc             INTEGER       CHECK (cpc BETWEEN 1 AND 5),
  mensalidade     NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (mensalidade >= 0),
  UNIQUE (instituicao_id, curso_id, modalidade)
);

CREATE TABLE usuario (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  nome        VARCHAR(150) NOT NULL,
  email       VARCHAR(150) NOT NULL UNIQUE,
  senha_hash  VARCHAR(255) NOT NULL,
  perfil      VARCHAR(10)  NOT NULL CHECK (perfil IN ('EMPRESARIO', 'ADMIN')),
  empresa     VARCHAR(150),
  cargo       VARCHAR(100),
  CHECK (perfil = 'ADMIN' OR (empresa IS NOT NULL AND cargo IS NOT NULL))
);

CREATE TABLE avaliacao_mercado (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id            INTEGER  NOT NULL REFERENCES usuario (id) ON DELETE CASCADE,
  oferta_curso_id       INTEGER  NOT NULL REFERENCES oferta_curso (id) ON DELETE CASCADE,
  nota_empregabilidade  INTEGER  NOT NULL CHECK (nota_empregabilidade BETWEEN 1 AND 5),
  nota_preparo          INTEGER  NOT NULL CHECK (nota_preparo BETWEEN 1 AND 5),
  nota_soft_skills      INTEGER  NOT NULL CHECK (nota_soft_skills BETWEEN 1 AND 5),
  comentario            VARCHAR(1000),
  data                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status                VARCHAR(10) NOT NULL DEFAULT 'PENDENTE'
                        CHECK (status IN ('PENDENTE', 'APROVADA', 'REJEITADA')),
  UNIQUE (usuario_id, oferta_curso_id)
);

CREATE INDEX ix_oferta_curso_id ON oferta_curso (curso_id);

CREATE VIEW vw_ranking AS
SELECT
  o.id                                   AS oferta_id,
  c.id                                   AS curso_id,
  c.nome                                 AS curso,
  i.id                                   AS instituicao_id,
  i.nome                                 AS instituicao,
  i.sigla,
  i.tipo,
  i.uf,
  o.modalidade,
  o.mensalidade,
  COALESCE(o.cpc, o.conceito_enade)      AS nota_oficial,
  m.media_mercado,
  COALESCE(m.qtd_avaliacoes, 0)          AS qtd_avaliacoes,
  CASE
    WHEN COALESCE(o.cpc, o.conceito_enade) IS NULL THEN NULL
    WHEN m.media_mercado IS NULL THEN COALESCE(o.cpc, o.conceito_enade)
    ELSE 0.6 * COALESCE(o.cpc, o.conceito_enade) + 0.4 * m.media_mercado
  END                                    AS nota_final
FROM oferta_curso o
JOIN instituicao i ON i.id = o.instituicao_id
JOIN curso c       ON c.id = o.curso_id
LEFT JOIN (
  SELECT oferta_curso_id,
         AVG((nota_empregabilidade + nota_preparo + nota_soft_skills) / 3.0) AS media_mercado,
         COUNT(*) AS qtd_avaliacoes
  FROM avaliacao_mercado
  WHERE status = 'APROVADA'
  GROUP BY oferta_curso_id
) m ON m.oferta_curso_id = o.id;
