import os
import sys
import logging
import warnings
import traceback
import socket
import platform
from pathlib import Path
from datetime import datetime
import argparse


def get_python_command():
    """Determina o comando Python com base no sistema operacional."""
    system = platform.system().lower()

    if system == "darwin":  # macOS
        return "python3"
    elif system == "linux":
        return "python3"
    elif system == "windows":
        return "python"
    else:
        return "python"  # fallback padrão


# Configura o comando Python correto para o sistema
PYTHON_CMD = get_python_command()

# Garanta que os diretórios 'Class' e 'Class/src' estejam no PYTHONPATH
current_dir = Path(__file__).resolve().parent
class_src = current_dir / "src"
for p in (str(class_src), str(current_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

"""
Imports de módulos do projeto serão feitos dentro de main(),
após ajustar sys.path para evitar conflitos com o 'src' da raiz.

Também expomos um símbolo de nível de módulo `SSADashboard` para permitir
monkeypatch nos testes sem acionar importações pesadas. Caso a importação real
falhe aqui (por exemplo, dependências ausentes), fornecemos um fallback dummy
que aceita a mesma interface mínima usada no smoke test.
"""


class _DummySSADashboard:
    """Fallback leve para testes: não inicia servidor de verdade."""

    def __init__(self, *args, **kwargs):
        pass

    def run_server(self, **kwargs):  # noqa: D401 - simples no-op
        # No-op: usado apenas em smoke tests quando não queremos levantar o servidor
        return None


def _setup_imports():
    """Setup imports and expose SSADashboard at module level (or dummy)."""
    current_dir = Path(__file__).resolve().parent
    class_src = current_dir / "src"
    for p in (str(current_dir), str(class_src)):
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        from src.dashboard.ssa_dashboard import SSADashboard as _RealSSADashboard  # type: ignore
        return _RealSSADashboard
    except Exception:
        # Qualquer erro aqui retorna um dummy para permitir monkeypatch em testes
        return _DummySSADashboard


# Expor símbolo patchable no import do módulo
SSADashboard = _setup_imports()

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
                if sock.connect_ex(("localhost", port)) != 0:
                    return port
        except:
            pass
        port += 1


def main(argv: list[str] | None = None):
    # Salva estado de import antes de alterações para não afetar outros testes/processos
    _old_sys_path = list(sys.path)
    _removed_modules: dict[str, object] = {}
    try:
        setup_logging()

        parser = argparse.ArgumentParser(description="Run SSA Dashboard")
        parser.add_argument("--file", dest="data_file", help="Path to an Excel file to load", default=None)
        parser.add_argument("--port", dest="port", help="Port to run the server", type=int, default=None)
        parser.add_argument(
            "--no-reload",
            dest="no_reload",
            action="store_true",
            help="Disable Flask/Dash reloader (prevents double-run in background tasks)",
        )
        args = parser.parse_args(argv)

        base_dir = Path.cwd()
        downloads_dir = base_dir / "downloads"
        downloads_dir.mkdir(exist_ok=True)

        # Preparar ambiente de import
        for key in [k for k in list(sys.modules) if k == "src" or k.startswith("src.")]:
            if key == "src.dashboard.ssa_dashboard":
                continue
            _removed_modules[key] = sys.modules.pop(key, None)

        current_dir = Path(__file__).resolve().parent
        class_src = current_dir / "src"
        for p in (str(current_dir), str(class_src)):
            if p not in sys.path:
                sys.path.insert(0, p)

        # Importes tardios agora que o ambiente está preparado
        from src.utils.file_manager import FileManager  # type: ignore
        from src.data.data_loader import DataLoader  # type: ignore

        file_manager = FileManager(str(downloads_dir))

        try:
            selected_path: Path
            if args.data_file:
                selected_path = Path(args.data_file)
                if not selected_path.exists():
                    raise FileNotFoundError(f"Arquivo não encontrado: {selected_path}")
            else:
                # Prioriza arquivos de 'SSAs Pendentes Geral - ...'
                try:
                    latest_path = Path(file_manager.get_latest_file("ssa_pendentes"))
                    selected_path = latest_path
                except Exception:
                    # fallback: qualquer .xlsx no diretório downloads, excluindo agregados como relatorio_ssas.xlsx
                    candidates = sorted(
                        [p for p in downloads_dir.glob("*.xlsx") if "relatorio_ssas" not in p.name.lower()],
                        key=lambda p: p.stat().st_mtime,
                        reverse=True,
                    )
                    if not candidates:
                        raise FileNotFoundError("Nenhum arquivo .xlsx encontrado em downloads/")
                    selected_path = candidates[0]

            DATA_FILE_PATH = selected_path
            file_info = file_manager.get_file_info(str(DATA_FILE_PATH))
            print(f"\nUsando arquivo: {file_info['name']}")
            print(
                f"Última modificação: {file_info['modified'].strftime('%d/%m/%Y %H:%M:%S')}"
            )
        except FileNotFoundError:
            DATA_FILE_PATH = downloads_dir / "SSAs Pendentes Geral - 05-11-2024_0753AM.xlsx"
            print(f"\nUsando arquivo padrão: {DATA_FILE_PATH.name}")

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
        loader = DataLoader(str(DATA_FILE_PATH))
        df = loader.load_data()
        print(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")

        print("\nIniciando dashboard...")
        app = SSADashboard(df)

        desired = args.port if args.port else 8080
        port = get_available_port(desired)

        print(
            f"""
Dashboard iniciado com sucesso!
URL: http://localhost:{port}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Pressione CTRL+C para encerrar.
            """
        )
        # Evita spawn duplo quando em tarefa de background no VS Code
        run_kwargs = {"debug": True, "port": port}
        if args.no_reload:
            # Disable reloader and debug for quieter background runs
            os.environ["FLASK_ENV"] = "production"
            os.environ["FLASK_DEBUG"] = "0"
            os.environ["DASH_DEBUG"] = "0"
            os.environ["WERKZEUG_DEBUG_PIN"] = "off"
            run_kwargs["use_reloader"] = False
            run_kwargs["debug"] = False
            # Dash dev tools flags for explicitness across versions
            run_kwargs["dev_tools_hot_reload"] = False
            run_kwargs["dev_tools_ui"] = False
            run_kwargs["dev_tools_silence_routes_logging"] = True
        app.run_server(**run_kwargs)

    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Restaura sys.modules removidos e sys.path original
        try:
            for k, v in _removed_modules.items():
                if v is not None:
                    sys.modules[k] = v  # type: ignore[assignment]
        finally:
            sys.path[:] = _old_sys_path


if __name__ == "__main__":
    main()
