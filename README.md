
# scrap_sam_rework

Fork de modernização do SCRAP_SAM com foco em configuração e tooling atualizados (flake8/black/mypy/pytest) sem mudanças de comportamento em tempo de execução.

Atualizado: 2025-09-02 22:48

## Visão geral

- Compatibilidade: mesmas funcionalidades do projeto original, sem refatorações de lógica.
- Atualizações: padronização de `.flake8`, `pyproject.toml` (black/mypy), `mypy.ini`, e teste mínimo de import.
- Tipagem: redução de ruído com overrides de mypy; stubs de terceiros recomendados conforme necessário.

## Requisitos

- Python 3.13 (recomendado). Projetos secundários podem operar em 3.11+ com ajustes.
- pip >= 24, virtualenv/venv.
- Playwright para Python (browsers via `playwright install`).
- Node.js: somente se você usar ferramentas Node adicionais; o Playwright para Python não requer Node.

## Setup rápido

### macOS
- Instalar Xcode CLT e Homebrew.
- Instalar Python 3.13 (pyenv recomendado):
  - `brew install pyenv` e depois `pyenv install 3.13.7`
  - `pyenv local 3.13.7` (este repo rastreia `.python-version`).
- Criar venv: `python -m venv .venv && source .venv/bin/activate`
- Atualizar pip e instalar deps: `pip install -U pip && pip install -r requirements.txt`
- Playwright: `python -m playwright install` (e no Linux: `python -m playwright install --with-deps`).

### Debian/Ubuntu
- Dependências de build (se usar pyenv): `sudo apt-get update && sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev`
- Instalar pyenv (ou use Python do sistema 3.13 se disponível).
- Criar venv: `python3 -m venv .venv && source .venv/bin/activate`
- Instalar deps: `pip install -U pip && pip install -r requirements.txt`
- Playwright: `python -m playwright install --with-deps`

### Windows
- Instalar Python 3.13 (ou pyenv-win se preferir). Com pyenv-win: `pyenv install 3.13.7` e `pyenv local 3.13.7`.
- Criar venv: `py -3.13 -m venv .venv` e ativar: `\.venv\Scripts\activate`.
- Instalar deps: `python -m pip install -U pip && pip install -r requirements.txt`
- Playwright: `python -m playwright install`

Notas:
- Ambiente único e compartilhado no repositório: use SEMPRE o venv na raiz em `.venv/` (não crie `env/` ou `venv/` paralelos).
- Reaproveite os arquivos já existentes no repo: `.python-version` (pyenv) e `.envrc` (direnv) estão versionados e devem ser mantidos como fonte de verdade.
- A pasta do venv (`.venv/`) não é versionada; apenas os arquivos de configuração ficam no Git.

## Como rodar

- Dashboard_SM: `python backups/Dashboard_SM.py`
- Report_from_excel: `python backups/Report_from_excel.py`
- src.dashboard.Dashboard_SM: `python -m src.dashboard.Dashboard_SM`
- src.dashboard.Report_from_excel: `python -m src.dashboard.Report_from_excel`
- src.scrapers.scrap_sam_main: `python -m src.scrapers.scrap_sam_main`

- Teste rápido: `pytest -q`.
- Lints: `flake8` e `black --check .`; tipos: `mypy`.

## Diferenças em relação ao SCRAP_SAM (original)

Arquivos (rework vs original): adicionados=2110, removidos=117, modificados=8, comuns=61

Prévia (50 itens máx por seção). Listas completas: `reports/diff_files.txt`.

### Adicionados (rework):
- .env.example
- .envrc
- .flake8
- .mypy_cache/.gitignore
- .mypy_cache/3.13/@plugins_snapshot.json
- .mypy_cache/3.13/__future__.data.json
- .mypy_cache/3.13/__future__.meta.json
- .mypy_cache/3.13/__main__.data.json
- .mypy_cache/3.13/__main__.meta.json
- .mypy_cache/3.13/_ast.data.json
- .mypy_cache/3.13/_ast.meta.json
- .mypy_cache/3.13/_asyncio.data.json
- .mypy_cache/3.13/_asyncio.meta.json
- .mypy_cache/3.13/_bisect.data.json
- .mypy_cache/3.13/_bisect.meta.json
- .mypy_cache/3.13/_blake2.data.json
- .mypy_cache/3.13/_blake2.meta.json
- .mypy_cache/3.13/_bz2.data.json
- .mypy_cache/3.13/_bz2.meta.json
- .mypy_cache/3.13/_codecs.data.json
- .mypy_cache/3.13/_codecs.meta.json
- .mypy_cache/3.13/_collections_abc.data.json
- .mypy_cache/3.13/_collections_abc.meta.json
- .mypy_cache/3.13/_compression.data.json
- .mypy_cache/3.13/_compression.meta.json
- .mypy_cache/3.13/_contextvars.data.json
- .mypy_cache/3.13/_contextvars.meta.json
- .mypy_cache/3.13/_csv.data.json
- .mypy_cache/3.13/_csv.meta.json
- .mypy_cache/3.13/_ctypes.data.json
- .mypy_cache/3.13/_ctypes.meta.json
- .mypy_cache/3.13/_decimal.data.json
- .mypy_cache/3.13/_decimal.meta.json
- .mypy_cache/3.13/_frozen_importlib.data.json
- .mypy_cache/3.13/_frozen_importlib.meta.json
- .mypy_cache/3.13/_frozen_importlib_external.data.json
- .mypy_cache/3.13/_frozen_importlib_external.meta.json
- .mypy_cache/3.13/_hashlib.data.json
- .mypy_cache/3.13/_hashlib.meta.json
- .mypy_cache/3.13/_imp.data.json
- .mypy_cache/3.13/_imp.meta.json
- .mypy_cache/3.13/_io.data.json
- .mypy_cache/3.13/_io.meta.json
- .mypy_cache/3.13/_locale.data.json
- .mypy_cache/3.13/_locale.meta.json
- .mypy_cache/3.13/_markupbase.data.json
- .mypy_cache/3.13/_markupbase.meta.json
- .mypy_cache/3.13/_multibytecodec.data.json
- .mypy_cache/3.13/_multibytecodec.meta.json
- .mypy_cache/3.13/_operator.data.json

### Removidos (presentes no original, ausentes no rework):
- Acha_botao.py
- DashboardSM/Class/dashboard_activity.log
- DashboardSM/Class/main.py
- DashboardSM/Class/requirements.txt
- DashboardSM/Class/run.py
- DashboardSM/Class/src/__init__.py
- DashboardSM/Class/src/dashboard/__init__.py
- DashboardSM/Class/src/dashboard/kpi_calculator.py
- DashboardSM/Class/src/dashboard/ssa_dashboard - Copia (2).py
- DashboardSM/Class/src/dashboard/ssa_dashboard - Copia (3).py
- DashboardSM/Class/src/dashboard/ssa_dashboard - Copia.py
- DashboardSM/Class/src/dashboard/ssa_dashboard.py
- DashboardSM/Class/src/dashboard/ssa_visualizer - Copia.py
- DashboardSM/Class/src/dashboard/ssa_visualizer.py
- DashboardSM/Class/src/dashboard/tempCodeRunnerFile.py
- DashboardSM/Class/src/data/__init__.py
- DashboardSM/Class/src/data/data_loader.py
- DashboardSM/Class/src/data/ssa_columns.py
- DashboardSM/Class/src/data/ssa_data.py
- DashboardSM/Class/src/utils/__init__.py
- DashboardSM/Class/src/utils/data_validator.py
- DashboardSM/Class/src/utils/date_utils.py
- DashboardSM/Class/src/utils/file_manager.py
- DashboardSM/Class/src/utils/log_manager.py
- DashboardSM/Dashboard.zip
- DashboardSM/Dashboard_SM.py
- DashboardSM/Downloads/SSAs Pendentes Geral - 02-12-2024_1114AM.xlsx
- DashboardSM/Report_from_excel.py
- DashboardSM/Scrap-Playwright_otimizado_tratamento_de_erro_rede.py
- DashboardSM/dashboard_activity.log
- DashboardSM/error_report.json
- DashboardSM/execution_log_20241105_075106.log
- DashboardSM/execution_log_20241105_153649.log
- DashboardSM/execution_log_20241114_162115.log
- DashboardSM/relatorio_ssas.xlsx
- DashboardSM/ssa_analysis.log
- DashboardSM/tempCodeRunnerFile.py
- config/config.yaml
- config/settings.py
- dashboard.log
- dashboard_activity.log
- docs/BEST_PRACTICES.md
- docs/CODE_SANITY.md
- docs/CONFIGURACAO.md
- docs/DESENVOLVIMENTO.md
- docs/LOG_INSTRUCOES_REWORK.md
- docs/REWORK_TODO.md
- execution_log_20241111_090145.log
- execution_log_20241118_144913.log
- execution_log_20241119_162707.log

### Modificados (presentes em ambos, conteúdo diferente):
- .gitignore
- .pytest_cache/v/cache/nodeids
- README.md
- requirements.txt
- src/dashboard/Dashboard_SM.py
- src/scrapers/Scrap-Playwright_otimizado_tratamento_de_erro_rede.py
- src/scrapers/__init__.py
- src/utils/scrap_installer.py

## Maturidade e qualidade

- Maturidade: arquivos .py=42, testes=1, LOC~32476, funs=1015, anotadas~1015 (~100%).
- Sanity recente (black/flake8/mypy/pytest):
[OK] black --version ->
python -m black, 25.1.0 (compiled: yes)
[OK] flake8 --version ->
[OK] mypy --version ->
mypy 1.17.1 (compiled: yes)
[OK] pytest --version ->
pytest 8.4.1
black --check:
flake8:
mypy --show-config:
usage: mypy [-h] [-v] [-V] [more options; see below]
mypy: error: unrecognized arguments: --show-config
mypy:
src/dashboard/Report_from_excel.py:20: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
pytest -q:

Presença de tooling/config:
- `.flake8`, `pyproject.toml` (black+mypy), `mypy.ini`, `tests/test_sanity_imports.py`, `log_instrucoes.md` adicionados no rework.
- `.python-version` e `.envrc` versionados para ambiente consistente.

## Troubleshooting

- Playwright no Debian/Ubuntu: use `python -m playwright install --with-deps` para instalar navegadores e dependências do sistema.
- Certificados/SSL no macOS: se `pip` falhar, rode `Install Certificates.command` (vem com o Python.org) ou atualize o Keychain.
- Erro de display no Linux: use `xvfb-run -s "-screen 0 1280x720x24" python -m ...` se não houver display.
- Navegadores headless: confira que o binário foi instalado (`~/.cache/ms-playwright/`). Apague a pasta de cache se corrompida e reinstale.
- Permissões de arquivos: evite clonar dentro de pastas sincronizadas com permissão restrita (ex.: alguns diretórios corporativos) para não afetar playwright/chromium.
- Windows PowerShell: ative o venv com `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` se houver bloqueio de scripts.

## Matriz de versões (recomendadas)

- Python: 3.13.7 (recomendado); 3.11+ provável compatível.
- black: 25.x
- flake8: 7.x
- mypy: 1.17.x
- pytest: 8.x
- pandas: 2.3.x
- selenium: 4.3x.x (no rework: 4.35.0 observado)
- dash: 3.x (no rework)
- plotly: 6.x (no rework)

Notas:
- As versões acima refletem o alvo do rework e o que já foi observado no ambiente. Ajuste conforme o lock/constraints da sua equipe.
- Para tipagem, considere `pandas-stubs`, `types-requests`, `types-PyYAML`, `types-psutil`.

## Node (opcional)

Se você utilizar ferramentas Node neste repo:
- Instale Node LTS (nvm, asdf, ou instalador). Mantenha `node_modules/` fora do versionamento.
- Os arquivos `package.json`/lockfiles permanecem versionados. Rode `npm ci` (ou `pnpm i --frozen-lockfile`) quando aplicável.

## Convenções

- Ambientes: mantenha apenas UM venv em `.venv/` na raiz. Não duplique ambientes.
-- Configs: `.python-version` e `.envrc` são a base; ajustes específicos de SO podem ser documentados no `log_instrucoes.md`.

