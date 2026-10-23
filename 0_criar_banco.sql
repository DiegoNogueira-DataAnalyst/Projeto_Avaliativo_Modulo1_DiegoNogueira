-- Executar com psql conectado inicialmente ao database postgres.
-- Criação condicional; não apaga um database existente.
SELECT 'CREATE DATABASE "Projeto_Avaliativo_Modulo1_DiegoNogueira" ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'Projeto_Avaliativo_Modulo1_DiegoNogueira')\gexec
\connect Projeto_Avaliativo_Modulo1_DiegoNogueira

BEGIN;
CREATE TABLE IF NOT EXISTS raw_viagem (
 id_viagem VARCHAR, num_proposta VARCHAR, situacao VARCHAR, viagem_urgente VARCHAR,
 justificativa_urgencia VARCHAR, cod_orgao_superior VARCHAR, nome_orgao_superior VARCHAR,
 cod_orgao_solicitante VARCHAR, nome_orgao_solicitante VARCHAR, cpf_viajante VARCHAR,
 nome_viajante VARCHAR, cargo VARCHAR, funcao VARCHAR, descricao_funcao VARCHAR,
 data_inicio VARCHAR, data_fim VARCHAR, destinos VARCHAR, motivo VARCHAR,
 valor_diarias VARCHAR, valor_passagens VARCHAR, valor_devolucao VARCHAR, valor_outros_gastos VARCHAR
);
CREATE TABLE IF NOT EXISTS raw_pagamento (
 id_viagem VARCHAR, num_proposta VARCHAR, cod_orgao_superior VARCHAR,
 nome_orgao_superior VARCHAR, cod_orgao_pagador VARCHAR, nome_orgao_pagador VARCHAR,
 cod_ug_pagadora VARCHAR, nome_ug_pagadora VARCHAR, tipo_pagamento VARCHAR, valor VARCHAR
);
CREATE TABLE IF NOT EXISTS raw_passagem (
 id_viagem VARCHAR, num_proposta VARCHAR, meio_transporte VARCHAR,
 pais_origem_ida VARCHAR, uf_origem_ida VARCHAR, cidade_origem_ida VARCHAR,
 pais_destino_ida VARCHAR, uf_destino_ida VARCHAR, cidade_destino_ida VARCHAR,
 pais_origem_volta VARCHAR, uf_origem_volta VARCHAR, cidade_origem_volta VARCHAR,
 pais_destino_volta VARCHAR, uf_destino_volta VARCHAR, cidade_destino_volta VARCHAR,
 valor_passagem VARCHAR, taxa_servico VARCHAR, data_emissao VARCHAR, hora_emissao VARCHAR
);
CREATE TABLE IF NOT EXISTS raw_trecho (
 id_viagem VARCHAR, num_proposta VARCHAR, sequencia_trecho VARCHAR,
 origem_data VARCHAR, origem_pais VARCHAR, origem_uf VARCHAR, origem_cidade VARCHAR,
 destino_data VARCHAR, destino_pais VARCHAR, destino_uf VARCHAR, destino_cidade VARCHAR,
 meio_transporte VARCHAR, numero_diarias VARCHAR, missao VARCHAR
);
CREATE TABLE IF NOT EXISTS silver_viagem (
 id_viagem VARCHAR(20) PRIMARY KEY NOT NULL,
 num_proposta VARCHAR(20), situacao VARCHAR(50), viagem_urgente VARCHAR(5),
 cod_orgao_superior VARCHAR(20), nome_orgao_superior VARCHAR(255) NOT NULL,
 nome_viajante VARCHAR(255), cargo VARCHAR(255), data_inicio DATE, data_fim DATE,
 destinos VARCHAR(4000), motivo VARCHAR(4000),
 valor_diarias DECIMAL(10,2) CONSTRAINT ck_viagem_diarias CHECK (valor_diarias >= 0),
 valor_passagens DECIMAL(10,2), valor_devolucao DECIMAL(10,2), valor_outros_gastos DECIMAL(10,2),
 valor_total DECIMAL(12,2), duracao_dias INT
);
CREATE TABLE IF NOT EXISTS silver_pagamento (
 id_pagamento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 id_viagem VARCHAR(20) NOT NULL REFERENCES silver_viagem(id_viagem),
 num_proposta VARCHAR(20), nome_orgao_pagador VARCHAR(255), nome_ug_pagadora VARCHAR(255),
 tipo_pagamento VARCHAR(50) NOT NULL,
 valor DECIMAL(10,2) CONSTRAINT ck_pagamento_valor CHECK (valor >= 0)
);
CREATE TABLE IF NOT EXISTS silver_passagem (
 id_passagem INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 id_viagem VARCHAR(20) NOT NULL REFERENCES silver_viagem(id_viagem),
 meio_transporte VARCHAR(50), pais_origem_ida VARCHAR(60), uf_origem_ida VARCHAR(40),
 cidade_origem_ida VARCHAR(80), pais_destino_ida VARCHAR(60), uf_destino_ida VARCHAR(40),
 cidade_destino_ida VARCHAR(80),
 valor_passagem DECIMAL(10,2) CONSTRAINT ck_passagem_valor CHECK (valor_passagem >= 0),
 taxa_servico DECIMAL(10,2) CONSTRAINT ck_passagem_taxa CHECK (taxa_servico >= 0), data_emissao DATE
);
CREATE TABLE IF NOT EXISTS silver_trecho (
 id_trecho INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 id_viagem VARCHAR(20) NOT NULL REFERENCES silver_viagem(id_viagem), sequencia_trecho INT,
 origem_data DATE, origem_uf VARCHAR(40), origem_cidade VARCHAR(80),
 destino_data DATE, destino_uf VARCHAR(40), destino_cidade VARCHAR(80), meio_transporte VARCHAR(50),
 numero_diarias DECIMAL(10,2) CONSTRAINT ck_trecho_diarias CHECK (numero_diarias >= 0),
 CONSTRAINT uq_trecho_sequencia UNIQUE (id_viagem, sequencia_trecho)
);
CREATE INDEX IF NOT EXISTS ix_pagamento_viagem ON silver_pagamento(id_viagem);
CREATE INDEX IF NOT EXISTS ix_passagem_viagem ON silver_passagem(id_viagem);
COMMIT;
