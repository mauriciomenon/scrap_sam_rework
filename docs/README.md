# SCRAP_SAM - Sistema de Scraping Reorganizado

## Visão Geral

Este projeto foi completamente reorganizado para melhorar a manutenibilidade, escalabilidade e confiabilidade do sistema de scraping do SAM (Sistema de Manutenção).

## Estrutura do Projeto

```
scrap_sam_rework/
├── src/
│   ├── scrapers/           # Módulos de scraping
│   │   ├── scrap_sam_main.py    # Implementação principal (Playwright)
│   │   ├── legacy/             # Versões antigas mantidas para referência
│   │   └── __init__.py
│   ├── dashboard/          # Módulos do dashboard
│   │   ├── Dashboard_SM.py
│   │   └── Report_from_excel.py
│   └── utils/              # Utilitários e ferramentas auxiliares
│       ├── scrap_installer.py
│       ├── Acha_botao.py
│       └── lixo_para_servir_de_base.py
├── config/                 # Arquivos de configuração
├── tests/                  # Testes unitários e de integração
├── docs/                   # Documentação
├── reports/                # Relatórios de análise e plano
├── PLANO_REORGANIZACAO.md  # Plano de reorganização (sempre ler primeiro!)
└── README.md               # Este arquivo
```

## Como Usar

### Instalação
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o instalador de drivers: `python src/utils/scrap_installer.py`

### Execução
```python
from src.scrapers import run_scraping

# Executar scraping principal
run_scraping()
```

## Funcionalidades

- **Scraping Automatizado**: Extração de dados do sistema SAM
- **Tratamento de Erros**: Sistema robusto de detecção e recuperação de erros
- **Dashboard**: Visualização de dados extraídos
- **Logging Estruturado**: Rastreamento completo de operações

## Desenvolvimento

### Adicionando Novos Scrapers
1. Crie novo arquivo em `src/scrapers/`
2. Implemente a classe seguindo o padrão de `scrap_sam_main.py`
3. Atualize `__init__.py` para exportar a nova funcionalidade

### Testes
- Adicione testes em `tests/`
- Execute com: `python -m pytest tests/`

## Histórico de Versões

- **v2.0.0** (2025-09-01): Reorganização completa, consolidação de versões
- **v1.x**: Versões legadas em `src/scrapers/legacy/`

## Contribuição

1. Leia o `PLANO_REORGANIZACAO.md` antes de qualquer alteração
2. Siga os padrões estabelecidos
3. Adicione testes para novas funcionalidades
4. Atualize a documentação

## Suporte

Para questões técnicas, consulte:
- `reports/levantamento_e_plano_reorganizacao.md` - Análise completa
- Logs em tempo real durante execução
- Documentação em `docs/`

---

**Importante**: Sempre consulte o plano de reorganização antes de fazer alterações!

## Executar o Dashboard SSA (guia rápido)

- Coloque novas planilhas Excel em `downloads/`. O runner escolhe automaticamente o arquivo mais recente que comece com “SSAs Pendentes Geral - …”.
- Você pode especificar um arquivo manualmente com `--file`.
- A porta é escolhida automaticamente a partir de 8080 (se ocupada, tenta a próxima livre), ou defina com `--port`.

Exemplos:

```bash
# Seleção automática de arquivo/porta
/Users/menon/git/scrap_sam_rework/.venv/bin/python src/dashboard/Class/run.py

# Forçando porta e arquivo
/Users/menon/git/scrap_sam_rework/.venv/bin/python src/dashboard/Class/run.py --port 8050 --file downloads/"SSAs Pendentes Geral - 05-11-2024_0753AM.xlsx"
```

Validação de planilhas (opcional):

```bash
/Users/menon/git/scrap_sam_rework/.venv/bin/python scripts/validate_excels.py
```

O validador varre `downloads/*.xlsx` e gera um relatório em `docs/VALIDATION_REPORT.md`.

## Troubleshooting (Dashboard SSA)

- Ausência de planilhas: adicione um `.xlsx` em `downloads/` ou especifique com `--file`.
- Porta ocupada: use `--port` ou deixe o runner escolher a próxima livre.
- Import/Path em ambientes interativos: rode a partir da raiz do repo; prefira o Python do venv.
- `pytest` fora do venv: use `/.venv/bin/python -m pytest` do repositório.
- Playwright sem binários: `python -m playwright install` (Linux: `--with-deps`).
- Datas inconsistentes: utilize `scripts/validate_excels.py` para diagnosticar e o relatório em `docs/VALIDATION_REPORT.md`.