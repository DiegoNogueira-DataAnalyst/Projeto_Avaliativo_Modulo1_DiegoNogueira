-- Agregações independentes: não juntar duas relações 1:N na mesma soma.
CREATE OR REPLACE VIEW vw_gold_metricas AS
SELECT 'tipo_pagamento'::text AS metrica,
       p.tipo_pagamento::text AS dimensao,
       COUNT(*)::bigint AS quantidade,
       SUM(p.valor)::numeric AS valor_total,
       AVG(p.valor)::numeric AS valor_medio
FROM silver_viagem v
JOIN silver_pagamento p ON p.id_viagem = v.id_viagem
GROUP BY p.tipo_pagamento
UNION ALL
SELECT 'orgao_pagador', COALESCE(p.nome_orgao_pagador, 'Não informado'),
       COUNT(*), SUM(p.valor), AVG(p.valor)
FROM silver_viagem v
JOIN silver_pagamento p ON p.id_viagem = v.id_viagem
GROUP BY COALESCE(p.nome_orgao_pagador, 'Não informado')
UNION ALL
SELECT 'meio_transporte', COALESCE(t.meio_transporte, 'Não informado'),
       COUNT(*), NULL::numeric, NULL::numeric
FROM silver_viagem v
JOIN silver_trecho t ON t.id_viagem = v.id_viagem
GROUP BY COALESCE(t.meio_transporte, 'Não informado')
UNION ALL
SELECT 'uf_destino', COALESCE(t.destino_uf, 'Não informado'),
       COUNT(*), NULL::numeric, NULL::numeric
FROM silver_viagem v
JOIN silver_trecho t ON t.id_viagem = v.id_viagem
GROUP BY COALESCE(t.destino_uf, 'Não informado');

CREATE TABLE IF NOT EXISTS gold_metricas (
    metrica TEXT NOT NULL,
    dimensao TEXT NOT NULL,
    quantidade BIGINT NOT NULL,
    valor_total NUMERIC,
    valor_medio NUMERIC,
    PRIMARY KEY (metrica, dimensao)
);
TRUNCATE gold_metricas;
INSERT INTO gold_metricas SELECT * FROM vw_gold_metricas;
