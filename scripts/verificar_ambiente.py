"""Verifica conexão e tabelas existentes sem exibir credenciais."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from banco import conectar
from config import parametros_banco

with conectar('postgres') as conexao:
    nome = parametros_banco()['dbname']
    existe = conexao.execute('SELECT datname FROM pg_database WHERE datname=%s', (nome,)).fetchone()
    print('Banco configurado:', nome, '| existente:', bool(existe))
if existe:
    with conectar() as conexao:
        print('Tabelas existentes:', conexao.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall())
