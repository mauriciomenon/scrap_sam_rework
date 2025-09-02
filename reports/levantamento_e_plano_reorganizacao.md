# Relatório de Levantamento e Plano de Reorganização - SCRAP_SAM

**Data:** 1 de setembro de 2025
**Responsável:** GitHub Copilot
**Repositório Original:** SCRAP_SAM
**Novo Repositório:** scrap_sam_rework

## Levantamento das Condições do Repositório

Após uma análise detalhada do repositório SCRAP_SAM, identifiquei as seguintes condições:

### Estrutura Atual
- **Arquivos principais**: 3 versões paralelas de scraping (Selenium, Selenium BETA, Playwright) + variações otimizadas
- **Duplicatas**: Múltiplos arquivos idênticos em `/backups/` e raiz
- **Pastas especiais**: `DashboardSM/` com dashboard em Dash, `downloads/`, `drivers/`, `logs/`
- **Arquivos temporários**: `__pycache__/`, `tempCodeRunnerFile.python`, `lixo_para_servir_de_base.py`

### Estado do Git
- Branch única: `main` (atualizada com origin)
- Commits recentes: Adições de logs, backups e workflow GitHub Actions
- Arquivos não rastreados: `.github/chatmodes/`, `.snapshots/`

### Análise dos Arquivos Principais
- **scrap_SAM.py**: Selenium básico com Firefox, login manual, download de relatórios
- **scrap_SAM_BETA.py**: Selenium melhorado com download automático de drivers, tratamento de exceções
- **Scrap-Playwright.py**: Playwright com login automático, navegação estruturada
- **Variações otimizadas**: Tratamento de erro de rede, otimizações de performance

### Duplicatas Identificadas
- Scripts de scraping duplicados entre raiz e `/backups/`
- Arquivos de configuração (`config.json`, `config.yml`) em múltiplos locais
- Logs de execução espalhados por datas

### Dependências
- **Python**: `requirements.txt` em `DashboardSM/Class/` (Dash, pandas, plotly, etc.)
- **Drivers**: `scrap_installer.py` baixa Firefox e GeckoDriver automaticamente
- **Pacotes Node.js**: Não encontrados (possível confusão com dependências Python)

### Maturidade do Código
- **Pontos positivos**: Estrutura modular, tratamento de exceções, logs detalhados
- **Problemas**: 
  - Erros frequentes de rede (404 em recursos não essenciais)
  - Falhas em requisições POST ao site alvo
  - Código espalhado sem organização clara
  - Dependências não centralizadas

## Plano Detalhado de Reorganização

### Fase 1: Estruturação Básica (1-2 dias)
1. **Criar estrutura de pastas**:
   ```
   src/
     scrapers/          # Scripts de scraping consolidados
     dashboard/         # Código do dashboard
     utils/            # Utilitários compartilhados
   tests/              # Testes unitários
   docs/               # Documentação
   config/             # Arquivos de configuração
   ```

2. **Consolidar versões**:
   - Escolher `Scrap-Playwright_otimizado_tratamento_de_erro_rede.py` como versão estável
   - Migrar melhorias do Selenium BETA para a versão Playwright
   - Remover versões antigas após migração

3. **Limpar duplicatas**:
   - Mover conteúdo útil de `/backups/` para histórico Git
   - Remover arquivos duplicados
   - Adicionar `.gitignore` para ignorar logs, downloads temporários

### Fase 2: Centralização de Dependências (0.5 dia)
1. **Criar `requirements.txt` central**:
   - Consolidar dependências de todos os módulos
   - Incluir versões específicas para reprodutibilidade
   - Adicionar dependências de desenvolvimento (pytest, black, etc.)

2. **Atualizar instalador**:
   - Melhorar `scrap_installer.py` para detectar SO automaticamente
   - Adicionar verificação de versões de drivers

### Fase 3: Melhoria da Qualidade do Código (2-3 dias)
1. **Tratamento de erros**:
   - Implementar retry automático para falhas de rede
   - Melhorar logging com níveis apropriados
   - Adicionar validação de dados baixados

2. **Modularização**:
   - Separar lógica de scraping da interface
   - Criar classes para diferentes tipos de relatório
   - Implementar configuração via arquivo YAML/JSON

3. **Testes**:
   - Adicionar testes unitários para funções críticas
   - Criar mocks para simular respostas do site
   - Implementar testes de integração

### Fase 4: Documentação e Automação (1-2 dias)
1. **Documentação**:
   - Criar README.md com instruções de instalação e uso
   - Documentar API das classes principais
   - Adicionar exemplos de uso

2. **CI/CD**:
   - Melhorar workflow GitHub Actions
   - Adicionar linting e formatação automática
   - Implementar testes automatizados

### Fase 5: Migração e Limpeza Final (1 dia)
1. **Migrar dados**:
   - Mover logs antigos para `/logs/archive/`
   - Consolidar configurações em `/config/`
   - Limpar `/downloads/` de arquivos temporários

2. **Atualizar Git**:
   - Commit da nova estrutura
   - Criar tags para versões
   - Atualizar branch main

### Cronograma Sugerido
- **Semana 1**: Estruturação e consolidação
- **Semana 2**: Melhorias de código e testes
- **Semana 3**: Documentação e finalização

### Benefícios Esperados
- **Manutenibilidade**: Código organizado e documentado
- **Confiabilidade**: Melhor tratamento de erros
- **Escalabilidade**: Estrutura modular para novas funcionalidades
- **Colaboração**: Padrões claros para desenvolvimento

Este plano pode ser ajustado baseado em prioridades específicas. Recomendo começar pela consolidação das versões para ter uma base estável antes de implementar melhorias.
