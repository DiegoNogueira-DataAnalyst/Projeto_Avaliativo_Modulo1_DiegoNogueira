"""Configuração central; credenciais são lidas somente do .env local."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
ZIP_PATH = DATA_DIR / "viagens_2025_6meses.zip"
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID", "1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "10000"))


def parametros_banco(database=None):
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=database
        or os.getenv("DB_NAME", "Projeto_Avaliativo_Modulo1_DiegoNogueira"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        connect_timeout=10,
    )
