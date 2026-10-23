"""Valida dados reais: reconciliação, integridade e ausência de inflação na Gold."""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz))
from banco import conectar

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--silver",
    action="store_true",
    help="Valida até a Silver, antes da construção Gold",
)
args = parser.parse_args()
manifesto = json.loads((raiz / "data" / "manifesto.json").read_text(encoding="utf-8"))
resumo = json.loads(
    (raiz / "data" / "quality" / "resumo.json").read_text(encoding="utf-8")
)
assert resumo["regra_deduplicacao"] == "linha_csv_completa"
motivos = Counter()
rejeitados_por_tabela = Counter()
with (raiz / "data" / "quality" / "rejeicoes.csv").open(
    encoding="utf-8", newline=""
) as arquivo:
    for linha in csv.DictReader(arquivo):
        motivos[(linha["tabela"], linha["motivo"])] += 1
        rejeitados_por_tabela[linha["tabela"]] += 1
verificacoes = {}
with conectar() as conexao:
    for tabela in ("viagem", "pagamento", "passagem", "trecho"):
        raw = conexao.execute(f"SELECT COUNT(*) FROM raw_{tabela}").fetchone()[0]
        silver = conexao.execute(f"SELECT COUNT(*) FROM silver_{tabela}").fetchone()[0]
        assert raw == manifesto["arquivos"][f"2025_{tabela.capitalize()}.csv"]["linhas"]
        assert raw == silver + resumo.get(f"{tabela}_rejeitados", 0)
        assert silver == resumo[f"{tabela}_aceitos"]
        assert raw - silver == rejeitados_por_tabela[tabela]
        verificacoes[tabela] = {
            "raw": raw,
            "silver": silver,
            "rejeitados": raw - silver,
        }
        if tabela != "viagem":
            assert (
                conexao.execute(
                    f"SELECT COUNT(*) FROM silver_{tabela} f LEFT JOIN silver_viagem v USING(id_viagem) WHERE v.id_viagem IS NULL"
                ).fetchone()[0]
                == 0
            )
    assert (
        conexao.execute(
            "SELECT COUNT(*) FROM silver_viagem WHERE valor_total IS DISTINCT FROM valor_diarias + valor_passagens - valor_devolucao + valor_outros_gastos OR duracao_dias IS DISTINCT FROM (data_fim-data_inicio+1)"
        ).fetchone()[0]
        == 0
    )
    assert (
        conexao.execute(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' AND table_name LIKE 'raw_%' AND data_type <> 'character varying'"
        ).fetchone()[0]
        == 0
    )
    assert (
        conexao.execute(
            "SELECT COUNT(*) FROM pg_constraint WHERE conrelid IN ('raw_viagem'::regclass,'raw_pagamento'::regclass,'raw_passagem'::regclass,'raw_trecho'::regclass)"
        ).fetchone()[0]
        == 0
    )
    for tabela in ("viagem", "pagamento", "passagem", "trecho"):
        assert (
            conexao.execute(
                "SELECT COUNT(*) FROM pg_constraint WHERE conrelid=%s::regclass AND contype=%s",
                (f"silver_{tabela}", "p"),
            ).fetchone()[0]
            == 1
        )
        if tabela != "viagem":
            assert (
                conexao.execute(
                    "SELECT COUNT(*) FROM pg_constraint WHERE conrelid=%s::regclass AND contype=%s",
                    (f"silver_{tabela}", "f"),
                ).fetchone()[0]
                == 1
            )
    assert (
        conexao.execute(
            "SELECT COUNT(*) FROM pg_constraint WHERE conrelid IN ('silver_viagem'::regclass,'silver_pagamento'::regclass,'silver_passagem'::regclass,'silver_trecho'::regclass) AND contype='c'"
        ).fetchone()[0]
        == 5
    )
    assert (
        conexao.execute(
            "SELECT COUNT(*) FROM pg_constraint WHERE conrelid='silver_trecho'::regclass AND contype='u'"
        ).fetchone()[0]
        == 1
    )
    assert (
        conexao.execute(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' AND is_nullable='NO' AND ((table_name='silver_viagem' AND column_name='nome_orgao_superior') OR (table_name='silver_pagamento' AND column_name='tipo_pagamento'))"
        ).fetchone()[0]
        == 2
    )
    if not args.silver:
        assert (
            conexao.execute(
                "SELECT SUM(valor_total) FROM gold_metricas WHERE metrica='orgao_pagador'"
            ).fetchone()[0]
            == conexao.execute("SELECT SUM(valor) FROM silver_pagamento").fetchone()[0]
        )
        assert (
            conexao.execute(
                "SELECT SUM(quantidade) FROM gold_metricas WHERE metrica='meio_transporte'"
            ).fetchone()[0]
            == conexao.execute("SELECT COUNT(*) FROM silver_trecho").fetchone()[0]
        )
        assert (
            conexao.execute(
                "SELECT COUNT(*) FROM ((SELECT * FROM gold_metricas EXCEPT SELECT * FROM vw_gold_metricas) UNION ALL (SELECT * FROM vw_gold_metricas EXCEPT SELECT * FROM gold_metricas)) d"
            ).fetchone()[0]
            == 0
        )
saida = (
    raiz / "reports" / ("validacao_silver.json" if args.silver else "validacao.json")
)
saida.parent.mkdir(exist_ok=True)
saida.write_text(
    json.dumps(
        {
            "status": "aprovado",
            "etapa": "silver" if args.silver else "pipeline_completo",
            "contagens": verificacoes,
            "rejeicoes_por_motivo": [
                {"tabela": tabela, "motivo": motivo, "quantidade": quantidade}
                for (tabela, motivo), quantidade in sorted(motivos.items())
            ],
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("Validações de integração aprovadas:", verificacoes)
