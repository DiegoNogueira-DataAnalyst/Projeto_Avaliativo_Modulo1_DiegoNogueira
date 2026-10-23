"""Gera a estrutura do notebook; resultados só surgem após execução real."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
celulas = []


def markdown(texto):
    celulas.append(
        {"cell_type": "markdown", "metadata": {}, "source": texto.splitlines(True)}
    )


def codigo(texto):
    celulas.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": texto.splitlines(True),
        }
    )


markdown("""# Viagens a serviço — análise dos gastos públicos

**Autor:** Diego Nogueira | **Fonte:** recorte de seis meses de 2025 fornecido pelo professor.

Este notebook executa a etapa Gold após `0_criar_banco.py`, `1_extrair.py` e
`2_transformar.py`. As saídas são calculadas no PostgreSQL; não há resultados simulados.

## Definições de negócio

- Custo líquido da viagem = diárias + passagens + outros gastos − devoluções.
- Duração inclui a data inicial e a final: `(data_fim - data_inicio) + 1`.
  O indicador representa o período informado e deve ser lido junto à situação da viagem.
- Órgão responsável pela viagem usa `nome_orgao_superior`; órgão pagador usa
  `nome_orgao_pagador`. São perguntas e universos financeiros diferentes.
- Destino usa a combinação completa de localidades em `destinos`: uma viagem
  multidestino é um itinerário, e seu custo não é atribuído integralmente a cada cidade.
- Valores ausentes permanecem nulos: somas e médias SQL os ignoram. Rejeições são
  auditadas em `data/quality/`. As conclusões se restringem aos dados aceitos na Silver.
- Duplicatas de pagamentos/passagens são identificadas pela linha completa do CSV,
  incluindo campos não projetados na Silver. Eventos legítimos inteiramente idênticos
  permanecem indistinguíveis sem identificador próprio fornecido pela fonte.
""")
codigo("""from pathlib import Path
import json
import sys
import pandas as pd
import matplotlib
matplotlib.use('module://matplotlib_inline.backend_inline')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
from IPython.display import display, Markdown
from sqlalchemy import create_engine, URL, text

ROOT = Path.cwd()
if not (ROOT / 'config.py').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
from config import parametros_banco
from banco import conectar

p = parametros_banco()
engine = create_engine(URL.create('postgresql+psycopg', username=p['user'],
    password=p['password'], host=p['host'], port=p['port'], database=p['dbname']))
plt.style.use('seaborn-v0_8-whitegrid')
pd.options.display.max_colwidth = None
pd.options.display.float_format = lambda valor: f'{valor:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')

def consultar(sql):
    with engine.connect() as conexao:
        return pd.read_sql_query(text(sql), conexao)

def grafico(df, categoria, valor, titulo, eixo, arquivo):
    if df.empty:
        raise ValueError('Consulta sem dados: ' + titulo)
    dados = df.copy()
    marcadores = dados[categoria].astype(str).str.strip().str.casefold().isin({'inválido', 'não informado', 'sigiloso'})
    cores = ['#9A9A9A' if marcador else '#176B87' for marcador in marcadores]
    dados[categoria] = dados[categoria].astype(str).map(lambda s: s if len(s) <= 100 else s[:97] + '...').str.wrap(45)
    fig, ax = plt.subplots(figsize=(12, max(4, len(dados) * .65)))
    ax.barh(range(len(dados)), dados[valor].astype(float), color=cores, height=.45 if len(dados) == 1 else .7)
    ax.set_yticks(range(len(dados)), dados[categoria])
    ax.invert_yaxis()
    if len(dados) == 1:
        ax.set_ylim(1, -1)
    rotulos = {'nome_orgao_superior': 'Órgão superior', 'destinos': 'Itinerário',
        'id_viagem': 'Identificador da viagem', 'tipo_pagamento': 'Tipo de pagamento',
        'meio_transporte': 'Meio de transporte', 'uf_destino': 'UF de destino'}
    ax.set(title=titulo, xlabel=eixo, ylabel=rotulos.get(categoria, categoria))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:,.0f}'.replace(',', '.')))
    legenda = [Patch(color='#176B87', label='Categorias informadas' if marcadores.any() else eixo)]
    if marcadores.any():
        legenda.append(Patch(color='#9A9A9A', label='Marcador de informação não identificada'))
    fig.legend(handles=legenda, loc='lower center', frameon=False, bbox_to_anchor=(.5, 0))
    fig.tight_layout(rect=(0, .08, 1, 1))
    pasta = ROOT / 'reports' / 'figures'
    pasta.mkdir(parents=True, exist_ok=True)
    fig.savefig(pasta / arquivo, dpi=150, bbox_inches='tight')
    plt.show()

resultados = {}
""")
markdown(
    "## Qualidade e cobertura da análise\nA contagem permite confrontar Raw, Silver e registros rejeitados. Nenhum dado pessoal de viajante é exibido nas saídas."
)
codigo("""contagens = []
for camada in ('raw', 'silver'):
    for tabela in ('viagem', 'pagamento', 'passagem', 'trecho'):
        nome = f'{camada}_{tabela}'
        qtd = int(consultar(f'SELECT COUNT(*) AS n FROM {nome}').iloc[0]['n'])
        contagens.append({'tabela': nome, 'linhas': qtd})
display(pd.DataFrame(contagens))
resumo = ROOT / 'data' / 'quality' / 'resumo.json'
if resumo.exists():
    display(pd.DataFrame([json.loads(resumo.read_text(encoding='utf-8'))]))
display(consultar('SELECT MIN(data_inicio) AS inicio, MAX(data_fim) AS fim, COUNT(*) FILTER (WHERE valor_total IS NULL) AS custos_ausentes FROM silver_viagem'))
""")
perguntas = [
    (
        "1. Quais são os cinco órgãos com maior custo total?",
        """SELECT nome_orgao_superior, COUNT(*) AS viagens, SUM(valor_total) AS custo_total
FROM silver_viagem GROUP BY nome_orgao_superior
ORDER BY custo_total DESC NULLS LAST, nome_orgao_superior LIMIT 5""",
        "nome_orgao_superior",
        "custo_total",
        "Top 5 órgãos por custo líquido",
        "Custo líquido (R$)",
    ),
    (
        "2. Quais são os três destinos com maior custo médio por viagem?",
        """SELECT destinos, COUNT(*) AS viagens, AVG(valor_total) AS custo_medio
FROM silver_viagem WHERE destinos IS NOT NULL AND valor_total IS NOT NULL
GROUP BY destinos ORDER BY custo_medio DESC, destinos LIMIT 3""",
        "destinos",
        "custo_medio",
        "Top 3 itinerários por custo médio",
        "Custo médio por viagem (R$)",
    ),
    (
        "3. Qual é a viagem de maior duração e seu custo total?",
        """SELECT id_viagem, nome_orgao_superior, situacao, data_inicio, data_fim, duracao_dias, valor_total
FROM silver_viagem WHERE duracao_dias IS NOT NULL
ORDER BY duracao_dias DESC, id_viagem LIMIT 1""",
        "id_viagem",
        "duracao_dias",
        "Maior duração registrada na base",
        "Duração inclusiva (dias)",
    ),
]
for i, (titulo, sql, categoria, valor, graf, eixo) in enumerate(perguntas, 1):
    markdown(
        "## "
        + titulo
        + "\n\n```sql\n"
        + sql
        + "\n```\n\nEmpates são ordenados pela dimensão/identificador para resultados reprodutíveis."
    )
    codigo(
        f"df = consultar({sql!r})\ndisplay(df)\nresultados['p{i}'] = df\ngrafico(df, {categoria!r}, {valor!r}, {graf!r}, {eixo!r}, 'p{i}.png')\ndisplay(Markdown('**Evidência:** ' + df.to_string(index=False)))\n"
    )
markdown("""## Construção da camada Gold: tabela e VIEW

A VIEW calcula quatro agregações com `JOIN` e `GROUP BY`. A tabela persiste a mesma
fotografia. Cada fato é agregado separadamente, evitando o produto entre pagamentos
e trechos de uma mesma viagem. A tabela deve ser atualizada após nova transformação;
a VIEW reflete imediatamente a Silver.""")
codigo("""ddl = (ROOT / 'sql' / '3_gold.sql').read_text(encoding='utf-8')
display(Markdown('```sql\\n' + ddl + '\\n```'))
with conectar() as conexao:
    conexao.execute(ddl)
display(consultar('SELECT * FROM gold_metricas ORDER BY metrica, quantidade DESC LIMIT 15'))
divergencias = consultar("SELECT COUNT(*) AS n FROM ((SELECT * FROM gold_metricas EXCEPT SELECT * FROM vw_gold_metricas) UNION ALL (SELECT * FROM vw_gold_metricas EXCEPT SELECT * FROM gold_metricas)) d")
assert int(divergencias.iloc[0]['n']) == 0, 'Tabela Gold divergente da VIEW'
""")
gold = [
    (
        "4. Qual é o tipo de pagamento com maior valor médio?",
        "SELECT dimensao AS tipo_pagamento, quantidade, valor_medio FROM gold_metricas WHERE metrica='tipo_pagamento' ORDER BY valor_medio DESC NULLS LAST, dimensao",
        "tipo_pagamento",
        "valor_medio",
        "Valor médio por tipo de pagamento",
        "Valor médio (R$)",
    ),
    (
        "5. Qual é o meio de transporte mais usado nos trechos?",
        "SELECT dimensao AS meio_transporte, quantidade FROM gold_metricas WHERE metrica='meio_transporte' ORDER BY quantidade DESC, dimensao",
        "meio_transporte",
        "quantidade",
        "Meios de transporte nos trechos",
        "Número de trechos",
    ),
    (
        "6. Qual UF de destino aparece em mais trechos?",
        "SELECT dimensao AS uf_destino, quantidade FROM gold_metricas WHERE metrica='uf_destino' ORDER BY quantidade DESC, dimensao",
        "uf_destino",
        "quantidade",
        "Top 10 UFs de destino nos trechos",
        "Número de trechos",
    ),
    (
        "7. Qual órgão pagou mais no total?",
        "SELECT dimensao AS orgao_pagador, quantidade AS pagamentos, valor_total FROM gold_metricas WHERE metrica='orgao_pagador' ORDER BY valor_total DESC NULLS LAST, dimensao LIMIT 10",
        "orgao_pagador",
        "valor_total",
        None,
        None,
    ),
]
for i, (titulo, sql, categoria, valor, graf, eixo) in enumerate(gold, 4):
    markdown(
        "## "
        + titulo
        + "\n\n```sql\n"
        + sql
        + "\n```\n\nA tabela ordena os rótulos publicados na fonte. Marcadores de sigilo ou de classificação ausente são interpretados separadamente na síntese."
    )
    fonte = f"df = consultar({sql!r})\ndisplay(df)\nresultados['p{i}'] = df\ndisplay(Markdown('**Liderança observada:** ' + df.head(1).to_string(index=False)))\n"
    if graf:
        fonte += f"grafico(df.head(10), {categoria!r}, {valor!r}, {graf!r}, {eixo!r}, 'p{i}.png')\n"
    codigo(fonte)
    if i == 7:
        markdown(
            "**Limite de identificação:** `Sigiloso` é um rótulo de divulgação, e não o nome de um órgão. O total dessa categoria não permite identificar um pagador único. A síntese também apresenta o maior órgão cujo nome foi divulgado."
        )
markdown("""## Interpretação e limites

O ranking de custos indica concentração dos gastos, não irregularidade. O ranking
de custo médio deve ser lido junto à quantidade de viagens: um itinerário com uma
única observação não representa um padrão estável. A viagem mais longa merece
verificação de contexto, sem presumir erro. Contagem de trechos mede movimentação,
não pessoas distintas. Pagamentos e custo líquido da viagem têm conceitos diferentes
e não devem ser somados entre si.

Antes da entrega, conferir rejeições e a cobertura temporal; a interpretação vale
somente para o recorte fornecido e os registros aceitos. Uma evolução seria medir
custo por diária e por órgão, controlar viagens internacionais e adicionar séries mensais.
""")
codigo("""saida = ROOT / 'reports' / 'resultados.json'
saida.parent.mkdir(parents=True, exist_ok=True)
saida.write_text(json.dumps({k: json.loads(v.to_json(orient='records', date_format='iso', force_ascii=False)) for k, v in resultados.items()}, ensure_ascii=False, indent=2), encoding='utf-8')
engine.dispose()
""")
markdown(
    "## Síntese dos resultados\nIndicadores calculados a partir das consultas anteriores, com ressalvas de interpretação."
)
codigo("""def reais(valor):
    if pd.isna(valor):
        return 'Não informado'
    return f'R$ {float(valor):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')

total_viagens = float(consultar('SELECT SUM(valor_total) AS total FROM silver_viagem').iloc[0]['total'])
total_pago = float(consultar('SELECT SUM(valor) AS total FROM silver_pagamento').iloc[0]['total'])
total_trechos = int(consultar('SELECT COUNT(*) AS total FROM silver_trecho').iloc[0]['total'])
p1, p2, p3, p4, p5, p6, p7 = [resultados[f'p{i}'] for i in range(1, 8)]
nao_identificados = {'sigiloso', 'não informado', 'inválido'}
nomeados = p7[~p7['orgao_pagador'].str.strip().str.casefold().isin(nao_identificados)]
primeiro = p7.iloc[0]
if primeiro['orgao_pagador'].strip().casefold() in nao_identificados:
    texto_pagador = f"O maior agrupamento por rótulo é {primeiro['orgao_pagador']}, com {reais(primeiro['valor_total'])} ({float(primeiro['valor_total']) / total_pago:.1%} dos pagamentos aceitos). Esse rótulo não identifica um órgão único."
else:
    texto_pagador = f"O órgão pagador {primeiro['orgao_pagador']} lidera com {reais(primeiro['valor_total'])}."
if not nomeados.empty:
    identificado = nomeados.iloc[0]
    texto_pagador += f" Entre os órgãos com nome divulgado, {identificado['orgao_pagador']} lidera com {reais(identificado['valor_total'])}."
situacao = p3.iloc[0]['situacao']
qualidade = consultar("SELECT metrica, dimensao, quantidade, valor_total FROM gold_metricas WHERE lower(dimensao) IN ('inválido', 'não informado', 'sigiloso') ORDER BY metrica, dimensao")
linhas = [
    f"Os cinco órgãos líderes concentram {float(p1['custo_total'].sum()) / total_viagens:.1%} do custo líquido conhecido. {p1.iloc[0]['nome_orgao_superior']} lidera com {reais(p1.iloc[0]['custo_total'])}. Isso mede concentração, sem demonstrar irregularidade.",
    f"O itinerário com maior média registra {reais(p2.iloc[0]['custo_medio'])}. Quantidade de viagens nesse itinerário: {int(p2.iloc[0]['viagens'])}. Médias com poucas observações devem ser interpretadas com cautela; não se estima um padrão populacional a partir desse ranking.",
    f"A viagem {p3.iloc[0]['id_viagem']} apresenta período informado de {int(p3.iloc[0]['duracao_dias'])} dias inclusivos e custo líquido registrado de {reais(p3.iloc[0]['valor_total'])}. Situação: {situacao if pd.notna(situacao) else 'não informada'}. O valor zero registrado e o período informado não comprovam, isoladamente, despesa efetiva nula ou deslocamento contínuo durante todo o intervalo.",
    f"O tipo {p4.iloc[0]['tipo_pagamento']} tem o maior valor médio: {reais(p4.iloc[0]['valor_medio'])}. A média é por registro de pagamento, não por viagem.",
    f"O meio {p5.iloc[0]['meio_transporte']} representa {int(p5.iloc[0]['quantidade']) / total_trechos:.1%} dos trechos aceitos. Isso mede segmentos de deslocamento, não pessoas distintas.",
    f"A UF de destino {p6.iloc[0]['uf_destino']} aparece em {int(p6.iloc[0]['quantidade'])} trechos ({int(p6.iloc[0]['quantidade']) / total_trechos:.1%} do total). O ranking indica concentração operacional de destinos.",
    texto_pagador,
    'A fonte contém marcadores de classificação ausente ou inválida em campos textuais. Eles são preservados para rastreabilidade, mas não representam modalidades de transporte, UFs ou órgãos identificáveis. Sua frequência está discriminada na tabela de qualidade. Custo líquido da viagem e total de pagamentos são perspectivas diferentes e não devem ser somados entre si.'
]
sintese = '\\n\\n'.join(linhas)
display(Markdown(sintese))
display(qualidade)
(ROOT / 'reports' / 'insights.md').write_text(sintese, encoding='utf-8')
(ROOT / 'reports' / 'qualidade_categorias.json').write_text(qualidade.to_json(orient='records', force_ascii=False, indent=2), encoding='utf-8')
engine.dispose()
""")
notebook = {
    "cells": celulas,
    "metadata": {
        "kernelspec": {
            "display_name": "Python (.venv)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.14"},
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}
(ROOT / "3_analise.ipynb").write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8"
)
