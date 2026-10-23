"""Utilitários transacionais para PostgreSQL."""

import psycopg
from psycopg import sql

from config import parametros_banco


def conectar(database=None):
    return psycopg.connect(**parametros_banco(database))


def executar(comando, parametros=None):
    with conectar() as conexao:
        return conexao.execute(comando, parametros).rowcount


def inserir_em_lote(conexao, tabela, linhas, colunas=None):
    comando = sql.SQL("COPY {} FROM STDIN").format(sql.Identifier(tabela))
    if colunas:
        comando = sql.SQL("COPY {} ({}) FROM STDIN").format(
            sql.Identifier(tabela), sql.SQL(",").join(map(sql.Identifier, colunas))
        )
    with conexao.cursor().copy(comando) as copia:
        for linha in linhas:
            copia.write_row(linha)
