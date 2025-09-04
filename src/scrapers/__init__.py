"""SCRAP_SAM - Módulo de Scraping Consolidado

Este módulo contém as implementações consolidadas para scraping do sistema SAM.
Versão principal baseada em Playwright com tratamento avançado de erros.

Módulos disponíveis:
- scrap_sam_main: Implementação principal com Playwright
- scrap_sam_legacy: Versões legadas (Selenium) mantidas para referência
"""

from .scrap_sam_main import SAMNavigator, ErrorTracker
from .scrap_sam_main import main as run_scraping

__version__ = "2.0.0"
__author__ = "GitHub Copilot"
__date__ = "2025-09-01"

__all__ = ["SAMNavigator", "ErrorTracker", "run_scraping"]
