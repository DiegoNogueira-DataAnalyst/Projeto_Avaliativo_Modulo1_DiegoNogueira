"""Executa o notebook na .venv atual; erros interrompem a entrega."""

from pathlib import Path
import nbformat
from nbclient import NotebookClient

raiz = Path(__file__).resolve().parents[1]
caminho = raiz / "3_analise.ipynb"
notebook = nbformat.read(caminho, as_version=4)
NotebookClient(
    notebook,
    timeout=1200,
    kernel_name="python3",
    resources={"metadata": {"path": str(raiz)}},
).execute()
nbformat.write(notebook, caminho)
print("Notebook executado com sucesso.")
