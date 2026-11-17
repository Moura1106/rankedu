-- =====================================================================
-- RankEdu - Dados de exemplo (funciona no MySQL e no SQLite)
-- ATENÇÃO: instituições e notas são FICTÍCIAS, apenas para demonstração.
-- Para a versão final, usar dados abertos do INEP (CPC/ENADE).
-- Senha de todos os usuários de teste: senha123
-- =====================================================================

INSERT INTO instituicao (id, nome, sigla, tipo, cidade, uf, site) VALUES
(1, 'Universidade Federal do Planalto',          'UFPL',  'PUBLICA', 'Brasília',            'DF', NULL),
(2, 'Universidade Estadual do Vale',             'UEV',   'PUBLICA', 'São José dos Campos', 'SP', NULL),
(3, 'Centro Universitário Horizonte',            'UNIHZ', 'PRIVADA', 'São Paulo',           'SP', NULL),
(4, 'Faculdade Atlântica Digital',               'FAD',   'PRIVADA', 'Rio de Janeiro',      'RJ', NULL),
(5, 'Universidade Pampa Integrada',              'UPI',   'PRIVADA', 'Porto Alegre',        'RS', NULL);

INSERT INTO curso (id, nome, area, pitch_texto, pitch_video_url) VALUES
(1, 'Ciência da Computação', 'Tecnologia',
 'Você vai aprender a resolver problemas com algoritmos, criar sistemas e entender como os computadores funcionam por dentro. Mercado aquecido em desenvolvimento, dados e inteligência artificial.',
 NULL),
(2, 'Administração', 'Negócios',
 'Forma profissionais para planejar, organizar e liderar empresas. Estuda finanças, marketing, pessoas e estratégia, com atuação em praticamente qualquer setor.',
 NULL),
(3, 'Enfermagem', 'Saúde',
 'Prepara para cuidar de pessoas em hospitais, postos de saúde e domicílios, unindo conhecimento científico, técnica e empatia. Alta demanda em todo o país.',
 NULL);

-- (id, instituição, curso, modalidade, ENADE, CPC, mensalidade)
INSERT INTO oferta_curso (id, instituicao_id, curso_id, modalidade, conceito_enade, cpc, mensalidade) VALUES
(1,  1, 1, 'PRESENCIAL', 5,    5,       0.00),
(2,  2, 1, 'PRESENCIAL', 4,    4,       0.00),
(3,  3, 1, 'PRESENCIAL', 4,    4,    1890.00),
(4,  4, 1, 'EAD',        3,    3,     389.90),
(5,  5, 1, 'PRESENCIAL', 3,    NULL, 1450.00),   -- sem CPC: usa ENADE (RN06)
(6,  1, 2, 'PRESENCIAL', 4,    4,       0.00),
(7,  3, 2, 'PRESENCIAL', 4,    3,    1290.00),
(8,  4, 2, 'EAD',        NULL, NULL,  299.90),   -- sem nota oficial (RN06)
(9,  2, 3, 'PRESENCIAL', 5,    4,       0.00),
(10, 5, 3, 'PRESENCIAL', 4,    4,    1690.00);

INSERT INTO usuario (id, nome, email, senha_hash, perfil, empresa, cargo) VALUES
(1, 'Marina Alves',  'admin@rankedu.com',
 'pbkdf2_sha256$100000$1f2c3aaedd08e39b$bd24943c99f26f32978817efee02e9ef3cac4d6fc71e6bb283243f1e482b77f1',
 'ADMIN', NULL, NULL),
(2, 'Carlos Souza',  'carlos@techbr.com',
 'pbkdf2_sha256$100000$1f2c3aaedd08e39b$bd24943c99f26f32978817efee02e9ef3cac4d6fc71e6bb283243f1e482b77f1',
 'EMPRESARIO', 'TechBR Soluções', 'Gerente de RH'),
(3, 'Juliana Lima',  'juliana@hospitalvida.com',
 'pbkdf2_sha256$100000$1f2c3aaedd08e39b$bd24943c99f26f32978817efee02e9ef3cac4d6fc71e6bb283243f1e482b77f1',
 'EMPRESARIO', 'Hospital Vida', 'Coordenadora de Enfermagem'),
(4, 'Rafael Costa',  'rafael@finconsult.com',
 'pbkdf2_sha256$100000$1f2c3aaedd08e39b$bd24943c99f26f32978817efee02e9ef3cac4d6fc71e6bb283243f1e482b77f1',
 'EMPRESARIO', 'FinConsult', 'Diretor de Operações');

INSERT INTO avaliacao_mercado
  (id, usuario_id, oferta_curso_id, nota_empregabilidade, nota_preparo, nota_soft_skills, comentario, data, status) VALUES
(1, 2, 3,  5, 5, 4, 'Os formados chegam muito bem preparados em programação.',   '2026-03-10 10:00:00', 'APROVADA'),
(2, 2, 1,  4, 5, 3, 'Base teórica excelente; poderiam ter mais vivência prática.', '2026-03-11 14:30:00', 'APROVADA'),
(3, 2, 4,  3, 3, 4, 'Bons em autonomia, mas com lacunas técnicas.',               '2026-03-12 09:15:00', 'APROVADA'),
(4, 4, 3,  4, 4, 5, 'Ótima comunicação e trabalho em equipe.',                    '2026-03-15 16:00:00', 'APROVADA'),
(5, 4, 7,  5, 4, 5, 'Profissionais com visão de negócio e liderança.',            '2026-03-16 11:20:00', 'APROVADA'),
(6, 3, 9,  5, 5, 5, 'Referência em formação prática na área hospitalar.',        '2026-03-18 08:45:00', 'APROVADA'),
(7, 3, 10, 4, 4, 4, 'Bons estágios supervisionados.',                             '2026-03-20 13:00:00', 'PENDENTE'),
(8, 4, 6,  3, 4, 3, 'Bom conteúdo, pouca conexão com o mercado.',                 '2026-03-21 10:10:00', 'APROVADA'),
(9, 2, 2,  2, 3, 2, 'Comentário fora das regras da plataforma.',                  '2026-03-22 17:40:00', 'REJEITADA');
