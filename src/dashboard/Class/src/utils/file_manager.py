# src/utils/file_manager.py
import os
import re
import logging
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path


class FileManager:
    """Gerencia o carregamento e identificação de arquivos de SSA."""

    def __init__(self, base_directory: str):
        """
        Inicializa o gerenciador de arquivos.

        Args:
            base_directory (str): Diretório base onde procurar os arquivos
        """
        self.base_directory = Path(base_directory)
        self.file_patterns: Dict[str, re.Pattern] = {
            "ssa_pendentes": re.compile(
                r"SSAs Pendentes Geral - (\d{2})-(\d{2})-(\d{4})_(\d{4})(AM|PM)\.xlsx"
            ),
            "ssa_programadas": re.compile(
                r"SSAs Programadas - (\d{2})-(\d{2})-(\d{4})_(\d{4})(AM|PM)\.xlsx"
            ),
            # Adicione outros padrões conforme necessário
        }

    def _convert_to_datetime(self, match: re.Match) -> datetime:
        """
        Converte os grupos do match em objeto datetime.

        Args:
            match: Match object do regex com grupos de data/hora

        Returns:
            datetime: Data e hora extraídas do nome do arquivo
        """
        try:
            day, month, year, time, period = match.groups()
            hour = int(time[:2])
            minute = int(time[2:])

            # Converte para formato 24 horas
            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0

            return datetime(int(year), int(month), int(day), hour, minute)
        except Exception as e:
            logging.error(f"Erro ao converter data/hora do arquivo: {str(e)}")
            raise

    def get_latest_file(
        self, pattern_key: str, subdirectory: Optional[str] = None
    ) -> str:
        """
        Encontra o arquivo mais recente que corresponde ao padrão especificado.

        Args:
            pattern_key (str): Chave do padrão de arquivo ('ssa_pendentes', etc)
            subdirectory (str, optional): Subdiretório opcional para buscar

        Returns:
            str: Caminho completo do arquivo mais recente

        Raises:
            FileNotFoundError: Se nenhum arquivo correspondente for encontrado
            KeyError: Se o pattern_key não existir
        """
        try:
            pattern = self.file_patterns.get(pattern_key)
            if not pattern:
                raise KeyError(f"Padrão '{pattern_key}' não encontrado")

            search_dir = self.base_directory
            if subdirectory:
                search_dir = search_dir / subdirectory

            if not search_dir.exists():
                raise FileNotFoundError(f"Diretório '{search_dir}' não encontrado")

            latest_file = None
            latest_time = None

            # Lista todos os arquivos no diretório
            for file_path in search_dir.glob("*.xlsx"):
                match = pattern.match(file_path.name)
                if match:
                    file_datetime = self._convert_to_datetime(match)

                    if latest_time is None or file_datetime > latest_time:
                        latest_time = file_datetime
                        latest_file = file_path

            if latest_file:
                logging.info(
                    f"Arquivo mais recente encontrado: {latest_file.name} "
                    f"({latest_time.strftime('%d/%m/%Y %H:%M')})"
                )
                return str(latest_file)
            else:
                raise FileNotFoundError(
                    f"Nenhum arquivo correspondente ao padrão '{pattern_key}' "
                    f"encontrado em '{search_dir}'"
                )

        except Exception as e:
            logging.error(f"Erro ao buscar arquivo mais recente: {str(e)}")
            raise

    def register_pattern(self, key: str, pattern: str):
        """
        Registra um novo padrão de arquivo.

        Args:
            key (str): Chave para identificar o padrão
            pattern (str): Padrão regex para o nome do arquivo
        """
        try:
            self.file_patterns[key] = re.compile(pattern)
            logging.info(f"Novo padrão '{key}' registrado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao registrar padrão '{key}': {str(e)}")
            raise

    def validate_file(self, file_path: str) -> bool:
        """
        Valida se um arquivo existe e pode ser lido.

        Args:
            file_path (str): Caminho do arquivo

        Returns:
            bool: True se o arquivo é válido
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logging.error(f"Arquivo não encontrado: {file_path}")
                return False
            if not path.is_file():
                logging.error(f"Caminho não é um arquivo: {file_path}")
                return False
            if not os.access(path, os.R_OK):
                logging.error(f"Arquivo sem permissão de leitura: {file_path}")
                return False
            return True
        except Exception as e:
            logging.error(f"Erro ao validar arquivo {file_path}: {str(e)}")
            return False

    def get_file_info(self, file_path: str) -> Dict:
        """
        Retorna informações sobre um arquivo.

        Args:
            file_path (str): Caminho do arquivo

        Returns:
            Dict com informações do arquivo
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            stats = path.stat()
            return {
                "name": path.name,
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime),
                "modified": datetime.fromtimestamp(stats.st_mtime),
                "is_valid": self.validate_file(file_path),
            }
        except Exception as e:
            logging.error(f"Erro ao obter informações do arquivo: {str(e)}")
            raise
