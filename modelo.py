"""Colunas Raw na ordem exata dos CSVs; nenhuma coluna é descartada."""

RAW = {
    "viagem": "id_viagem num_proposta situacao viagem_urgente justificativa_urgencia cod_orgao_superior nome_orgao_superior cod_orgao_solicitante nome_orgao_solicitante cpf_viajante nome_viajante cargo funcao descricao_funcao data_inicio data_fim destinos motivo valor_diarias valor_passagens valor_devolucao valor_outros_gastos".split(),
    "pagamento": "id_viagem num_proposta cod_orgao_superior nome_orgao_superior cod_orgao_pagador nome_orgao_pagador cod_ug_pagadora nome_ug_pagadora tipo_pagamento valor".split(),
    "passagem": "id_viagem num_proposta meio_transporte pais_origem_ida uf_origem_ida cidade_origem_ida pais_destino_ida uf_destino_ida cidade_destino_ida pais_origem_volta uf_origem_volta cidade_origem_volta pais_destino_volta uf_destino_volta cidade_destino_volta valor_passagem taxa_servico data_emissao hora_emissao".split(),
    "trecho": "id_viagem num_proposta sequencia_trecho origem_data origem_pais origem_uf origem_cidade destino_data destino_pais destino_uf destino_cidade meio_transporte numero_diarias missao".split(),
}
