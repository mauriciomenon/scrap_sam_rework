# Arquitetura do Pipeline: Excel → Dash

Data: 2025-09-03
Autor: GitHub Copilot

## Visão geral
Fluxo end-to-end do dado, do Excel até os gráficos no navegador:

1) Arquivo Excel (downloads/SSAs Pendentes Geral - *.xlsx)
   - Origem dos dados.
   - Cabeçalho na 2ª linha (header=1).

2) Carregamento (DataLoader)
   - Arquivo: `src/dashboard/Class/src/data/data_loader.py`
   - Classe: `DataLoader`
   - Responsabilidades:
     - Ler planilha com `pandas.read_excel(..., header=1)`.
     - Converter datas: coluna `Emitida Em` → `datetime64[ns]` (dayfirst=True, errors='coerce').
     - Normalizar strings obrigatórias e opcionais.
     - Normalizar semanas (`Semana de Cadastro`, `Semana Programada`) para strings de 6 dígitos; `000000` → `None` na programada.
     - Validar qualidade; converter linhas em `SSAData` via `_convert_to_objects()`.

3) Estruturas (SSAData, SSAColumns)
   - Arquivos:
     - `src/dashboard/Class/src/data/ssa_data.py`
     - `src/dashboard/Class/src/data/ssa_columns.py`
   - `SSAColumns`: enum de índices das colunas esperadas (acesso posicional).
   - `SSAData`: dataclass com campos principais; `emitida_em: Optional[datetime]`.

4) Validação adicional (SSADataValidator)
   - Arquivo: `src/dashboard/Class/src/utils/data_validator.py`
   - Checagens de consistência, integridade e estatísticas (responsáveis, campos obrigatórios, etc.).

5) Visualização (SSADashboard + SSAVisualizer)
   - Arquivos:
     - `src/dashboard/Class/src/dashboard/ssa_dashboard.py`
     - `src/dashboard/Class/src/dashboard/ssa_visualizer.py`
   - `SSADashboard`: cria app Dash, layout e callbacks; integra DataFrame.
   - `SSAVisualizer`: funções de criação de gráficos (prioridade, setor, semanas, tempo no estado).
   - Harden:
     - Montagem de gráficos lida com conjuntos vazios e tipagens mistas.
     - Evita ambiguidade booleana de arrays numpy.
     - Geração de figuras “vazias” show-friendly quando necessário.

6) Execução do servidor
   - `SSADashboard.run_server(port=...)` (Dash 3.x) com fallback a `run_server` legado.
   - Servidor disponível em `http://127.0.0.1:<porta>`.

## Contratos e formatos
- Entrada:
  - Excel com colunas padronizadas; cabeçalho na segunda linha.
- Saída (intermediária):
  - `pandas.DataFrame` com:
    - `Emitida Em`: datetime64[ns]
    - `Semana de Cadastro`: string de 6 dígitos
    - `Semana Programada`: string de 6 dígitos ou `None`
    - Campos de texto sem `nan` literais e sem espaços excedentes
- Saída (final):
  - Gráficos plotly/dash renderizados no browser.

## Erros e tratamentos
- Datas inválidas: convertidas para `NaT` (coerce) e registradas.
- Weeks faltantes: convertidas para `000000` → `None` (programada), cadastro sempre 6 dígitos.
- Campos vazios obrigatórios: filtrados ou logados conforme o caso.
- Conjuntos vazios em gráficos: figura padrão “sem dados”.

## Arquivos-chave
- Data
  - `data_loader.py`, `ssa_data.py`, `ssa_columns.py`, `data_validator.py`
- Dash
  - `ssa_dashboard.py`, `ssa_visualizer.py`
- Utilitários
  - `utils/file_manager.py`, `utils/date_utils.py`

## Como rodar
- Por código (exemplo minimalista):
  - Localiza último Excel em `downloads/` via `FileManager.get_latest_file(...)`.
  - `df = DataLoader(path).load_data()`
  - `app = SSADashboard(df)`
  - `app.run_server(port=8091)`

## Observações
- Repositório preparado para múltiplas variantes (bkp/src/...); a principal roda com as classes em `src/dashboard/Class/src/...`.
- JS client-side para utilidades (copiar valores) está acoplado ao layout; reforços de robustez previstos.
