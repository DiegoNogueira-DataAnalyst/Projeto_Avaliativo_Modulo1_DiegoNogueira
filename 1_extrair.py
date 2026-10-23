"""Baixa o ZIP e carrega os quatro CSVs sem alterar seus valores."""

import csv
import hashlib
import json
import logging
import shutil
import argparse
from itertools import islice
from zipfile import ZipFile

import gdown

from banco import conectar, inserir_em_lote
from config import CHUNK_SIZE, DATA_DIR, DRIVE_FILE_ID, ZIP_PATH
from modelo import RAW


def executar(local=False):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporario = ZIP_PATH.with_suffix(".download")
    try:
        if not local:
            gdown.download(id=DRIVE_FILE_ID, output=str(temporario), quiet=False)
        elif not ZIP_PATH.exists():
            raise FileNotFoundError("ZIP local ausente em data/")
        with ZipFile(ZIP_PATH if local else temporario) as arquivo:
            if arquivo.testzip():
                raise ValueError("ZIP corrompido")
            for tabela in RAW:
                nome = f"2025_{tabela.capitalize()}.csv"
                with (
                    arquivo.open(nome) as origem,
                    (DATA_DIR / nome).open("wb") as destino,
                ):
                    shutil.copyfileobj(origem, destino)
        if not local:
            temporario.replace(ZIP_PATH)
        with ZIP_PATH.open("rb") as origem:
            digest = hashlib.file_digest(origem, "sha256").hexdigest()
        manifesto = {"sha256": digest, "arquivos": {}}
        with conectar() as conexao:
            # Uma transação preserva a carga anterior se qualquer CSV falhar.
            conexao.execute(
                "TRUNCATE raw_viagem, raw_pagamento, raw_passagem, raw_trecho"
            )
            for tabela, colunas in RAW.items():
                nome = f"2025_{tabela.capitalize()}.csv"
                with (DATA_DIR / nome).open(encoding="latin-1", newline="") as origem:
                    leitor = csv.reader(origem, delimiter=";")
                    cabecalho = next(leitor)
                    if len(cabecalho) != len(colunas):
                        raise ValueError(f"Layout inesperado: {nome}")
                    quantidade = 0
                    while bloco := list(islice((r for r in leitor if r), CHUNK_SIZE)):
                        if any(len(r) != len(colunas) for r in bloco):
                            raise ValueError(
                                f"Linha com número incorreto de campos: {nome}"
                            )
                        inserir_em_lote(conexao, f"raw_{tabela}", bloco)
                        quantidade += len(bloco)
                    manifesto["arquivos"][nome] = {
                        "cabecalho": cabecalho,
                        "linhas": quantidade,
                    }
                    logging.info("%s: %s linhas", nome, quantidade)
        (DATA_DIR / "manifesto.json").write_text(
            json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        logging.exception("Extração falhou; a transação de carga foi revertida.")
        raise
    finally:
        temporario.unlink(missing_ok=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Reprocessa o ZIP já baixado, sem acesso à rede",
    )
    executar(local=parser.parse_args().local)
