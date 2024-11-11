import os
import sys
import logging
import warnings
import traceback
from pathlib import Path
from datetime import datetime

# Adiciona o diretório atual ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Imports dos módulos locais
from src.dashboard.ssa_dashboard import SSADashboard
from src.data.data_loader import DataLoader

# Configurações globais
warnings.filterwarnings("ignore")


def setup_logging():
    """Configura o sistema de logging."""
    # Cria diretório de logs se não existir
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configura o formato do log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(
                os.path.join(log_dir, "dashboard.log"), encoding="utf-8"
            ),
            logging.StreamHandler(),
        ],
    )


def main():
    try:
        # Configura logging
        setup_logging()

        # Configura o caminho do arquivo Excel
        DATA_FILE_PATH = r"C:\Users\menon\git\trabalho\SCRAP-SAM\DashboardSM\Downloads\SSAs Pendentes Geral - 05-11-2024_0753AM.xlsx"

        # Cria diretórios necessários
        for directory in ["logs", "downloads"]:
            os.makedirs(directory, exist_ok=True)

        print(
            """
██████╗  █████╗ ███████╗██╗  ██╗    ███████╗███████╗ █████╗ 
██╔══██╗██╔══██╗██╔════╝██║  ██║    ██╔════╝██╔════╝██╔══██╗
██║  ██║███████║███████╗███████║    ███████╗███████╗███████║
██║  ██║██╔══██║╚════██║██╔══██║    ╚════██║╚════██║██╔══██║
██████╔╝██║  ██║███████║██║  ██║    ███████║███████║██║  ██║
╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝╚══════╝╚═╝  ╚═╝
        """
        )

        print("\nIniciando carregamento dos dados...")
        loader = DataLoader(DATA_FILE_PATH)
        df = loader.load_data()
        print(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")

        print("\nIniciando dashboard...")
        app = SSADashboard(df)

        print(
            f"""
Dashboard iniciado com sucesso!
URL: http://localhost:8080
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Pressione CTRL+C para encerrar.
        """
        )

        app.run_server(debug=True, port=8080)

    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
