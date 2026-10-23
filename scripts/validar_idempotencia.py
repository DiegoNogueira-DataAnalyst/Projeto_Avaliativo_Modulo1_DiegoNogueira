"""Reexecuta a Raw e compara contagens e fingerprint do conteúdo completo."""

import json
import subprocess
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz))
from banco import conectar


def fotografia():
    with conectar() as conexao:
        return {
            t: list(
                conexao.execute(
                    f"SELECT COUNT(*), SUM(hashtextextended(r::text, 0)::numeric)::text FROM raw_{t} r"
                ).fetchone()
            )
            for t in ("viagem", "pagamento", "passagem", "trecho")
        }


antes = fotografia()
subprocess.run(
    [sys.executable, str(raiz / "1_extrair.py"), "--local"], cwd=raiz, check=True
)
depois = fotografia()
assert antes == depois, "Reexecução alterou contagens ou conteúdo da Raw"
pasta = raiz / "reports"
pasta.mkdir(exist_ok=True)
(pasta / "idempotencia.json").write_text(
    json.dumps({"status": "aprovado", "antes": antes, "depois": depois}, indent=2),
    encoding="utf-8",
)
print("Idempotência Raw aprovada:", depois)
