import os
import sys
import logging
import pandas as pd
import warnings
from datetime import datetime
from pathlib import Path

# Importações locais
from dataclasses import dataclass
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL, dash_table
import dash_bootstrap_components as dbc
import logging
from dash import dash_table
from typing import Union, Tuple
from typing import Dict, List, Optional
import dash
import warnings
import traceback
from flask import request
import xlsxwriter
import pdfkit

import os
import sys
import logging
from pathlib import Path

# Adiciona o diretório atual ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Imports dos módulos locais
from src.dashboard.ssa_dashboard import SSADashboard
from src.data.data_loader import DataLoader
from src.data.ssa_data import SSAData
from src.data.ssa_columns import SSAColumns
from src.utils.log_manager import LogManager
from src.utils.date_utils import diagnose_dates
from src.utils.file_manager import FileManager

# Configurações globais
warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dashboard.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def setup_directories():
    """Cria diretórios necessários se não existirem."""
    directories = ["logs", "downloads", "backups", "cache"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def validate_environment():
    """Valida variáveis de ambiente e dependências."""
    required_packages = [
        "dash",
        "dash-bootstrap-components",
        "pandas",
        "plotly",
        "xlsxwriter",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.error(f"Pacotes faltando: {', '.join(missing_packages)}")
        logger.error("Use: pip install " + " ".join(missing_packages))
        sys.exit(1)


def load_configuration():
    """Carrega configurações do sistema."""
    # Aqui você pode adicionar lógica para carregar de um arquivo config.json ou .env
    config = {
        "DATA_FILE_PATH": r"C:\Users\menon\git\trabalho\SCRAP-SAM\DashboardSM\Downloads\SSAs Pendentes Geral - 05-11-2024_0753AM.xlsx",
        "PORT": 8080,
        "DEBUG": True,
        "HOST": "0.0.0.0",
        "LOG_LEVEL": "INFO",
        "AUTO_RELOAD_INTERVAL": 5 * 60 * 1000,  # 5 minutos em milissegundos
    }
    return config


def initialize_dashboard(config):
    """Inicializa o dashboard com as configurações fornecidas."""
    try:
        # Inicializa o gerenciador de arquivos
        file_manager = FileManager(os.path.dirname(config["DATA_FILE_PATH"]))

        # Verifica se existe arquivo mais recente
        try:
            latest_file = file_manager.get_latest_file("ssa_pendentes")
            if latest_file != config["DATA_FILE_PATH"]:
                logger.info(f"Encontrado arquivo mais recente: {latest_file}")
                config["DATA_FILE_PATH"] = latest_file
        except FileNotFoundError:
            logger.warning(
                "Usando arquivo configurado pois não foi encontrado mais recente"
            )

        # Carrega os dados
        logger.info("Iniciando carregamento dos dados...")
        loader = DataLoader(config["DATA_FILE_PATH"])
        df = loader.load_data()
        logger.info(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")

        # Cria e configura o dashboard
        dashboard = SSADashboard(df)

        return dashboard

    except Exception as e:
        logger.error(f"Erro ao inicializar dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def main():
    """Função principal."""
    try:
        print(
            """
█████████╗███████╗███████╗ █████╗     ██████╗  █████╗ ███████╗██╗  ██╗
██╚══════╝██╚════╝██╚════╝██╔══██╗    ██╔══██╗██╔══██╗██╔════╝██║  ██║
███████╗  ███████╗███████╗███████║    ██║  ██║███████║███████╗███████║
╚════██║  ╚════██║╚════██║██╔══██║    ██║  ██║██╔══██║╚════██║██╔══██║
███████║  ███████║███████║██║  ██║    ██████╔╝██║  ██║███████║██║  ██║
╚══════╝  ╚══════╝╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
        """
        )

        print("Inicializando Dashboard SSA...")

        # Configuração inicial
        setup_directories()
        validate_environment()
        config = load_configuration()

        # Configura logging baseado no config
        logging.getLogger().setLevel(config["LOG_LEVEL"])

        # Inicializa o dashboard
        dashboard = initialize_dashboard(config)

        print(
            f"""
Dashboard inicializado com sucesso!
- Acessível em: http://{config['HOST']}:{config['PORT']}
- Modo Debug: {'Ativado' if config['DEBUG'] else 'Desativado'}
- Auto Reload: {config['AUTO_RELOAD_INTERVAL']/1000/60} minutos
        """
        )

        # Inicia o servidor
        dashboard.run_server(
            debug=config["DEBUG"], port=config["PORT"], host=config["HOST"]
        )

    except KeyboardInterrupt:
        print("\nDesligando o servidor...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro fatal: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


class LogManager:
    """Gerencia o logging do sistema."""

    def __init__(self):
        self.logger = logging.getLogger("dashboard.monitor")
        self.logger.setLevel(logging.INFO)

    def log_with_ip(self, level: str, message: str):
        """Registra log com informações de IP."""
        try:
            if request:
                ip = request.remote_addr
            else:
                ip = "system"
        except:
            ip = "system"

        if level.upper() == "INFO":
            self.logger.info(f"[{ip}] {message}")
        elif level.upper() == "WARNING":
            self.logger.warning(f"[{ip}] {message}")
        elif level.upper() == "ERROR":
            self.logger.error(f"[{ip}] {message}")


def check_dependencies():
    """Verifica e instala dependências necessárias."""
    try:
        import xlsxwriter
    except ImportError:
        logger.warning("xlsxwriter não encontrado. Tentando instalar...")
        import subprocess

        subprocess.check_call(["pip", "install", "xlsxwriter"])
        logger.info("xlsxwriter instalado com sucesso")


if __name__ == "__main__":
    main()
