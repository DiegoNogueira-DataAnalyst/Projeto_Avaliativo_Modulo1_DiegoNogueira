"""Organiza o ZIP recebido, preservando seu conteúdo original."""

from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
origem = raiz / "viagens_2025_6meses.zip"
destino = raiz / "data" / origem.name
destino.parent.mkdir(exist_ok=True)
if origem.exists() and not destino.exists():
    origem.rename(destino)
