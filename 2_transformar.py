"""Raw → Silver: conversões estritas e rejeições auditáveis, sem truncar textos."""

import csv
import logging
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation

from psycopg import sql

from banco import conectar, inserir_em_lote
from config import ROOT


def converter_decimal(texto):
    valor = texto.strip()
    if not valor:
        return None
    try:
        numero = Decimal(valor.replace(".", "").replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError("decimal inválido") from erro
    if not numero.is_finite() or numero != numero.quantize(Decimal(".01")):
        raise ValueError("decimal fora da precisão")
    return numero


def converter_data(texto):
    return (
        datetime.strptime(texto.strip(), "%d/%m/%Y").date() if texto.strip() else None
    )


def executar():
    pasta = ROOT / "data" / "quality"
    pasta.mkdir(parents=True, exist_ok=True)
    resumo = Counter()
    try:
        with (
            conectar() as conexao,
            (pasta / "rejeicoes.csv").open(
                "w", encoding="utf-8", newline=""
            ) as arquivo,
        ):
            rejeicoes = csv.writer(arquivo)
            rejeicoes.writerow(["tabela", "linha_raw", "id_viagem", "motivo"])
            # Não usa CASCADE: dependências Gold não são removidas silenciosamente.
            conexao.execute(
                "TRUNCATE silver_pagamento, silver_passagem, silver_trecho, silver_viagem RESTART IDENTITY"
            )
            ids = set()
            for tabela in ("viagem", "pagamento", "passagem", "trecho"):
                campos = conexao.execute(
                    "SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND is_identity='NO' ORDER BY ordinal_position",
                    (f"silver_{tabela}",),
                ).fetchall()
                nomes = [c[0] for c in campos]
                vistos = set()
                lote = []
                with conexao.cursor(name=f"leitura_{tabela}") as leitor:
                    leitor.execute(
                        sql.SQL("SELECT * FROM {} ORDER BY ctid").format(
                            sql.Identifier(f"raw_{tabela}")
                        )
                    )
                    colunas = [c.name for c in leitor.description]
                    for numero, linha in enumerate(leitor, 1):
                        origem = dict(zip(colunas, linha))
                        try:
                            registro = {}
                            for nome, tipo, limite, nulo in campos:
                                if nome in ("valor_total", "duracao_dias"):
                                    continue
                                texto = origem[nome]
                                if tipo == "numeric":
                                    valor = converter_decimal(texto)
                                    if valor is not None and abs(valor) >= Decimal(
                                        "100000000"
                                    ):
                                        raise ValueError(
                                            f"{nome}: excede DECIMAL(10,2)"
                                        )
                                elif tipo == "date":
                                    valor = converter_data(texto)
                                elif tipo == "integer":
                                    valor = (
                                        int(texto.strip()) if texto.strip() else None
                                    )
                                else:
                                    valor = texto.strip() or None
                                    if limite and valor and len(valor) > limite:
                                        raise ValueError(
                                            f"{nome}: excede {limite} caracteres"
                                        )
                                if valor is None and nulo == "NO":
                                    raise ValueError(f"{nome}: obrigatório")
                                registro[nome] = valor
                            id_viagem = registro["id_viagem"]
                            if tabela != "viagem" and id_viagem not in ids:
                                raise ValueError("viagem ausente na Silver")
                            nao_negativos = {
                                "viagem": ["valor_diarias"],
                                "pagamento": ["valor"],
                                "passagem": ["valor_passagem", "taxa_servico"],
                                "trecho": ["numero_diarias"],
                            }[tabela]
                            if any(
                                registro[c] is not None and registro[c] < 0
                                for c in nao_negativos
                            ):
                                raise ValueError(
                                    "valor negativo incompatível com CHECK"
                                )
                            if tabela == "viagem":
                                valores = [
                                    registro[c]
                                    for c in (
                                        "valor_diarias",
                                        "valor_passagens",
                                        "valor_devolucao",
                                        "valor_outros_gastos",
                                    )
                                ]
                                registro["valor_total"] = (
                                    valores[0] + valores[1] - valores[2] + valores[3]
                                    if all(v is not None for v in valores)
                                    else None
                                )
                                inicio, fim = (
                                    registro["data_inicio"],
                                    registro["data_fim"],
                                )
                                if inicio and fim and fim < inicio:
                                    raise ValueError("data final anterior à inicial")
                                registro["duracao_dias"] = (
                                    (fim - inicio).days + 1 if inicio and fim else None
                                )
                                chave = id_viagem
                            elif tabela == "trecho":
                                if registro["sequencia_trecho"] is None:
                                    raise ValueError("sequência de trecho ausente")
                                chave = (id_viagem, registro["sequencia_trecho"])
                            else:
                                chave = tuple(valor.strip() for valor in linha)
                            if chave in vistos:
                                raise ValueError(
                                    "chave duplicada; preservada primeira ocorrência na ordem Raw"
                                )
                            lote.append([registro[n] for n in nomes])
                            if len(lote) >= 10000:
                                inserir_em_lote(
                                    conexao, f"silver_{tabela}", lote, colunas=nomes
                                )
                                lote.clear()
                            vistos.add(chave)
                            if tabela == "viagem":
                                ids.add(id_viagem)
                            resumo[f"{tabela}_aceitos"] += 1
                        except (ValueError, InvalidOperation) as erro:
                            resumo[f"{tabela}_rejeitados"] += 1
                            rejeicoes.writerow(
                                [tabela, numero, origem.get("id_viagem"), str(erro)]
                            )
                if lote:
                    inserir_em_lote(conexao, f"silver_{tabela}", lote, colunas=nomes)
                logging.info(
                    "%s: %s aceitos, %s rejeitados",
                    tabela,
                    resumo[f"{tabela}_aceitos"],
                    resumo[f"{tabela}_rejeitados"],
                )
        import json

        (pasta / "resumo.json").write_text(
            json.dumps(
                {"regra_deduplicacao": "linha_csv_completa", **resumo}, indent=2
            ),
            encoding="utf-8",
        )
        logging.info("Transformação concluída: %s", dict(resumo))
    except Exception:
        logging.exception("Falha na transformação; carga Silver revertida.")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executar()
