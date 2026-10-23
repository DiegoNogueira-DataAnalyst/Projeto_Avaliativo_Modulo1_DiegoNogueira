"""Cria o database e executa o DDL compartilhado com o script SQL."""

from psycopg import sql

from banco import conectar
from config import ROOT, parametros_banco


def executar():
    nome = parametros_banco()["dbname"]
    with conectar("postgres") as conexao:
        conexao.autocommit = True
        if not conexao.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", (nome,)
        ).fetchone():
            conexao.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nome)))
    fonte = (ROOT / "0_criar_banco.sql").read_text(encoding="utf-8")
    ddl = fonte.split("BEGIN;", 1)[1].rsplit("COMMIT;", 1)[0]
    with conectar() as conexao:
        conexao.execute(ddl)


if __name__ == "__main__":
    executar()
