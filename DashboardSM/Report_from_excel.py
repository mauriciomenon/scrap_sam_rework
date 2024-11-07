from dataclasses import dataclass
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import logging
from dash import dash_table
from typing import Union, Tuple
from typing import Dict, List, Optional
import warnings
import traceback
import xlsxwriter
import pdfkit

# Depois de todos os imports
warnings.filterwarnings("ignore")

# Configuração do caminho do arquivo no início do script
DATA_FILE_PATH = r"C:\Users\menon\git\trabalho\SCRAP-SAM\DashboardSM\Downloads\SSAs Pendentes Geral - 05-11-2024_0753AM.xlsx"

@dataclass
class SSAData:
    """Estrutura de dados para uma SSA."""

    numero: str
    situacao: str
    derivada: Optional[str]
    localizacao: str
    desc_localizacao: str
    equipamento: str
    semana_cadastro: str
    emitida_em: datetime
    descricao: str
    setor_emissor: str
    setor_executor: str
    solicitante: str
    servico_origem: str
    prioridade_emissao: str
    prioridade_planejamento: Optional[str]
    execucao_simples: str
    responsavel_programacao: Optional[str]
    semana_programada: Optional[str]
    responsavel_execucao: Optional[str]
    descricao_execucao: Optional[str]
    sistema_origem: str
    anomalia: Optional[str]

    def to_dict(self) -> Dict:
        """Converte o objeto para dicionário."""
        return {
            "numero": self.numero,
            "situacao": self.situacao,
            "setor_executor": self.setor_executor,
            "prioridade": self.prioridade_emissao,
            "emitida_em": (
                self.emitida_em.strftime("%Y-%m-%d %H:%M:%S")
                if self.emitida_em
                else None
            ),
        }


class DataLoader:
    """Carrega e prepara os dados das SSAs."""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.ssa_objects = []

    def validate_and_fix_date(self, date_str, row_num, logger=None):
        """
        Valida e corrige valores de data apenas quando necessário.
        """
        import pandas as pd
        from datetime import datetime

        def log_issue(message):
            if logger:
                logger.warning(f"Linha {row_num}: {message}")

        try:
            # Se já for timestamp válido, retorna diretamente
            if isinstance(date_str, pd.Timestamp):
                return date_str

            # Se for string vazia ou NaT/nan, então sim, precisamos tentar recuperar
            if pd.isna(date_str) or date_str == "" or date_str == "NaT":
                log_issue(f"Data vazia ou inválida (valor original = {date_str})")
                return None

            # Se for string com formato válido, converte
            try:
                # Primeiro tenta o formato padrão do sistema
                return pd.to_datetime(date_str, format="%d/%m/%Y %H:%M:%S")
            except:
                # Se falhar, tenta formato flexível
                try:
                    return pd.to_datetime(date_str)
                except:
                    log_issue(f"Formato de data não reconhecido: {date_str}")
                    return None

        except Exception as e:
            log_issue(f"Erro ao processar data: {str(e)}")
            return None


    def _convert_dates(self):
        """Converte e valida datas mantendo o tipo apropriado."""
        try:
            # Se a coluna já for datetime, não precisa converter
            if pd.api.types.is_datetime64_any_dtype(self.df.iloc[:, SSAColumns.EMITIDA_EM]):
                logging.info("Coluna já está em formato datetime")
                return

            # Converte diretamente para datetime usando o formato correto
            self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.to_datetime(
                self.df.iloc[:, SSAColumns.EMITIDA_EM],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce",
            )

            # Verifica se houve problemas
            invalid_mask = self.df.iloc[:, SSAColumns.EMITIDA_EM].isna()
            invalid_count = invalid_mask.sum()

            if invalid_count > 0:
                logging.error(f"Encontradas {invalid_count} datas inválidas")
                for idx in invalid_mask[invalid_mask].index:
                    logging.error(
                        f"Linha {idx + 1}: Data inválida - verificar valor original"
                    )

        except Exception as e:
            logging.error(f"Erro no processamento de datas: {str(e)}")
            raise

    def load_data(self) -> pd.DataFrame:
        """Carrega dados do Excel com as configurações corretas."""
        try:
            # Carrega o Excel pulando a primeira linha (cabeçalho na segunda linha)
            self.df = pd.read_excel(
                self.excel_path,
                header=1,  # Cabeçalho na segunda linha
            )

            # NOVO: Diagnóstico de datas antes da conversão
            date_diagnosis = diagnose_dates(self.df, SSAColumns.EMITIDA_EM)
            if date_diagnosis['error_count'] > 0:
                logging.info("=== Diagnóstico de Datas ===")
                logging.info(f"Total de linhas: {date_diagnosis['total_rows']}")
                logging.info(f"Problemas encontrados: {date_diagnosis['error_count']}")
                for prob in date_diagnosis['problematic_rows']:
                    logging.info(f"\nLinha {prob['index'] + 1}:")
                    logging.info(f"  Valor encontrado: {prob['value']}")
                    logging.info(f"  Motivo: {prob['reason']}")
                    logging.info("  Dados da linha:")
                    for key, value in prob['row_data'].items():
                        logging.info(f"    {key}: {value}")

            # Converte as datas usando o novo método
            self._convert_dates()

            # Converte colunas string
            string_columns = [
                SSAColumns.NUMERO_SSA,
                SSAColumns.SITUACAO,
                SSAColumns.SEMANA_CADASTRO,
                SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                SSAColumns.SETOR_EXECUTOR,
                SSAColumns.DERIVADA,
                SSAColumns.LOCALIZACAO,
                SSAColumns.DESC_LOCALIZACAO,
                SSAColumns.EQUIPAMENTO,
                SSAColumns.DESC_SSA,
                SSAColumns.SETOR_EMISSOR,
                SSAColumns.SOLICITANTE,
                SSAColumns.SERVICO_ORIGEM,
                SSAColumns.EXECUCAO_SIMPLES,
                SSAColumns.SISTEMA_ORIGEM,
                SSAColumns.ANOMALIA,
            ]

            for col in string_columns:
                try:
                    self.df.iloc[:, col] = (
                        self.df.iloc[:, col].astype(str).str.strip().replace("nan", "")
                    )
                except Exception as e:
                    logging.error(f"Erro ao converter coluna {col}: {str(e)}")

            # Padroniza prioridades para maiúsculas
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] = (
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].str.upper().str.strip()
            )

            # Converte colunas opcionais
            optional_string_columns = [
                SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO,
                SSAColumns.RESPONSAVEL_PROGRAMACAO,
                SSAColumns.SEMANA_PROGRAMADA,
                SSAColumns.RESPONSAVEL_EXECUCAO,
                SSAColumns.DESCRICAO_EXECUCAO,
            ]

            for col in optional_string_columns:
                try:
                    self.df.iloc[:, col] = (
                        self.df.iloc[:, col]
                        .astype(str)
                        .replace("nan", None)
                        .replace("", None)
                    )
                except Exception as e:
                    logging.error(f"Erro ao converter coluna opcional {col}: {str(e)}")

            # Remove linhas com número da SSA vazio
            self.df = self.df[self.df.iloc[:, SSAColumns.NUMERO_SSA].str.strip() != ""]

            # Converte semana cadastro para string preenchendo com zeros à esquerda
            try:
                # Trata semana cadastro
                self.df.iloc[:, SSAColumns.SEMANA_CADASTRO] = (
                    pd.to_numeric(
                        self.df.iloc[:, SSAColumns.SEMANA_CADASTRO], errors="coerce"
                    )
                    .fillna(0)
                    .astype(int)
                    .astype(str)
                    .str.zfill(6)  # Garante 6 dígitos (AAASS)
                )

                # Trata semana programada
                self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA] = (
                    pd.to_numeric(
                        self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA], errors="coerce"
                    )
                    .fillna(0)
                    .astype(int)
                    .astype(str)
                    .str.zfill(6)
                )
                self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA] = self.df.iloc[
                    :, SSAColumns.SEMANA_PROGRAMADA
                ].replace("000000", None)

            except Exception as e:
                logging.error(f"Erro ao formatar semanas: {str(e)}")

            # Converte para objetos SSAData
            self._convert_to_objects()

            # Verifica a qualidade dos dados após todas as conversões
            self._validate_data_quality()

            return self.df

        except Exception as e:
            logging.error(f"Erro ao carregar dados: {str(e)}")
            raise

    def _validate_data_quality(self):
        """Valida a qualidade dos dados após as conversões."""
        issues = []

        # Verifica datas válidas
        valid_dates = self.df.iloc[:, SSAColumns.EMITIDA_EM].notna().sum()
        total_rows = len(self.df)
        if valid_dates < total_rows:
            diff = total_rows - valid_dates
            issues.append(
                f"{diff} data{'s' if diff > 1 else ''} inválida{'s' if diff > 1 else ''}"
            )

        # Verifica campos obrigatórios vazios
        for col in [
            SSAColumns.NUMERO_SSA,
            SSAColumns.SITUACAO,
            SSAColumns.GRAU_PRIORIDADE_EMISSAO,
        ]:
            empty_count = self.df.iloc[:, col].isna().sum()
            if empty_count > 0:
                issues.append(
                    f"{empty_count} {SSAColumns.get_name(col)} vazio{'s' if empty_count > 1 else ''}"
                )

        # Registra todos os problemas em uma única mensagem
        if issues:
            logging.warning("Problemas encontrados nos dados: " + "; ".join(issues))

    def _convert_to_objects(self):
        """Converte as linhas do DataFrame em objetos SSAData."""
        try:
            self.ssa_objects = []
            for idx, row in self.df.iterrows():
                try:
                    ssa = SSAData(
                        numero=str(row.iloc[SSAColumns.NUMERO_SSA]).strip(),
                        situacao=str(row.iloc[SSAColumns.SITUACAO]).strip(),
                        derivada=str(row.iloc[SSAColumns.DERIVADA]).strip() or None,
                        localizacao=str(row.iloc[SSAColumns.LOCALIZACAO]).strip(),
                        desc_localizacao=str(
                            row.iloc[SSAColumns.DESC_LOCALIZACAO]
                        ).strip(),
                        equipamento=str(row.iloc[SSAColumns.EQUIPAMENTO]).strip(),
                        semana_cadastro=str(
                            row.iloc[SSAColumns.SEMANA_CADASTRO]
                        ).strip(),
                        emitida_em=(
                            row.iloc[SSAColumns.EMITIDA_EM]
                            if pd.notna(row.iloc[SSAColumns.EMITIDA_EM])
                            else None
                        ),
                        descricao=str(row.iloc[SSAColumns.DESC_SSA]).strip(),
                        setor_emissor=str(row.iloc[SSAColumns.SETOR_EMISSOR]).strip(),
                        setor_executor=str(row.iloc[SSAColumns.SETOR_EXECUTOR]).strip(),
                        solicitante=str(row.iloc[SSAColumns.SOLICITANTE]).strip(),
                        servico_origem=str(row.iloc[SSAColumns.SERVICO_ORIGEM]).strip(),
                        prioridade_emissao=str(
                            row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                        )
                        .strip()
                        .upper(),
                        prioridade_planejamento=str(
                            row.iloc[SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO]
                        ).strip()
                        or None,
                        execucao_simples=str(
                            row.iloc[SSAColumns.EXECUCAO_SIMPLES]
                        ).strip(),
                        responsavel_programacao=str(
                            row.iloc[SSAColumns.RESPONSAVEL_PROGRAMACAO]
                        ).strip()
                        or None,
                        semana_programada=str(
                            row.iloc[SSAColumns.SEMANA_PROGRAMADA]
                        ).strip()
                        or None,
                        responsavel_execucao=str(
                            row.iloc[SSAColumns.RESPONSAVEL_EXECUCAO]
                        ).strip()
                        or None,
                        descricao_execucao=str(
                            row.iloc[SSAColumns.DESCRICAO_EXECUCAO]
                        ).strip()
                        or None,
                        sistema_origem=str(row.iloc[SSAColumns.SISTEMA_ORIGEM]).strip(),
                        anomalia=str(row.iloc[SSAColumns.ANOMALIA]).strip() or None,
                    )
                    self.ssa_objects.append(ssa)
                except Exception as e:
                    logging.error(f"Erro ao converter linha {idx}: {str(e)}")
                    continue

            logging.info(f"Convertidos {len(self.ssa_objects)} registros para SSAData")

            # Log exemplo do primeiro objeto convertido para verificação
            if self.ssa_objects:
                first_ssa = self.ssa_objects[0]
                logging.info(f"Exemplo de primeiro objeto convertido:")
                logging.info(f"Número: {first_ssa.numero}")
                logging.info(f"Data de emissão: {first_ssa.emitida_em}")
                logging.info(f"Prioridade: {first_ssa.prioridade_emissao}")

        except Exception as e:
            logging.error(f"Erro durante conversão para objetos: {str(e)}")
            raise

    def filter_ssas(
        self,
        setor: str = None,
        prioridade: str = None,
        data_inicio: datetime = None,
        data_fim: datetime = None,
    ) -> List[SSAData]:
        """Filtra SSAs com base nos critérios fornecidos."""
        filtered_ssas = self.get_ssa_objects()

        if setor:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.setor_executor and ssa.setor_executor.upper() == setor.upper()
            ]

        if prioridade:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.prioridade_emissao
                and ssa.prioridade_emissao.upper() == prioridade.upper()
            ]

        if data_inicio:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.emitida_em and ssa.emitida_em >= data_inicio
            ]

        if data_fim:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.emitida_em and ssa.emitida_em <= data_fim
            ]

        return filtered_ssas

    def get_ssa_objects(self) -> List[SSAData]:
        """Retorna a lista de objetos SSAData."""
        if not self.ssa_objects:
            self._convert_to_objects()
        return self.ssa_objects


class SSAColumns:
    """Mantém os índices e nomes das colunas."""

    # Índices
    NUMERO_SSA = 0
    SITUACAO = 1
    DERIVADA = 2
    LOCALIZACAO = 3
    DESC_LOCALIZACAO = 4
    EQUIPAMENTO = 5
    SEMANA_CADASTRO = 6
    EMITIDA_EM = 7
    DESC_SSA = 8
    SETOR_EMISSOR = 9
    SETOR_EXECUTOR = 10
    SOLICITANTE = 11
    SERVICO_ORIGEM = 12
    GRAU_PRIORIDADE_EMISSAO = 13
    GRAU_PRIORIDADE_PLANEJAMENTO = 14
    EXECUCAO_SIMPLES = 15
    RESPONSAVEL_PROGRAMACAO = 16
    SEMANA_PROGRAMADA = 17
    RESPONSAVEL_EXECUCAO = 18
    DESCRICAO_EXECUCAO = 19
    SISTEMA_ORIGEM = 20
    ANOMALIA = 21

    # Nomes para exibição
    COLUMN_NAMES = {
        NUMERO_SSA: "Número da SSA",
        SITUACAO: "Situação",
        DERIVADA: "Derivada de",
        LOCALIZACAO: "Localização",
        DESC_LOCALIZACAO: "Descrição da Localização",
        EQUIPAMENTO: "Equipamento",
        SEMANA_CADASTRO: "Semana de Cadastro",
        EMITIDA_EM: "Emitida Em",
        DESC_SSA: "Descrição da SSA",
        SETOR_EMISSOR: "Setor Emissor",
        SETOR_EXECUTOR: "Setor Executor",
        SOLICITANTE: "Solicitante",
        SERVICO_ORIGEM: "Serviço de Origem",
        GRAU_PRIORIDADE_EMISSAO: "Grau de Prioridade Emissão",
        GRAU_PRIORIDADE_PLANEJAMENTO: "Grau de Prioridade Planejamento",
        EXECUCAO_SIMPLES: "Execução Simples",
        RESPONSAVEL_PROGRAMACAO: "Responsável na Programação",
        SEMANA_PROGRAMADA: "Semana Programada",
        RESPONSAVEL_EXECUCAO: "Responsável na Execução",
        DESCRICAO_EXECUCAO: "Descrição Execução",
        SISTEMA_ORIGEM: "Sistema de Origem",
        ANOMALIA: "Anomalia",
    }

    @classmethod
    def get_name(cls, index: int) -> str:
        """Retorna o nome da coluna pelo índice."""
        return cls.COLUMN_NAMES.get(index, f"Coluna {index}")


@dataclass
class WeekInfo:
    """Represents ISO week information for calculations."""
    year: int
    week: int
    
    @classmethod
    def from_string(cls, week_str: str) -> Optional['WeekInfo']:
        """
        Creates WeekInfo from YYYYWW format string.
        Returns None if input is invalid.
        
        Args:
            week_str: String in format 'YYYYWW' (e.g., '202401')
        """
        if not isinstance(week_str, str) or len(week_str) != 6:
            return None
        
        try:
            year = int(week_str[:4])
            week = int(week_str[4:])
            
            # Basic validation
            if year < 2000 or year > 2100 or week < 1 or week > 53:
                return None
                
            return cls(year=year, week=week)
        except ValueError:
            return None

    def to_string(self) -> str:
        """Converts WeekInfo back to YYYYWW format."""
        return f"{self.year}{self.week:02d}"

class WeekCalculator:
    """Handles ISO week-based calculations with year transition awareness."""
    
    @staticmethod
    def get_iso_calendar(dt: Union[date, datetime]) -> Tuple[int, int, int]:
        """
        Gets ISO calendar information safely.
        Returns tuple of (year, week, weekday).
        """
        try:
            if isinstance(dt, datetime):
                dt = dt.date()
            return dt.isocalendar()
        except AttributeError:
            return (0, 0, 0)  # Invalid date

    @staticmethod
    def current_iso_week() -> WeekInfo:
        """Gets current ISO week information."""
        today = date.today()
        iso_year, iso_week, _ = today.isocalendar()
        return WeekInfo(year=iso_year, week=iso_week)

    @staticmethod
    def get_last_week_of_year(year: int) -> int:
        """
        Determines if a year has 52 or 53 ISO weeks.
        
        Args:
            year: The year to check
            
        Returns:
            Number of weeks (52 or 53)
        """
        # December 28th is always in the last week of the ISO year
        dec_28 = date(year, 12, 28)
        _, last_week, _ = dec_28.isocalendar()
        return last_week

    @classmethod
    def calculate_week_difference(
        cls,
        week1: Optional[WeekInfo],
        week2: Optional[WeekInfo]
    ) -> Optional[int]:
        """
        Calculates the difference between two ISO weeks, handling year transitions.
        
        Args:
            week1: First WeekInfo object
            week2: Second WeekInfo object
            
        Returns:
            Number of weeks difference or None if invalid input
        """
        if not week1 or not week2:
            return None
            
        if week1.year == week2.year:
            return week2.week - week1.week
            
        # Handle year transitions
        total_weeks = 0
        
        # Add weeks for complete years between
        for year in range(week1.year, week2.year):
            total_weeks += cls.get_last_week_of_year(year)
            
        # Adjust for partial weeks in start and end year
        total_weeks -= week1.week
        total_weeks += week2.week
        
        return total_weeks

class SSAWeekAnalyzer:
    """Analyzes SSA data with respect to weeks, following ISO standard."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.calculator = WeekCalculator()
        self.current_date = date.today()
        self.current_year = self.current_date.year
        self.current_week = self.current_date.isocalendar()[1]

    def _parse_week_str(self, week_str: Union[str, float, None]) -> Optional[WeekInfo]:
        """
        Parseia string de semana no formato YYYYSS.

        Args:
            week_str: String no formato YYYYSS (ex: 202401)

        Returns:
            WeekInfo object ou None se inválido
        """
        if pd.isna(week_str) or not str(week_str).strip():
            return None

        try:
            week_str = str(week_str).replace(".0", "")
            if len(week_str) != 6:
                return None

            year = int(week_str[:4])
            week = int(week_str[4:])

            # Validação básica
            if year < 2000 or year > self.current_year + 5 or week < 1 or week > 53:
                return None

            return WeekInfo(year=year, week=week)
        except ValueError:
            return None

    def calculate_weeks_in_state(self) -> pd.Series:
        """
        Calcula quantas semanas cada SSA está em seu estado atual.
        Considera transições de ano e mantém valores NaN.

        Returns:
            Series com contagem de semanas, preservando NaN para entradas inválidas
        """
        current_week = self.calculator.current_iso_week()

        def process_week(week_str: Union[str, float, None]) -> Optional[int]:
            week_info = self._parse_week_str(week_str)
            if not week_info:
                return None

            diff = self.calculator.calculate_week_difference(week_info, current_week)
            return diff if diff is not None and diff >= 0 else None

        weeks_in_state = self.df.iloc[:, SSAColumns.SEMANA_CADASTRO].apply(process_week)

        # Log de estatísticas
        total_rows = len(weeks_in_state)
        valid_counts = weeks_in_state.notna().sum()

        logging.info(
            f"Week calculation stats: {valid_counts}/{total_rows} valid calculations"
        )
        if valid_counts < total_rows:
            logging.warning(
                f"Found {total_rows - valid_counts} entries with invalid or missing week data"
            )

        return weeks_in_state

    def analyze_weeks(self, use_programmed: bool = True) -> pd.DataFrame:
        """
        Analisa distribuição de SSAs por semana e ano.

        Args:
            use_programmed: Se True, usa semana_programada, senão usa semana_cadastro

        Returns:
            DataFrame com análise por ano e semana
        """
        week_column = (
            SSAColumns.SEMANA_PROGRAMADA
            if use_programmed
            else SSAColumns.SEMANA_CADASTRO
        )

        week_data = []
        for _, row in self.df.iterrows():
            year, week = self._get_year_week(row.iloc[week_column])
            if year and week:
                week_data.append(
                    {
                        "year": year,
                        "week": week,
                        "year_week": f"{year}{week:02d}",
                        "ssa_number": row.iloc[SSAColumns.NUMERO_SSA],
                        "prioridade": row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                    }
                )

        if not week_data:
            return pd.DataFrame()

        df_weeks = pd.DataFrame(week_data)

        # Agrupa por ano, semana e prioridade
        analysis = (
            df_weeks.groupby(["year", "week", "prioridade"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        # Adiciona coluna com formato ano-semana para display
        analysis["year_week"] = analysis.apply(
            lambda x: f"{x['year']}{x['week']:02d}", axis=1
        )

        return analysis.sort_values(["year", "week"])


    def create_week_chart(self, use_programmed: bool = True) -> go.Figure:
        """Cria gráfico de SSAs por semana."""
        analysis = self.week_analyzer.analyze_weeks(use_programmed)

        if analysis.empty:
            return go.Figure().update_layout(
                self._get_standard_layout(
                    title="SSAs por Semana",
                    xaxis_title="Ano-Semana",
                    yaxis_title="Quantidade de SSAs",
                    annotations=[
                        {
                            "text": "Não há dados válidos disponíveis",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {"size": 14},
                        }
                    ],
                )
            )

        fig = go.Figure()

        for priority in analysis.columns[2:-1]:
            fig.add_trace(
                go.Bar(
                    name=priority,
                    x=analysis["year_week"],
                    y=analysis[priority],
                    text=analysis[priority],
                    textposition="auto",
                )
            )

        title_text = (
            "SSAs Programadas por Semana"
            if use_programmed
            else "SSAs Cadastradas por Semana"
        )

        fig.update_layout(
            self._get_standard_layout(
                title=title_text,
                xaxis_title="Ano-Semana",
                yaxis_title="Quantidade de SSAs",
                x_values=analysis["year_week"],
                barmode="stack",
            )
        )

        return fig

    def _get_year_week(self, week_str: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrai ano e semana de uma string YYYYSS.

        Args:
            week_str: String no formato YYYYSS (ex: 202401)

        Returns:
            Tuple (ano, semana) ou (None, None) se inválido
        """
        try:
            week_str = str(week_str).replace(".0", "").strip()
            if len(week_str) != 6:
                return None, None

            year = int(week_str[:4])
            week = int(week_str[4:])

            # Validação ISO
            if year < 2000 or year > self.current_year + 5 or week < 1 or week > 53:
                return None, None

            return year, week
        except (ValueError, AttributeError):
            return None, None

    def analyze_week_distribution(self) -> pd.DataFrame:
        """
        Analisa a distribuição de SSAs entre semanas, mantendo qualidade dos dados.

        Returns:
            DataFrame com estatísticas de distribuição por semana
        """
        analysis = self.analyze_weeks()

        if analysis.empty:
            return pd.DataFrame({
                'week_count': pd.Series(dtype='int64'),
                'cumulative_percent': pd.Series(dtype='float64')
            })

        # Calcular contagem total por semana (soma de todas as prioridades)
        total_por_semana = analysis.iloc[:, 2:-1].sum(axis=1)  # Soma todas as colunas exceto year, week e year_week

        # Criar análise de distribuição
        stats = pd.DataFrame({
            'week_count': total_por_semana,
            'cumulative_percent': (total_por_semana.cumsum() / total_por_semana.sum() * 100)
        })

        # Adicionar métricas de qualidade
        invalid_count = len(self.df) - total_por_semana.sum()
        if len(self.df) > 0:
            invalid_percent = (invalid_count / len(self.df)) * 100
        else:
            invalid_percent = 0

        stats.loc['missing_data'] = [invalid_count, invalid_percent]

        return stats


class SSAVisualizer:
    """Gera visualizações específicas para SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.week_analyzer = SSAWeekAnalyzer(df)  # Adicionar analisador de semanas


    def _get_standard_layout(
        self,
        title: str,
        xaxis_title: str = None,
        yaxis_title: str = None,
        x_values: list = None,
        show_year_annotation: bool = True,
        chart_type: str = "default",
        **kwargs,
    ) -> dict:
        """
        Retorna configuração padrão de layout para gráficos com tratamento robusto para diferentes tipos.

        Args:
            title: Título do gráfico
            xaxis_title: Título do eixo X (opcional)
            yaxis_title: Título do eixo Y (opcional)
            x_values: Valores para o eixo X (opcional)
            show_year_annotation: Se deve mostrar anotação de anos
            chart_type: Tipo de gráfico ('bar', 'line', 'heatmap', 'scatter', 'default')
            **kwargs: Configurações adicionais de layout
        """
        # Layout base que funciona para todos os tipos de gráfico
        base_layout = {
            "title": title,
            "template": "plotly_white",
            "showlegend": True,
            "margin": {"l": 50, "r": 20, "t": 50, "b": 50},
        }

        # Adiciona configurações de eixos apenas se fornecidos
        if xaxis_title is not None:
            base_layout["xaxis_title"] = xaxis_title
        if yaxis_title is not None:
            base_layout["yaxis_title"] = yaxis_title

        # Configurações específicas por tipo de gráfico
        chart_specific = {
            "bar": {
                "xaxis": {"tickangle": -45, "tickfont": {"size": 10}, "showgrid": True},
                "yaxis": {"showgrid": True, "gridcolor": "lightgray"},
                "bargap": 0.2,
                "bargroupgap": 0.1,
            },
            "line": {
                "xaxis": {
                    "showgrid": True,
                    "gridcolor": "lightgray",
                    "showline": True,
                    "linewidth": 1,
                    "linecolor": "black",
                },
                "yaxis": {
                    "showgrid": True,
                    "gridcolor": "lightgray",
                    "showline": True,
                    "linewidth": 1,
                    "linecolor": "black",
                },
            },
            "heatmap": {
                "xaxis": {"side": "bottom", "tickfont": {"size": 10}},
                "yaxis": {"side": "left", "tickfont": {"size": 10}},
            },
            "scatter": {
                "xaxis": {"showgrid": True, "gridcolor": "lightgray", "zeroline": True},
                "yaxis": {"showgrid": True, "gridcolor": "lightgray", "zeroline": True},
            },
            "default": {
                "xaxis": {"showgrid": True, "gridcolor": "lightgray"},
                "yaxis": {"showgrid": True, "gridcolor": "lightgray"},
            },
        }

        # Seleciona configurações específicas do tipo de gráfico
        type_config = chart_specific.get(chart_type, chart_specific["default"])
        base_layout.update(type_config)

        # Configura valores específicos do eixo X se fornecidos
        if x_values is not None and "xaxis" in base_layout:
            base_layout["xaxis"].update(
                {"tickmode": "array", "ticktext": x_values, "tickvals": x_values}
            )

        # Adiciona anotação de anos se necessário e se tiver os dados
        if show_year_annotation and hasattr(self, "df") and "year" in self.df.columns:
            try:
                year_min = self.df["year"].min()
                year_max = self.df["year"].max()
                if pd.notna(year_min) and pd.notna(year_max):
                    base_layout.setdefault("annotations", []).append(
                        {
                            "text": f"Anos: {year_min} - {year_max}",
                            "xref": "paper",
                            "yref": "paper",
                            "x": 0.98,
                            "y": 0.98,
                            "showarrow": False,
                            "font": {"size": 12},
                        }
                    )
            except Exception as e:
                logging.warning(f"Erro ao adicionar anotação de anos: {str(e)}")

        # Atualiza com configurações adicionais fornecidas
        base_layout.update(kwargs)

        return base_layout

    def create_priority_chart(self) -> go.Figure:
        """Cria gráfico de distribuição por prioridade."""
        priority_counts = self.df.iloc[
            :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
        ].value_counts()

        fig = go.Figure(
            data=[
                go.Bar(
                    x=priority_counts.index,
                    y=priority_counts.values,
                    text=priority_counts.values,
                    textposition="auto",
                    marker_color=[
                        (
                            "#ff7f0e"
                            if x == "S3.7"
                            else "#2ca02c" if x == "S3.6" else "#1f77b4"
                        )
                        for x in priority_counts.index
                    ],
                )
            ]
        )

        fig.update_layout(
            title=f"Distribuição de SSAs por {SSAColumns.get_name(SSAColumns.GRAU_PRIORIDADE_EMISSAO)}",
            xaxis_title="Grau de Prioridade",
            yaxis_title="Quantidade",
            template="plotly_white",
        )

        return fig

    def create_sector_heatmap(self) -> go.Figure:
        """Cria heatmap de SSAs por setor emissor/executor."""
        cross_sector = pd.crosstab(
            self.df.iloc[:, SSAColumns.SETOR_EMISSOR],
            self.df.iloc[:, SSAColumns.SETOR_EXECUTOR],
        )

        fig = go.Figure(
            data=go.Heatmap(
                z=cross_sector.values,
                x=cross_sector.columns,
                y=cross_sector.index,
                colorscale="Viridis",
                text=cross_sector.values,
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False,
            )
        )

        fig.update_layout(
            title="Distribuição de SSAs entre Setores",
            xaxis_title=SSAColumns.get_name(SSAColumns.SETOR_EXECUTOR),
            yaxis_title=SSAColumns.get_name(SSAColumns.SETOR_EMISSOR),
            template="plotly_white",
        )

        return fig

    def create_timeline_chart(self) -> go.Figure:
        """Cria gráfico de linha do tempo das SSAs."""
        timeline_data = (
            self.df.groupby(self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date)
            .size()
            .reset_index()
        )
        timeline_data.columns = ["data", "quantidade"]

        fig = go.Figure(
            data=go.Scatter(
                x=timeline_data["data"],
                y=timeline_data["quantidade"],
                mode="lines+markers",
                name="SSAs Emitidas",
            )
        )

        fig.update_layout(
            title="Timeline de Emissão de SSAs",
            xaxis_title=SSAColumns.get_name(SSAColumns.EMITIDA_EM),
            yaxis_title="Quantidade de SSAs",
            template="plotly_white",
            showlegend=True,
        )

        return fig

    def create_equipment_chart(self) -> go.Figure:
        """Cria gráfico de equipamentos mais frequentes."""
        equip_counts = self.df.iloc[:, SSAColumns.EQUIPAMENTO].value_counts().head(10)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=equip_counts.values,
                    y=equip_counts.index,
                    orientation="h",
                    text=equip_counts.values,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="Top 10 Equipamentos com mais SSAs",
            xaxis_title="Quantidade de SSAs",
            yaxis_title=SSAColumns.get_name(SSAColumns.EQUIPAMENTO),
            template="plotly_white",
            height=500,  # Altura maior para acomodar os nomes
        )

        return fig

    def create_priority_timeline(self) -> go.Figure:
        """Cria gráfico de evolução das prioridades ao longo do tempo."""
        priority_by_date = pd.crosstab(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date,
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
        )

        fig = go.Figure()
        for priority in priority_by_date.columns:
            fig.add_trace(
                go.Scatter(
                    x=priority_by_date.index,
                    y=priority_by_date[priority],
                    name=priority,
                    mode="lines+markers",
                )
            )

        fig.update_layout(
            title="Evolução das Prioridades ao Longo do Tempo",
            xaxis_title="Data",
            yaxis_title="Quantidade de SSAs",
            template="plotly_white",
            showlegend=True,
        )

        return fig

    def create_sector_workload(self) -> go.Figure:
        """Cria gráfico de carga de trabalho por setor."""
        workload = (
            self.df.groupby(
                [
                    self.df.iloc[:, SSAColumns.SETOR_EXECUTOR],
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                ]
            )
            .size()
            .unstack(fill_value=0)
        )

        fig = go.Figure()
        for priority in workload.columns:
            fig.add_trace(
                go.Bar(
                    name=priority,
                    x=workload.index,
                    y=workload[priority],
                    text=workload[priority],
                    textposition="auto",
                )
            )

        fig.update_layout(
            self._get_standard_layout(
                title="Carga de Trabalho por Setor",
                xaxis_title=SSAColumns.get_name(SSAColumns.SETOR_EXECUTOR),
                yaxis_title="Quantidade de SSAs",
                x_values=workload.index,
                barmode="stack"
            )
        )

        return fig

    def create_week_chart(self, use_programmed: bool = True) -> go.Figure:
        """
        Cria gráfico de SSAs por semana.

        Args:
            use_programmed: Se True, usa semana_programada, senão usa semana_cadastro
        """
        week_info = self.week_analyzer.analyze_week_distribution()

        if week_info.empty:
            return go.Figure().update_layout(
                title="SSAs por Semana",
                annotations=[
                    {
                        "text": "Não há dados válidos disponíveis",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14},
                    }
                ],
            )

        analysis = self.week_analyzer.analyze_weeks(use_programmed)

        if analysis.empty:
            return go.Figure().update_layout(
                title="SSAs por Semana",
                annotations=[
                    {
                        "text": "Não há dados válidos disponíveis",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14},
                    }
                ],
            )

        fig = go.Figure()

        # Uma barra para cada prioridade
        for priority in analysis.columns[2:-1]:  # Exclui year, week e year_week
            fig.add_trace(
                go.Bar(
                    name=priority,
                    x=analysis["year_week"],
                    y=analysis[priority],
                    text=analysis[priority],
                    textposition="auto",
                )
            )

        title_text = (
            "SSAs Programadas por Semana"
            if use_programmed
            else "SSAs por Semana de Cadastro"
        )

        fig.update_layout(
            title=title_text,
            xaxis_title="Ano-Semana (ISO)",
            yaxis_title="Quantidade de SSAs",
            barmode="stack",
            template="plotly_white",
            showlegend=True,
            xaxis={"tickangle": -45},
            annotations=[
                {
                    "text": f"Anos: {analysis['year'].min()} - {analysis['year'].max()}",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.98,
                    "y": 0.98,
                    "showarrow": False,
                    "font": {"size": 12},
                }
            ],
        )

        return fig

    # Update the visualizer's week-related method
    def add_weeks_in_state_chart(self) -> go.Figure:
        """Cria gráfico mostrando distribuição de SSAs por tempo no estado."""
        weeks_in_state = self.week_analyzer.calculate_weeks_in_state()
        valid_weeks = weeks_in_state.dropna()

        if valid_weeks.empty:
            return go.Figure().update_layout(
                self._get_standard_layout(
                    title="Distribuição de SSAs por Tempo no Estado Atual",
                    xaxis_title="Semanas no Estado",
                    yaxis_title="Quantidade de SSAs",
                    chart_type="bar",
                    annotations=[{
                        'text': 'Não há dados válidos disponíveis',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {'size': 14}
                    }]
                )
            )

        # Agrupa em intervalos de semanas para melhor visualização
        value_counts = valid_weeks.value_counts().sort_index()
        
        # Criar bins (intervalos) para agrupar as semanas
        max_weeks = value_counts.index.max()
        if max_weeks > 50:  # Se tivermos muitas semanas, criar intervalos maiores
            bins = list(range(0, int(max_weeks) + 10, 10))  # Intervalos de 10 semanas
            labels = [f'{bins[i]}-{bins[i+1]-1}' for i in range(len(bins)-1)]
            
            # Redistribuir os dados nos novos intervalos
            binned_data = pd.cut(value_counts.index, bins=bins, labels=labels, right=False)
            value_counts = value_counts.groupby(binned_data).sum()

        fig = go.Figure([
            go.Bar(
                x=value_counts.index,
                y=value_counts.values,
                text=value_counts.values,
                textposition='auto',
                name='SSAs por Semana',
                marker_color='rgb(64, 83, 177)',  # Azul mais agradável
                hovertemplate="Intervalo: %{x}<br>SSAs: %{y}<extra></extra>"
            )
        ])

        invalid_count = weeks_in_state.isna().sum()
        total_count = len(weeks_in_state)

        fig.update_layout(
            self._get_standard_layout(
                title=f"Distribuição de SSAs por Tempo no Estado Atual<br><sub>({invalid_count}/{total_count} registros inválidos)</sub>",
                xaxis_title="Intervalo de Semanas no Estado",
                yaxis_title="Quantidade de SSAs",
                chart_type="bar",
                annotations=[{
                    'text': f"Qualidade dos dados: {((total_count-invalid_count)/total_count*100):.1f}%",
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.98,
                    'y': 0.98,
                    'showarrow': False,
                    'font': {'size': 12}
                }]
            )
        )

        # Adiciona configurações específicas para melhorar a visualização
        fig.update_layout(
            bargap=0.2,
            plot_bgcolor='white',
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                tickangle=0,  # Mantém os rótulos horizontais
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=1
            ),
            margin=dict(t=100, l=50, r=50, b=50)  # Ajusta as margens
        )

        return fig

class SSAReporter:
    """Gera relatórios detalhados das SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.visualizer = SSAVisualizer(df)

    def generate_summary_stats(self) -> Dict:
        """Gera estatísticas resumidas das SSAs."""
        try:
            # Tenta calcular média da hora, se a coluna for datetime
            emitida_em = self.df.iloc[:, SSAColumns.EMITIDA_EM]
            if pd.api.types.is_datetime64_any_dtype(emitida_em):
                tempo_medio = emitida_em.dt.hour.mean()
            else:
                tempo_medio = None
                # Remove o warning e usa um log informativo
                logging.info(
                    "Tempo médio de emissão não calculado - Algumas datas inválidas"
                )

            return {
                "total_ssas": len(self.df),
                "por_prioridade": self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                .value_counts()
                .to_dict(),
                "por_situacao": self.df.iloc[:, SSAColumns.SITUACAO]
                .value_counts()
                .to_dict(),
                "por_setor_executor": self.df.iloc[:, SSAColumns.SETOR_EXECUTOR]
                .value_counts()
                .to_dict(),
                "execucao_simples": self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES]
                .value_counts()
                .to_dict(),
                "tempo_medio_emissao": tempo_medio,
                "distribuicao_semanal": self.df.iloc[:, SSAColumns.SEMANA_CADASTRO]
                .value_counts()
                .to_dict(),
            }
        except Exception as e:
            logging.error(f"Erro ao gerar estatísticas: {e}")
            raise

    def generate_html_report(self) -> str:
        """Gera relatório em formato HTML."""
        stats = self.generate_summary_stats()

        html_content = f"""
        <html>
            <head>
                <title>Relatório de SSAs</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; }}
                    .summary {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                    .metric {{ 
                        background-color: white;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        flex: 1;
                        min-width: 200px;
                    }}
                    .chart-container {{ margin: 20px 0; }}
                    .priority-stats {{
                        margin: 20px 0;
                        padding: 15px;
                        background-color: #f8f9fa;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Relatório de Análise de SSAs</h1>
                    <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="summary">
                    <div class="metric">
                        <h3>Total de SSAs</h3>
                        <p>{stats['total_ssas']}</p>
                    </div>
                    <div class="metric">
                        <h3>Média de Emissão (hora)</h3>
                        <p>{stats['tempo_medio_emissao']:.2f}</p>
                    </div>
                </div>
                
                <div class="priority-stats">
                    <h3>Distribuição por Prioridade</h3>
                    <table>
                        <tr>
                            <th>Prioridade</th>
                            <th>Quantidade</th>
                        </tr>
                        {self._generate_priority_table_rows(stats['por_prioridade'])}
                    </table>
                </div>
                
                <div class="chart-container">
                    {self.visualizer.create_priority_chart().to_html()}
                </div>
                
                <div class="chart-container">
                    {self.visualizer.create_sector_heatmap().to_html()}
                </div>
                
                <div class="chart-container">
                    {self.visualizer.create_equipment_chart().to_html()}
                </div>
                
                <div class="chart-container">
                    {self.visualizer.create_priority_timeline().to_html()}
                </div>
            </body>
        </html>
        """
        return html_content

    def _generate_priority_table_rows(self, priority_dict: Dict) -> str:
        """Gera as linhas da tabela de prioridades em HTML."""
        return "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in priority_dict.items()
        )

    def save_excel_report(self, filename: str):
        """Gera relatório em formato Excel com múltiplas abas."""
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            workbook = writer.book
            header_format = workbook.add_format(
                {"bold": True, "bg_color": "#D3D3D3", "border": 1}
            )

            # Gera análise temporal apenas se houver datas válidas
            emitida_em = self.df.iloc[:, SSAColumns.EMITIDA_EM]
            if pd.api.types.is_datetime64_any_dtype(emitida_em) and not emitida_em.isna().all():
                try:
                    temporal_analysis = (
                        self.df.groupby(
                            [
                                emitida_em.dt.date,
                                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                            ]
                        )
                        .size()
                        .unstack(fill_value=0)
                        .reset_index()
                    )
                    temporal_analysis.to_excel(
                        writer, sheet_name="Análise Temporal", index=False
                    )
                    logging.info("Análise temporal incluída no relatório")
                except Exception as e:
                    logging.error(f"Erro ao gerar análise temporal: {str(e)}")
            else:
                logging.debug("Análise temporal não incluída devido a datas inválidas")

            try:
                # Resumo geral
                summary_df = pd.DataFrame([self.generate_summary_stats()])
                summary_df.to_excel(writer, sheet_name="Resumo", index=False)

                # Análise por prioridade
                priority_pivot = pd.pivot_table(
                    self.df,
                    values=self.df.columns[SSAColumns.NUMERO_SSA],
                    index=self.df.columns[SSAColumns.SETOR_EXECUTOR],
                    columns=self.df.columns[SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                    aggfunc="count",
                    fill_value=0,
                )
                priority_pivot.to_excel(writer, sheet_name="Por Prioridade")

                # Análise de equipamentos
                equip_analysis = (
                    self.df.groupby(self.df.columns[SSAColumns.EQUIPAMENTO])
                    .agg(
                        {
                            self.df.columns[SSAColumns.NUMERO_SSA]: "count",
                            self.df.columns[SSAColumns.GRAU_PRIORIDADE_EMISSAO]: lambda x: (
                                x.value_counts().index[0] if len(x) > 0 else "N/A"
                            ),
                        }
                    )
                    .reset_index()
                )
                equip_analysis.columns = [
                    "Equipamento",
                    "Quantidade SSAs",
                    "Prioridade Mais Comum",
                ]
                equip_analysis.to_excel(writer, sheet_name="Equipamentos", index=False)

                # Análise por status
                status_analysis = pd.crosstab(
                    [
                        self.df.iloc[:, SSAColumns.SITUACAO],
                        self.df.iloc[:, SSAColumns.SETOR_EXECUTOR]
                    ],
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                )
                status_analysis.to_excel(writer, sheet_name="Por Status")

                # Análise por responsável
                resp_analysis = pd.crosstab(
                    [
                        self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
                        self.df.iloc[:, SSAColumns.SETOR_EXECUTOR]
                    ],
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                )
                resp_analysis.to_excel(writer, sheet_name="Por Responsável")

                # Análise por serviço
                service_analysis = pd.crosstab(
                    [
                        self.df.iloc[:, SSAColumns.SERVICO_ORIGEM],
                        self.df.iloc[:, SSAColumns.SETOR_EXECUTOR]
                    ],
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                )
                service_analysis.to_excel(writer, sheet_name="Por Serviço")

                # Dados completos
                raw_data = self.df.copy()
                raw_data.to_excel(writer, sheet_name="Dados Completos", index=False)

                # Formatação das abas
                for worksheet in writer.sheets.values():
                    worksheet.set_zoom(85)  # Ajusta o zoom
                    worksheet.freeze_panes(1, 0)  # Congela primeira linha
                    
                    # Ajusta largura das colunas
                    for idx, col in enumerate(raw_data.columns):
                        series = raw_data.iloc[:, idx]
                        max_len = max(
                            series.astype(str).apply(len).max(),  # comprimento máximo dos dados
                            len(str(series.name))  # comprimento do cabeçalho
                        ) + 2  # adiciona um pequeno padding
                        worksheet.set_column(idx, idx, max_len)

                # Adiciona filtros
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    if sheet_name != "Resumo":  # Não adiciona filtro na aba de resumo
                        worksheet.autofilter(0, 0, raw_data.shape[0], raw_data.shape[1] - 1)

            except Exception as e:
                logging.error(f"Erro ao gerar análises específicas: {str(e)}")
                logging.error(traceback.format_exc())

            try:
                # Adiciona uma aba de metadados com tratamento de datas nulas
                valid_dates = emitida_em[emitida_em.notna()]
                
                if not valid_dates.empty:
                    data_inicio = valid_dates.min().strftime('%d/%m/%Y')
                    data_fim = valid_dates.max().strftime('%d/%m/%Y')
                    periodo = f"{data_inicio} a {data_fim}"
                else:
                    periodo = "Período não disponível"

                metadata = pd.DataFrame([
                    {"Métrica": "Total de SSAs", "Valor": len(self.df)},
                    {"Métrica": "Data de Geração", "Valor": datetime.now().strftime("%d/%m/%Y %H:%M:%S")},
                    {"Métrica": "SSAs por Prioridade", "Valor": dict(self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].value_counts())},
                    {"Métrica": "SSAs por Status", "Valor": dict(self.df.iloc[:, SSAColumns.SITUACAO].value_counts())},
                    {"Métrica": "Período Analisado", "Valor": periodo}
                ])
                metadata.to_excel(writer, sheet_name="Metadados", index=False)

            except Exception as e:
                logging.error(f"Erro ao gerar metadados: {str(e)}")
                logging.debug(traceback.format_exc())

            # Aplica formatação final
            try:
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    worksheet.set_column('A:ZZ', None, None, {'text_wrap': True})  # Habilita wrap de texto
                    
                    # Ajusta zoom e visualização
                    worksheet.set_zoom(85)
                    if sheet_name == "Dados Completos":
                        worksheet.freeze_panes(1, 2)  # Congela primeira linha e duas colunas
                    else:
                        worksheet.freeze_panes(1, 0)  # Congela apenas primeira linha

            except Exception as e:
                logging.error(f"Erro ao aplicar formatação final: {str(e)}")

            logging.info(f"Relatório Excel salvo com sucesso em: {filename}")
 
    def generate_pdf_report(self, filename: str):
        """Gera relatório em PDF."""
        import pdfkit  # Requer wkhtmltopdf instalado

        html_content = self.generate_html_report()
        pdfkit.from_string(html_content, filename)

    def generate_summary_report(self) -> str:
        """Gera um relatório resumido em texto."""
        stats = self.generate_summary_stats()

        return f"""
RELATÓRIO RESUMIDO DE SSAs - {datetime.now().strftime('%d/%m/%Y')}

Total de SSAs: {stats['total_ssas']}

DISTRIBUIÇÃO POR PRIORIDADE:
{self._format_dict(stats['por_prioridade'])}

DISTRIBUIÇÃO POR SETOR EXECUTOR:
{self._format_dict(stats['por_setor_executor'])}

EXECUÇÃO SIMPLES:
{self._format_dict(stats['execucao_simples'])}

Tempo Médio de Emissão (hora): {stats['tempo_medio_emissao']:.2f}
        """

    def _format_dict(self, d: Dict) -> str:
        """Formata um dicionário para exibição em texto."""
        return "\n".join(f"- {k}: {v}" for k, v in d.items())


class KPICalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def calculate_efficiency_metrics(self) -> Dict:
        """Calcula métricas de eficiência."""
        return {
            "taxa_programacao": len(
                self.df[self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()]
            )
            / len(self.df),
            "taxa_execucao_simples": len(
                self.df[self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Sim"]
            )
            / len(self.df),
            "distribuicao_prioridade": self.df.iloc[
                :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
            ]
            .value_counts(normalize=True)
            .to_dict(),
        }

    def get_overall_health_score(self) -> float:
        """Calcula um score geral de saúde do sistema."""
        metrics = self.calculate_efficiency_metrics()
        score = (
            metrics["taxa_programacao"] * 0.5 + metrics["taxa_execucao_simples"] * 0.5
        )
        return round(score * 100, 2)


class SSADashboard:
    """Dashboard interativo para análise de SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.visualizer = SSAVisualizer(df)
        self.kpi_calc = KPICalculator(df)
        # Podemos usar o week_analyzer do visualizer ao invés de criar um novo
        self.week_analyzer = self.visualizer.week_analyzer
        self.setup_layout()
        self.setup_callbacks()

    def setup_callbacks(self):
        @self.app.callback(
            [
                Output("resp-summary-cards", "children"),
                Output("resp-prog-chart", "figure"),
                Output("resp-exec-chart", "figure"),
                Output("programmed-week-chart", "figure"),
                Output("registration-week-chart", "figure"),
                Output("detail-section", "style"),
                Output("detail-state-chart", "figure"),
                Output("detail-week-chart", "figure"),
                Output("ssa-table", "data"),
                Output("weeks-in-state-chart", "figure"),
            ],
            [Input("resp-prog-filter", "value"), Input("resp-exec-filter", "value")],
        )
        def update_all_charts(resp_prog, resp_exec):
            df_filtered = self.df.copy()
            if resp_prog:
                df_filtered = df_filtered[
                    df_filtered.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp_prog
                ]
            if resp_exec:
                df_filtered = df_filtered[
                    df_filtered.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp_exec
                ]

            # Criar visualizador filtrado
            filtered_visualizer = SSAVisualizer(df_filtered)

            # Criar os cards de resumo
            resp_cards = self._create_resp_summary_cards(df_filtered)

            # Gerar gráficos
            fig_prog = self._create_resp_prog_chart(df_filtered)
            fig_exec = self._create_resp_exec_chart(df_filtered)
            fig_programmed_week = filtered_visualizer.create_week_chart(
                use_programmed=True
            )
            fig_registration_week = filtered_visualizer.create_week_chart(
                use_programmed=False
            )
            detail_style = (
                {"display": "block"} if resp_prog or resp_exec else {"display": "none"}
            )
            fig_detail_state = self._create_detail_state_chart(df_filtered)
            fig_detail_week = filtered_visualizer.create_week_chart()
            table_data = self._prepare_table_data(df_filtered)
            weeks_fig = filtered_visualizer.add_weeks_in_state_chart()

            return (
                resp_cards,
                fig_prog,
                fig_exec,
                fig_programmed_week,
                fig_registration_week,
                detail_style,
                fig_detail_state,
                fig_detail_week,
                table_data,
                weeks_fig,
            )

    def _get_state_counts(self):
        """Obtém contagem de SSAs por estado."""
        return self.df.iloc[:, SSAColumns.SITUACAO].value_counts().to_dict()

    def _get_programmed_by_week(self):
        """Obtém SSAs programadas por semana usando o analisador central."""
        week_info = self.week_analyzer.analyze_week_distribution()
        if not week_info.empty and "week_count" in week_info:
            return week_info["week_count"]
        return pd.Series()  # Retorna série vazia se não houver dados

    def _get_responsaveis(self):
        """Obtém lista de responsáveis únicos."""
        prog = self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].unique()
        exec_ = self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].unique()
        return {
            "programacao": sorted([x for x in prog if pd.notna(x) and x != ""]),
            "execucao": sorted([x for x in exec_ if pd.notna(x) and x != ""]),
        }

    def setup_layout(self):
        """Define o layout do dashboard."""
        stats = self._get_initial_stats()
        state_counts = self._get_state_counts()

        self.app.layout = dbc.Container(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            html.H1("Dashboard de SSAs Pendentes", className="text-primary mb-4"),
                            width=12,
                        )
                    ]
                ),
                # Filtros
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Responsável Programação:"),
                                dcc.Dropdown(
                                    id="resp-prog-filter",
                                    options=[
                                        {"label": resp, "value": resp}
                                        for resp in self._get_responsaveis()["programacao"]
                                    ],
                                    placeholder="Selecione um responsável...",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Responsável Execução:"),
                                dcc.Dropdown(
                                    id="resp-exec-filter",
                                    options=[
                                        {"label": resp, "value": resp}
                                        for resp in self._get_responsaveis()["execucao"]
                                    ],
                                    placeholder="Selecione um responsável...",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                # Cards de Estado
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("SSAs por Estado", className="mb-3"),
                                self._create_state_cards(state_counts),
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Cards de resumo por estado - versão compacta
                html.Div(id="resp-summary-cards", className="mb-4"),
                # Gráfico de tempo no estado atual
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Tempo no Estado Atual"),
                                        dbc.CardBody(
                                            dcc.Graph(id="weeks-in-state-chart")
                                        ),
                                    ]
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Gráficos por Responsável
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "SSAs por Responsável na Programação"
                                        ),
                                        dbc.CardBody(dcc.Graph(id="resp-prog-chart")),
                                    ]
                                )
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "SSAs por Responsável na Execução"
                                        ),
                                        dbc.CardBody(dcc.Graph(id="resp-exec-chart")),
                                    ]
                                )
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-4",
                ),
                # Gráficos de Semana
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("SSAs Programadas por Semana"),
                                        dbc.CardBody(dcc.Graph(id="programmed-week-chart")),
                                    ]
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("SSAs por Semana de Cadastro"),
                                        dbc.CardBody(dcc.Graph(id="registration-week-chart")),
                                    ]
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Seção de detalhamento
                html.Div(
                    [
                        html.H4("Detalhamento por Responsável", className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    "SSAs Pendentes por Estado"
                                                ),
                                                dbc.CardBody(
                                                    dcc.Graph(id="detail-state-chart")
                                                ),
                                            ]
                                        )
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    "SSAs Programadas por Semana"
                                                ),
                                                dbc.CardBody(
                                                    dcc.Graph(id="detail-week-chart")
                                                ),
                                            ]
                                        )
                                    ],
                                    width=6,
                                ),
                            ],
                            className="mb-4",
                        ),
                    ],
                    id="detail-section",
                    style={"display": "none"},
                ),
                # Tabela de SSAs
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Lista de SSAs"),
                                        dbc.CardBody(
                                            dash_table.DataTable(
                                                id="ssa-table",
                                                columns=[
                                                    {"name": "Número", "id": "numero"},
                                                    {"name": "Estado", "id": "estado"},
                                                    {
                                                        "name": "Resp. Prog.",
                                                        "id": "resp_prog",
                                                    },
                                                    {
                                                        "name": "Resp. Exec.",
                                                        "id": "resp_exec",
                                                    },
                                                    {
                                                        "name": "Semana Prog.",
                                                        "id": "semana_prog",
                                                    },
                                                    {
                                                        "name": "Prioridade",
                                                        "id": "prioridade",
                                                    },
                                                ],
                                                data=self._prepare_table_data(),
                                                page_size=10,
                                                style_table={"overflowX": "auto"},
                                                style_cell={"textAlign": "left"},
                                                style_header={
                                                    "backgroundColor": "rgb(230, 230, 230)",
                                                    "fontWeight": "bold",
                                                },
                                            )
                                        ),
                                    ]
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
            ],
            fluid=True,
            className="p-4",
        )

    def _create_state_cards(self, state_counts):
        """Cria cards para cada estado de SSA."""
        cards = [
            # Label "Setor:"
            dbc.Col(
                html.H6("Setor:", className="mt-3 me-2"),
                width="auto"
            )
        ]
        
        # Calcula o total e adiciona como primeiro card
        total_ssas = sum(state_counts.values())
        cards.append(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H6("TOTAL", className="card-title text-center mb-0 small"),
                                html.H3(
                                    str(total_ssas), 
                                    className="text-center text-danger fw-bold mb-0",
                                    style={"fontSize": "1.8rem"}  # Texto um pouco maior
                                ),
                            ],
                            className="p-2"  # Menos padding
                        )
                    ],
                    className="mb-3",
                    style={
                        "height": "80px",
                        "border-left": "4px solid red",
                        "width": "150px"  # Largura um pouco maior
                    },
                ),
                width="auto"
            )
        )
        
        # Lista ordenada de estados
        state_list = ['AAD', 'ADM', 'AAT', 'SPG', 'AIM', 'APV', 'APG', 'SCD', 'ADI', 'APL']
        
        # Adiciona os cards de estado na ordem definida
        for state in state_list:
            count = state_counts.get(state, 0)
            cards.append(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6(state, className="card-title text-center mb-0 small"),
                                    html.H3(
                                        str(count), 
                                        className="text-center text-primary mb-0",
                                        style={"fontSize": "1.8rem"}  # Texto um pouco maior
                                    ),
                                ],
                                className="p-2"  # Menos padding
                            )
                        ],
                        className="mb-3",
                        style={
                            "height": "80px",
                            "width": "150px"  # Largura um pouco maior
                        },
                    ),
                    width="auto"
                )
            )
        
        return dbc.Row(
            cards,
            className="g-2 flex-nowrap align-items-center"  # Alinhamento vertical centralizado
        )

    def _create_resp_summary_cards(self, df_filtered):
        """Cria cards compactos para totais por estado."""
        state_counts = df_filtered.iloc[:, SSAColumns.SITUACAO].value_counts()
        total_count = len(df_filtered)

        cards = [
            # Label "Usuário:"
            dbc.Col(
                html.H6("User:", className="mt-2 me-2"),
                width="auto",
                style={"display": "flex", "alignItems": "center"}
            ),
            # Card de Total
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            "TOTAL",
                                            className="small text-muted",
                                            style={
                                                "lineHeight": "1",
                                                "marginBottom": "4px"
                                            }
                                        ),
                                        html.Div(
                                            str(total_count),
                                            className="h5 m-0 text-danger fw-bold",
                                            style={"lineHeight": "1"}
                                        )
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "justifyContent": "center",
                                        "alignItems": "center",
                                        "height": "100%"
                                    }
                                )
                            ],
                            className="p-2",
                            style={"height": "100%"}
                        )
                    ],
                    className="mb-2",
                    style={
                        "height": "50px",
                        "borderLeft": "4px solid red",
                        "width": "110px",
                        "display": "flex",
                        "alignItems": "center"
                    }
                ),
                width="auto"
            )
        ]

        # Lista ordenada de estados
        state_list = ['AAD', 'ADM', 'AAT', 'SPG', 'AIM', 'APV', 'APG', 'SCD', 'ADI', 'APL']
        
        # Um card para cada estado
        for state in state_list:
            count = state_counts.get(state, 0)
            cards.append(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                state,
                                                className="small text-muted",
                                                style={
                                                    "lineHeight": "1",
                                                    "marginBottom": "4px"
                                                }
                                            ),
                                            html.Div(
                                                str(count),
                                                className="h5 m-0 text-primary",
                                                style={"lineHeight": "1"}
                                            )
                                        ],
                                        style={
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "justifyContent": "center",
                                            "alignItems": "center",
                                            "height": "100%"
                                        }
                                    )
                                ],
                                className="p-2",
                                style={"height": "100%"}
                            )
                        ],
                        className="mb-2",
                        style={
                            "height": "50px",
                            "width": "110px",
                            "display": "flex",
                            "alignItems": "center"
                        }
                    ),
                    width="auto"
                )
            )

        return dbc.Row(
            cards,
            className="mb-3 g-2 flex-nowrap align-items-center",
            justify="start",
            style={"display": "flex", "alignItems": "center"}
        )

    def _prepare_table_data(self):
        """Prepara dados para a tabela."""
        return [
            {
                "numero": row.iloc[SSAColumns.NUMERO_SSA],
                "estado": row.iloc[SSAColumns.SITUACAO],
                "resp_prog": row.iloc[SSAColumns.RESPONSAVEL_PROGRAMACAO],
                "resp_exec": row.iloc[SSAColumns.RESPONSAVEL_EXECUCAO],
                "semana_prog": row.iloc[SSAColumns.SEMANA_PROGRAMADA],
                "prioridade": row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO],
            }
            for idx, row in self.df.iterrows()
        ]

    def _create_resp_prog_chart(self, df):
        """Cria o gráfico de responsáveis na programação."""
        resp_prog_counts = df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].value_counts()

        fig = go.Figure(
            data=[
                go.Bar(
                    x=resp_prog_counts.index,
                    y=resp_prog_counts.values,
                    text=resp_prog_counts.values,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            self.visualizer._get_standard_layout(  # Use o visualizer aqui
                title="SSAs por Responsável na Programação",
                xaxis_title="Responsável",
                yaxis_title="Quantidade",
                chart_type="bar",
            )
        )

        return fig

    def _create_resp_exec_chart(self, df):
        """Cria o gráfico de responsáveis na execução."""
        resp_exec_counts = df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].value_counts()

        fig = go.Figure(data=[
            go.Bar(
                x=resp_exec_counts.index,
                y=resp_exec_counts.values,
                text=resp_exec_counts.values,
                textposition="auto"
            )
        ])

        fig.update_layout(
            self.visualizer._get_standard_layout(  # Use o visualizer aqui
                title="SSAs por Responsável na Execução",
                xaxis_title="Responsável",
                yaxis_title="Quantidade",
                chart_type="bar"
            )
        )

        return fig

    def create_week_chart(self, use_programmed: bool = True) -> go.Figure:
        """
        Cria gráfico de SSAs por semana.

        Args:
            use_programmed: Se True, usa semana_programada, senão usa semana_cadastro
        """
        week_info = self.week_analyzer.analyze_week_distribution()

        if week_info.empty:
            return go.Figure().update_layout(
                title="SSAs por Semana",
                annotations=[
                    {
                        "text": "Não há dados válidos disponíveis",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14},
                    }
                ],
            )

        analysis = self.week_analyzer.analyze_weeks(use_programmed)

        if analysis.empty:
            return go.Figure().update_layout(
                title="SSAs por Semana",
                annotations=[
                    {
                        "text": "Não há dados válidos disponíveis",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14},
                    }
                ],
            )

        fig = go.Figure()

        # Uma barra para cada prioridade
        for priority in analysis.columns[2:-1]:  # Exclui year, week e year_week
            fig.add_trace(
                go.Bar(
                    name=priority,
                    x=analysis["year_week"],
                    y=analysis[priority],
                    text=analysis[priority],
                    textposition="auto",
                )
            )

        title_text = (
            "SSAs Programadas por Semana"
            if use_programmed
            else "SSAs por Semana de Cadastro"
        )

        fig.update_layout(
            title=title_text,
            xaxis_title="Ano-Semana (ISO)",
            yaxis_title="Quantidade de SSAs",
            barmode="stack",
            template="plotly_white",
            showlegend=True,
            xaxis={"tickangle": -45},
            annotations=[
                {
                    "text": f"Anos: {analysis['year'].min()} - {analysis['year'].max()}",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.98,
                    "y": 0.98,
                    "showarrow": False,
                    "font": {"size": 12},
                }
            ],
        )

        return fig

    def create_registration_week_chart(self) -> go.Figure:
        """
        Cria gráfico específico para SSAs por semana de cadastro.
        Wrapper para create_week_chart com use_programmed=False
        """
        return self.create_week_chart(use_programmed=False)

    def _create_detail_week_chart(self, df):
        """Cria o gráfico de detalhamento por semana usando o visualizador."""
        # Aqui já estamos usando o visualizador corretamente
        filtered_visualizer = SSAVisualizer(df)
        return filtered_visualizer.create_week_chart(
            use_programmed=True
        )

    def _create_detail_state_chart(self, df):
        """Cria o gráfico de detalhamento por estado."""
        state_counts = df.iloc[:, SSAColumns.SITUACAO].value_counts()

        fig = go.Figure(data=[
            go.Bar(
                x=state_counts.index,
                y=state_counts.values,
                text=state_counts.values,
                textposition="auto"
            )
        ])

        fig.update_layout(
            self.visualizer._get_standard_layout(  # Use o visualizer aqui
                title="SSAs Pendentes por Estado",
                xaxis_title="Estado",
                yaxis_title="Quantidade",
                chart_type="bar"
            )
        )

        return fig

    def _prepare_table_data(self, df=None):
        """Prepara dados para a tabela."""
        if df is None:
            df = self.df
        return [
            {
                "numero": row.iloc[SSAColumns.NUMERO_SSA],
                "estado": row.iloc[SSAColumns.SITUACAO],
                "resp_prog": row.iloc[SSAColumns.RESPONSAVEL_PROGRAMACAO],
                "resp_exec": row.iloc[SSAColumns.RESPONSAVEL_EXECUCAO],
                "semana_prog": row.iloc[SSAColumns.SEMANA_PROGRAMADA],
                "prioridade": row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO],
            }
            for idx, row in df.iterrows()
        ]

    def run_server(self, debug=True, port=8080):
        """Inicia o servidor do dashboard."""
        self.app.run_server(debug=debug, port=port, host='0.0.0.0')

    def _get_initial_stats(self):
        """Calcula estatísticas iniciais para o dashboard."""
        try:
            # Estatísticas básicas
            total_ssas = len(self.df)

            # Estatísticas de prioridade
            prioridades = self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].value_counts()
            ssas_criticas = len(
                self.df[
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].str.upper()
                    == "S3.7"
                ]
            )
            taxa_criticidade = (ssas_criticas / total_ssas * 100) if total_ssas > 0 else 0

            # Estatísticas de setor e estado
            setores = self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].value_counts()
            estados = self.df.iloc[:, SSAColumns.SITUACAO].value_counts()

            # Tratamento seguro das datas
            datas = self.df.iloc[:, SSAColumns.EMITIDA_EM]
            valid_dates = datas[datas.notna()]

            periodo = {}
            if not valid_dates.empty:
                try:
                    data_mais_antiga = valid_dates.min()
                    data_mais_recente = valid_dates.max()
                    periodo = {
                        "inicio": (
                            data_mais_antiga.strftime("%d/%m/%Y")
                            if pd.notna(data_mais_antiga)
                            else "N/A"
                        ),
                        "fim": (
                            data_mais_recente.strftime("%d/%m/%Y")
                            if pd.notna(data_mais_recente)
                            else "N/A"
                        ),
                    }
                except Exception as e:
                    logging.error(f"Erro ao processar datas para período: {str(e)}")
                    periodo = {"inicio": "N/A", "fim": "N/A"}
            else:
                periodo = {"inicio": "N/A", "fim": "N/A"}

            # Estatísticas de responsáveis
            responsaveis = {
                "programacao": self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO]
                .replace([None, ""], np.nan)
                .dropna()
                .nunique(),
                "execucao": self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
                .replace([None, ""], np.nan)
                .dropna()
                .nunique(),
            }

            return {
                "total": total_ssas,
                "criticas": ssas_criticas,
                "taxa_criticidade": taxa_criticidade,
                "por_prioridade": prioridades,
                "por_setor": setores,
                "por_estado": estados,
                "periodo": periodo,
                "responsaveis": responsaveis,
            }

        except Exception as e:
            logging.error(f"Erro ao calcular estatísticas iniciais: {str(e)}")
            # Retorna estatísticas vazias em caso de erro
            return {
                "total": 0,
                "criticas": 0,
                "taxa_criticidade": 0,
                "por_prioridade": pd.Series(),
                "por_setor": pd.Series(),
                "por_estado": pd.Series(),
                "periodo": {"inicio": "N/A", "fim": "N/A"},
                "responsaveis": {"programacao": 0, "execucao": 0},
            }


def check_dependencies():
    """Verifica e instala dependências necessárias."""
    try:
        import xlsxwriter
    except ImportError:
        logging.warning("xlsxwriter não encontrado. Tentando instalar...")
        import subprocess

        subprocess.check_call(["pip", "install", "xlsxwriter"])
        logging.info("xlsxwriter instalado com sucesso")

def diagnose_dates(df, date_column_index):
    """
    Diagnostica problemas com datas em um DataFrame.
    
    Args:
        df: DataFrame com os dados
        date_column_index: índice da coluna de data
    
    Returns:
        Dict com informações de diagnóstico
    """
    problematic_rows = []
    
    for idx, row in df.iterrows():
        date_value = row.iloc[date_column_index]
        try:
            if pd.isna(date_value):
                problematic_rows.append({
                    'index': idx,
                    'value': date_value,
                    'reason': 'Valor nulo ou NaN',
                    'row_data': row.to_dict()
                })
            elif isinstance(date_value, str):
                # Tenta converter para verificar se é uma data válida
                pd.to_datetime(date_value)
        except Exception as e:
            problematic_rows.append({
                'index': idx,
                'value': date_value,
                'reason': str(e),
                'row_data': row.to_dict()
            })
    
    return {
        'total_rows': len(df),
        'problematic_rows': problematic_rows,
        'error_count': len(problematic_rows)
    }


if __name__ == "__main__":
    check_dependencies()
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("ssa_analysis.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    try:
        # Carrega os dados
        logger.info("Iniciando carregamento dos dados...")
        # Lugar do carregamento do arquivo .xlsx com os dados do scrP
        loader = DataLoader(DATA_FILE_PATH)
        
        # metodo antigo abaixo com caminho direto 
        # loader = DataLoader(r"C:\Users\menon\git\trabalho\SCRAP-SAM\Downloads\SSAs Pendentes Geral - 28-10-2024_1221PM.xlsx")
        
        df = loader.load_data()
        logger.info(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")

        # Exemplo de uso dos objetos SSAData
        ssas = loader.get_ssa_objects()
        logger.info(f"Convertidos {len(ssas)} registros para objetos SSAData")

        # Exemplo de filtragem
        ssas_alta_prioridade = loader.filter_ssas(prioridade="S3.7")
        logger.info(f"Total de SSAs com alta prioridade: {len(ssas_alta_prioridade)}")

        # Gera relatório inicial
        logger.info("Gerando relatório inicial...")
        reporter = SSAReporter(df)
        reporter.save_excel_report("relatorio_ssas.xlsx")
        logger.info("Relatório Excel gerado com sucesso.")

        # Inicia o dashboard
        logger.info("Iniciando dashboard...")
        dashboard = SSADashboard(df)
        dashboard.run_server(debug=True, port=8080)

    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}")
        logger.error(traceback.format_exc())
        raise
