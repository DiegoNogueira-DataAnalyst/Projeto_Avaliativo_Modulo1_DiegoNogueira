# Guia de continuidade do projeto

Este guia orienta a manutenção do pipeline sem perder rastreabilidade dos dados
e do histórico de desenvolvimento. A instalação e as regras de negócio estão no README.

Instale as ferramentas de revisão com `python -m pip install -r requirements-dev.txt`.

## Desenvolvimento por etapa

Comece a partir da `develop` atualizada e crie uma branch com o nome da funcionalidade:

```powershell
git switch develop
git pull --ff-only origin develop
git switch -c feature/nome-da-funcionalidade
```

Implemente uma alteração com propósito definido. Preserve os nomes numerados dos
entregáveis e registre mudanças nas regras de transformação e análise no README.
O código Raw deve manter os valores da fonte; ajustes pertencem à Silver.

## Verificação e commits

Execute as verificações correspondentes à etapa alterada:

```powershell
python -m ruff check .
python -m unittest discover -s tests -v
python scripts/validar_pipeline.py
```

A última verificação requer o pipeline completo já executado, incluindo a Gold.
Na fase 2, use `python scripts/validar_pipeline.py --silver` para validar Raw e Silver
antes de construir a Gold.
Alterações de extração também devem ser verificadas com
`python scripts/validar_idempotencia.py`, que reprocessa a Raw do ambiente configurado.
Confira o `DB_NAME` local antes de executar cargas: Raw e Silver são substituídas
transacionalmente em cada reexecução, conforme o edital.

Revise `git diff` e adicione explicitamente os arquivos da alteração. Use commits
pequenos, em português e no imperativo, com prefixos como `feat:`, `fix:`, `docs:`
e `chore:`. As mensagens devem explicar a finalidade da mudança.

```powershell
git status --short
git diff
git add arquivo_alterado.py
git commit -m "fix: corrige conversao de valores monetarios"
git push -u origin feature/nome-da-funcionalidade
```

Mantenha `.env`, `.venv/`, ZIPs e CSVs fora do versionamento. Compartilhe resultados
agregados e evidências de validação em `reports/`, sem copiar dados pessoais da Raw.

## Integração e release

Integre a feature validada à `develop` com merge que preserve o histórico. A descrição
da integração deve registrar o problema, a alteração, a execução de validação e o
impacto nos dados. Use pull requests quando a conexão do GitHub permitir; o merge
pelo Git também preserva o fluxo e suas evidências.

```powershell
git switch develop
git merge --no-ff feature/nome-da-funcionalidade
git push origin develop
git switch -c release/X.Y.Z
```

Após conferir a versão candidata, promova a release para `main` e crie a tag:

```powershell
git switch main
git merge --no-ff release/X.Y.Z
git tag -a vX.Y.Z -m "Descreve a etapa validada"
git push origin main develop release/X.Y.Z vX.Y.Z
git switch develop
git merge --no-ff release/X.Y.Z
```

Correções posteriores são novos commits e novas versões. Preserve o histórico já
publicado. Depois da submissão acadêmica, aguarde a avaliação antes de modificar
o repositório, pois o edital considera a data da última atualização.
