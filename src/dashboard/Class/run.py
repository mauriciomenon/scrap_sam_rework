import os
import sys
import logging
import warnings
import traceback
import socket
import platform
from pathlib import Path
from datetime import datetime

def get_python_command():
    """Determina o comando Python com base no sistema operacional."""
    system = platform.system().lower()
    
    if system == 'darwin':  # macOS
        return 'python3'
    elif system == 'linux':
        return 'python3'
    elif system == 'windows':
        return 'python'
    else:
        return 'python'  # fallback padrão

# Configura o comando Python correto para o sistema
PYTHON_CMD = get_python_command()

# Adiciona o diretório atual ao PYTHONPATH usando Path
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# Imports dos módulos locais
from src.dashboard.ssa_dashboard import SSADashboard
from src.data.data_loader import DataLoader
from src.utils.file_manager import FileManager
from src.utils.log_manager import LogManager

# Configurações globais
warnings.filterwarnings("ignore")

def setup_logging():
    """Configura o sistema de logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "dashboard.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

def get_available_port(starting_port=8080):
    """Tenta encontrar uma porta disponível a partir da porta inicial."""
    port = starting_port
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(('localhost', port)) != 0:
                    return port
        except:
            pass
        port += 1

def main():
    try:
        setup_logging()
        
        base_dir = Path.cwd()
        downloads_dir = base_dir / "downloads"
        downloads_dir.mkdir(exist_ok=True)
        
        file_manager = FileManager(downloads_dir)
        
        try:
            latest_file = file_manager.get_latest_file("ssa_pendentes")
            file_info = file_manager.get_file_info(latest_file)
            DATA_FILE_PATH = latest_file
            print(f"\nUsando arquivo: {file_info['name']}")
            print(f"Última modificação: {file_info['modified'].strftime('%d/%m/%Y %H:%M:%S')}")
        except FileNotFoundError:
            DATA_FILE_PATH = downloads_dir / "SSAs Pendentes Geral - 05-11-2024_0753AM.xlsx"
            print(f"\nUsando arquivo padrão: {DATA_FILE_PATH.name}")

        print("""
██████╗  █████╗ ███████╗██╗  ██╗    ███████╗███████╗ █████╗ 
██╔══██╗██╔══██╗██╔════╝██║  ██║    ██╔════╝██╔════╝██╔══██╗
██║  ██║███████║███████╗███████║    ███████╗███████╗███████║
██║  ██║██╔══██║╚════██║██╔══██║    ╚════██║╚════██║██╔══██║
██████╔╝██║  ██║███████║██║  ██║    ███████║███████║██║  ██║
╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝╚══════╝╚═╝  ╚═╝
        """)

        print("\nIniciando carregamento dos dados...")
        loader = DataLoader(DATA_FILE_PATH)
        df = loader.load_data()
        print(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")
        
        print("\nIniciando dashboard...")
        app = SSADashboard(df)
        
        port = get_available_port(8080)
        
        print(f"""
Dashboard iniciado com sucesso!
URL: http://localhost:{port}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Pressione CTRL+C para encerrar.
        """)
        
        app.run_server(debug=True, port=port)
        
    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()