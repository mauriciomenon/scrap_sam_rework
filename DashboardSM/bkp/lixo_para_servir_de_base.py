# Imports padrão Python
from dataclasses import dataclass
from datetime import datetime
import time
import threading
import thread
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import warnings
import logging
import traceback
from io import BytesIO
import os
import json
import psutil
import schedule
import yaml  

# Imports de análise de dados
import pandas as pd
import numpy as np

# Imports de visualização
import plotly.express as px
import plotly.graph_objects as go

# Imports do Dash
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Imports de exportação
import xlsxwriter
import pdfkit

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

# Configurações globais
warnings.filterwarnings("ignore")

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

# Constantes globais
VERSION = "1.0.0"
DEFAULT_PORT = 8050
DEFAULT_HOST = "0.0.0.0"


@dataclass
class SSAData:
    """
    Estrutura de dados para uma SSA.

    Attributes:
        numero (str): Número identificador da SSA
        situacao (str): Estado atual da SSA
        derivada (Optional[str]): Número da SSA de origem, se for derivada
        localizacao (str): Código da localização
        desc_localizacao (str): Descrição da localização
        equipamento (str): Código do equipamento
        semana_cadastro (str): Semana de cadastro da SSA
        emitida_em (datetime): Data e hora de emissão
        descricao (str): Descrição detalhada da SSA
        setor_emissor (str): Setor que emitiu a SSA
        setor_executor (str): Setor responsável pela execução
        solicitante (str): Nome do solicitante
        servico_origem (str): Serviço que originou a SSA
        prioridade_emissao (str): Prioridade definida na emissão
        prioridade_planejamento (Optional[str]): Prioridade definida no planejamento
        execucao_simples (str): Indicador de execução simples
        responsavel_programacao (Optional[str]): Responsável pela programação
        semana_programada (Optional[str]): Semana programada para execução
        responsavel_execucao (Optional[str]): Responsável pela execução
        descricao_execucao (Optional[str]): Descrição da execução
        sistema_origem (str): Sistema onde a SSA foi gerada
        anomalia (Optional[str]): Código da anomalia relacionada
    """
    self.numero = str(data.get('NUMERO', ''))
    self.emissao = self._parse_date(data.get('EMITIDA_EM', ''))
    self.prioridade = str(data.get('PRIORIDADE', ''))
    self.status = str(data.get('STATUS', ''))
    self.descricao = str(data.get('DESCRICAO', ''))
    self.origem = str(data.get('ORIGEM', ''))
    self.responsavel = str(data.get('RESPONSAVEL', ''))
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
        """
        Converte o objeto para dicionário.

        Returns:
            Dict: Dicionário com os principais atributos da SSA
        """
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

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if pd.isna(date_str):
            return None
        try:
            if isinstance(date_str, datetime):
                return date_str
            return pd.to_datetime(date_str)
        except Exception as e:
            logging.warning(f"Erro ao converter data: {date_str}. Erro: {str(e)}")
            return None


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
        """
        Retorna o nome da coluna pelo índice.

        Args:
            index (int): Índice da coluna

        Returns:
            str: Nome de exibição da coluna ou nome genérico se não encontrado
        """
        return cls.COLUMN_NAMES.get(index, f"Coluna {index}")


class SSAAnalyzer:
    """Análise específica para os dados de SSA."""

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o analisador com um DataFrame.

        Args:
            df (pd.DataFrame): DataFrame contendo os dados das SSAs
        """
        self.df = df

    def analyze_by_priority(self) -> Dict:
        """
        Analisa SSAs por grau de prioridade.

        Returns:
            Dict: Dicionário com estatísticas por prioridade
        """
        priority_stats = {
            "count_by_priority": self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            .value_counts()
            .to_dict(),
            "sectors_by_priority": self.df.groupby(
                [
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                    self.df.iloc[:, SSAColumns.SETOR_EXECUTOR],
                ]
            )
            .size()
            .unstack(fill_value=0)
            .to_dict(),
            "equipment_by_priority": self.df.groupby(
                [
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                    self.df.iloc[:, SSAColumns.EQUIPAMENTO],
                ]
            )
            .size()
            .unstack(fill_value=0)
            .to_dict(),
        }
        return priority_stats

    def analyze_by_sector(self) -> Dict:
        """
        Analisa distribuição de SSAs por setor.

        Returns:
            Dict: Dicionário com estatísticas por setor
        """
        sector_stats = {
            "emissor": self.df.iloc[:, SSAColumns.SETOR_EMISSOR]
            .value_counts()
            .to_dict(),
            "executor": self.df.iloc[:, SSAColumns.SETOR_EXECUTOR]
            .value_counts()
            .to_dict(),
            "cross_sector": pd.crosstab(
                self.df.iloc[:, SSAColumns.SETOR_EMISSOR],
                self.df.iloc[:, SSAColumns.SETOR_EXECUTOR],
            ).to_dict(),
        }
        return sector_stats

    def analyze_execution_status(self) -> Dict:
        """
        Analisa status de execução das SSAs.

        Returns:
            Dict: Dicionário com estatísticas de execução
        """
        execution_stats = {
            "simple_execution": self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES]
            .value_counts()
            .to_dict(),
            "by_week": self.df.iloc[:, SSAColumns.SEMANA_CADASTRO]
            .value_counts()
            .to_dict(),
            "programmed_vs_total": {
                "programmed": self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA]
                .notna()
                .sum(),
                "total": len(self.df),
            },
        }
        return execution_stats

    def analyze_priority_trends(self) -> pd.DataFrame:
        """
        Analisa tendências de prioridade ao longo do tempo.

        Returns:
            pd.DataFrame: DataFrame com tendências temporais das prioridades
        """
        return pd.crosstab(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date,
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
        ).reset_index()

    def analyze_workload(self) -> pd.DataFrame:
        """
        Analisa carga de trabalho por setor/responsável.

        Returns:
            pd.DataFrame: DataFrame com análise de carga de trabalho
        """
        return pd.crosstab(
            [
                self.df.iloc[:, SSAColumns.SETOR_EXECUTOR],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ],
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
        ).reset_index()


class SSAVisualizer:
    """Gera visualizações específicas para SSAs."""

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o visualizador com um DataFrame.

        Args:
            df (pd.DataFrame): DataFrame contendo os dados das SSAs
        """
        self.df = df

    def create_priority_chart(self) -> go.Figure:
        """
        Cria gráfico de distribuição por prioridade.

        Returns:
            go.Figure: Gráfico de barras das SSAs por prioridade
        """
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
        """
        Cria heatmap de SSAs por setor emissor/executor.

        Returns:
            go.Figure: Heatmap da distribuição de SSAs entre setores
        """
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
        """
        Cria gráfico de linha do tempo das SSAs.

        Returns:
            go.Figure: Gráfico de linha temporal das SSAs
        """
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
        """
        Cria gráfico de equipamentos mais frequentes.

        Returns:
            go.Figure: Gráfico de barras horizontais dos equipamentos mais frequentes
        """
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
            height=500,
        )

        return fig

    def create_priority_timeline(self) -> go.Figure:
        """
        Cria gráfico de evolução das prioridades ao longo do tempo.

        Returns:
            go.Figure: Gráfico de linha temporal por prioridade
        """
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
        """
        Cria gráfico de carga de trabalho por setor.

        Returns:
            go.Figure: Gráfico de barras empilhadas da carga de trabalho setorial
        """
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
            title="Carga de Trabalho por Setor",
            xaxis_title=SSAColumns.get_name(SSAColumns.SETOR_EXECUTOR),
            yaxis_title="Quantidade de SSAs",
            barmode="stack",
            template="plotly_white",
        )

        return fig


class SSAReporter:
    """Gera relatórios detalhados das SSAs."""

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o gerador de relatórios com um DataFrame.

        Args:
            df (pd.DataFrame): DataFrame contendo os dados das SSAs
        """
        self.df = df
        self.visualizer = SSAVisualizer(df)

    def generate_summary_stats(self) -> Dict:
        """
        Gera estatísticas resumidas das SSAs.

        Returns:
            Dict: Dicionário com estatísticas principais
        """
        try:
            # Tenta calcular média da hora, se a coluna for datetime
            emitida_em = self.df.iloc[:, SSAColumns.EMITIDA_EM]
            if pd.api.types.is_datetime64_any_dtype(emitida_em):
                tempo_medio = emitida_em.dt.hour.mean()
            else:
                tempo_medio = None
                logging.warning("Coluna EMITIDA_EM não está em formato datetime")

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
        """
        Gera relatório em formato HTML.

        Returns:
            str: Conteúdo HTML do relatório
        """
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

    def save_excel_report(self, filename: str):
        """
        Gera relatório em formato Excel com múltiplas abas.

        Args:
            filename (str): Nome do arquivo Excel a ser gerado
        """
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            workbook = writer.book
            header_format = workbook.add_format(
                {"bold": True, "bg_color": "#D3D3D3", "border": 1}
            )

            # Gera análise temporal
            emitida_em = self.df.iloc[:, SSAColumns.EMITIDA_EM]
            if pd.api.types.is_datetime64_any_dtype(emitida_em):
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
            else:
                logging.warning("Análise temporal ignorada - coluna de data inválida")

            # Resumo
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

    def generate_pdf_report(self, filename: str):
        """
        Gera relatório em PDF.

        Args:
            filename (str): Nome do arquivo PDF a ser gerado
        """
        import pdfkit

        html_content = self.generate_html_report()
        pdfkit.from_string(html_content, filename)

    def generate_summary_report(self) -> str:
        """
        Gera um relatório resumido em texto.

        Returns:
            str: Texto do relatório resumido
        """
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

    def _generate_priority_table_rows(self, priority_dict: Dict) -> str:
        """
        Gera as linhas da tabela de prioridades em HTML.

        Args:
            priority_dict (Dict): Dicionário com contagens por prioridade

        Returns:
            str: HTML das linhas da tabela
        """
        return "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in priority_dict.items()
        )

    def _format_dict(self, d: Dict) -> str:
        """
        Formata um dicionário para exibição em texto.

        Args:
            d (Dict): Dicionário a ser formatado

        Returns:
            str: Texto formatado
        """
        return "\n".join(f"- {k}: {v}" for k, v in d.items())


class DashboardTheme:
    """Configurações de tema para o dashboard."""

    # Cores principais
    COLORS = {
        "primary": "#0d6efd",  # Azul principal
        "secondary": "#6c757d",  # Cinza secundário
        "success": "#198754",  # Verde sucesso
        "danger": "#dc3545",  # Vermelho perigo
        "warning": "#ffc107",  # Amarelo alerta
        "info": "#0dcaf0",  # Azul informação
        "light": "#f8f9fa",  # Cinza claro
        "dark": "#212529",  # Cinza escuro
    }

    # Cores para estados de SSA
    STATE_COLORS = {
        "ADM": "#dc3545",  # vermelho para estados administrativos
        "STE": "#0d6efd",  # azul para estados técnicos
        "AAT": "#198754",  # verde para estados de atendimento
        "default": "#6c757d",  # cinza para outros estados
    }

    # Cores para prioridades
    PRIORITY_COLORS = {
        "S3.7": "#dc3545",  # Vermelho para prioridade alta
        "S3.6": "#ffc107",  # Amarelo para prioridade média
        "S3.5": "#198754",  # Verde para prioridade baixa
        "default": "#6c757d",  # Cinza para outras prioridades
    }

    @classmethod
    def get_state_color(cls, state: str) -> str:
        """
        Retorna a cor apropriada para um estado.

        Args:
            state (str): Estado da SSA

        Returns:
            str: Código de cor hexadecimal
        """
        for key in cls.STATE_COLORS.keys():
            if key in state:
                return cls.STATE_COLORS[key]
        return cls.STATE_COLORS["default"]

    @classmethod
    def get_priority_color(cls, priority: str) -> str:
        """
        Retorna a cor apropriada para uma prioridade.

        Args:
            priority (str): Código de prioridade

        Returns:
            str: Código de cor hexadecimal
        """
        return cls.PRIORITY_COLORS.get(priority, cls.PRIORITY_COLORS["default"])

    @classmethod
    def get_trend_color(cls, value: float) -> str:
        """
        Retorna a cor apropriada para um valor de tendência.

        Args:
            value (float): Valor da tendência

        Returns:
            str: Código de cor hexadecimal
        """
        if value > 0:
            return cls.COLORS["success"]
        elif value < 0:
            return cls.COLORS["danger"]
        return cls.COLORS["secondary"]

    # Estilos para elementos do dashboard
    CARD_STYLE = {
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "borderRadius": "8px",
        "border": "none",
        "height": "100%",
    }

    HEADER_STYLE = {
        "backgroundColor": COLORS["light"],
        "padding": "20px",
        "marginBottom": "20px",
        "borderRadius": "8px",
    }

    TABLE_STYLES = {
        "header": {
            "backgroundColor": COLORS["light"],
            "fontWeight": "bold",
            "textAlign": "left",
            "padding": "12px",
        },
        "cell": {
            "textAlign": "left",
            "padding": "8px",
        },
    }

    # Configurações de gráficos
    CHART_CONFIG = {
        "template": "plotly_white",
        "font": {"family": "Arial, sans-serif"},
        "showlegend": True,
        "margin": {"t": 50, "l": 50, "r": 50, "b": 50},
        "hovermode": "closest",
    }

    @classmethod
    def apply_chart_theme(cls, fig: go.Figure) -> go.Figure:
        """
        Aplica o tema padrão a um gráfico Plotly.

        Args:
            fig (go.Figure): Figura do Plotly

        Returns:
            go.Figure: Figura com tema aplicado
        """
        fig.update_layout(
            template=cls.CHART_CONFIG["template"],
            font=cls.CHART_CONFIG["font"],
            showlegend=cls.CHART_CONFIG["showlegend"],
            margin=cls.CHART_CONFIG["margin"],
            hovermode=cls.CHART_CONFIG["hovermode"],
            paper_bgcolor=cls.COLORS["light"],
            plot_bgcolor="white",
        )
        return fig

    @classmethod
    def get_style_conditions(cls) -> List[Dict]:
        """
        Retorna condições de estilo para tabelas de dados.

        Returns:
            List[Dict]: Lista de condições de estilo
        """
        return [
            {
                "if": {"row_index": "odd"},
                "backgroundColor": cls.COLORS["light"],
            },
            {
                "if": {
                    "column_id": "prioridade",
                    "filter_query": "{prioridade} eq 'S3.7'",
                },
                "backgroundColor": f"{cls.PRIORITY_COLORS['S3.7']}20",
                "color": cls.PRIORITY_COLORS["S3.7"],
                "fontWeight": "bold",
            },
            {
                "if": {"column_id": "dias", "filter_query": "{dias} > 30"},
                "backgroundColor": f"{cls.COLORS['warning']}20",
                "color": cls.COLORS["warning"],
            },
        ]


class DataLoader:
    """
    Carrega e prepara os dados das SSAs.

    Esta classe é responsável por carregar os dados do arquivo Excel,
    realizar as conversões necessárias e manter os objetos SSAData.
    """

    def __init__(self, excel_path: str):
        """
        Inicializa o carregador de dados.

        Args:
            excel_path (str): Caminho para o arquivo Excel
        """
        if not excel_path:
            raise ValueError("Caminho do arquivo Excel não pode ser vazio")

        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {excel_path}")

        self.logger = logging.getLogger(__name__)
        self._df: Optional[pd.DataFrame] = None
        self._ssa_objects: Optional[List[SSAData]] = None

    def load_data(self) -> pd.DataFrame:
        """
        Carrega dados do Excel com as configurações corretas.

        Returns:
            pd.DataFrame: DataFrame com os dados carregados e processados

        Raises:
            FileNotFoundError: Se o arquivo Excel não for encontrado
            ValueError: Se houver problemas com o formato dos dados
            Exception: Para outros erros durante o carregamento
        """
        try:
            self.df = pd.read_excel(
                self.excel_path,
                header=2,
            )

            # Pipeline de processamento
            self._convert_dates()
            self._process_string_columns()
            self._process_optional_columns()
            self._standardize_priorities()
            self._remove_invalid_rows()
            self._convert_to_objects()
            self._log_sample_dates()
            self._validate_data()

            return self.df

        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {self.excel_path}")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            raise

    def load(self) -> pd.DataFrame:
        """Load data from Excel file"""
        try:
            self._df = pd.read_excel(self.excel_path)
            self.logger.info(
                f"Dados carregados com sucesso. Total de registros: {len(self._df)}"
            )
            return self._df
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {str(e)}")
            raise
            raise

    def _convert_dates(self):
        """Converte a coluna de data para o formato correto."""
        try:
            self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.to_datetime(
                self.df.iloc[:, SSAColumns.EMITIDA_EM],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce",
            )

            valid_dates = self.df.iloc[:, SSAColumns.EMITIDA_EM].notna().sum()
            total_dates = len(self.df)

            logger.info(f"Convertidas {valid_dates} de {total_dates} datas com sucesso")

            if valid_dates == 0:
                logger.error("Nenhuma data foi convertida com sucesso")
            elif valid_dates < total_dates:
                logger.warning(
                    f"Algumas datas ({total_dates - valid_dates}) não puderam ser convertidas"
                )

        except Exception as e:
            logger.error(f"Erro ao processar datas: {str(e)}")
            self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.NaT

    def _process_string_columns(self):
        """Processa e limpa as colunas do tipo string."""
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
            self.df.iloc[:, col] = (
                self.df.iloc[:, col].astype(str).replace("nan", "").str.strip()
            )

    def _process_optional_columns(self):
        """Processa e limpa as colunas opcionais."""
        optional_string_columns = [
            SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO,
            SSAColumns.RESPONSAVEL_PROGRAMACAO,
            SSAColumns.SEMANA_PROGRAMADA,
            SSAColumns.RESPONSAVEL_EXECUCAO,
            SSAColumns.DESCRICAO_EXECUCAO,
        ]

        for col in optional_string_columns:
            self.df.iloc[:, col] = self.df.iloc[:, col].astype(str).replace("nan", None)

    def _standardize_priorities(self):
        """Padroniza as prioridades para maiúsculas."""
        self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] = (
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].str.upper().str.strip()
        )

    def _remove_invalid_rows(self):
        """Remove linhas com número de SSA inválido."""
        self.df = self.df[self.df.iloc[:, SSAColumns.NUMERO_SSA].str.strip() != ""]

    def _log_sample_dates(self):
        """Registra exemplos das primeiras datas convertidas."""
        if not self.df.empty:
            sample_dates = self.df.iloc[:5, SSAColumns.EMITIDA_EM]
            logger.info("Exemplos de datas convertidas:")
            for idx, date in enumerate(sample_dates):
                logger.info(f"Linha {idx + 1}: {date}")

    # MODIFICAÇÕES PENDENTES

    def _convert_to_objects(self):
        """
        TODO: Refatorar para melhor tratamento de erros e validação
        Converte as linhas do DataFrame em objetos SSAData.
        """
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
                    logger.error(f"Erro ao converter linha {idx}: {str(e)}")
                    continue

            logger.info(f"Convertidos {len(self.ssa_objects)} registros para SSAData")

            if self.ssa_objects:
                first_ssa = self.ssa_objects[0]
                logger.info("Exemplo de primeiro objeto convertido:")
                logger.info(f"Número: {first_ssa.numero}")
                logger.info(f"Data de emissão: {first_ssa.emitida_em}")
                logger.info(f"Prioridade: {first_ssa.prioridade_emissao}")

        except Exception as e:
            logger.error(f"Erro durante conversão para objetos: {str(e)}")
            raise

    def filter_ssas(self, **kwargs) -> List[SSAData]:
        """Filtra SSAs baseado em critérios"""
        ssas = self.get_ssa_objects()
        filtered_ssas = []

        for ssa in ssas:
            match = True
            for key, value in kwargs.items():
                if not hasattr(ssa, key.lower()):
                    continue
                if getattr(ssa, key.lower()) != value:
                    match = False
                    break
            if match:
                filtered_ssas.append(ssa)

        return filtered_ssas
        """
         Implementar filtragem adicional por:
        - Status de execução
        - Tipo de equipamento
        - Responsável
        - Localização

        Returns:
            List[SSAData]: Lista de SSAs filtradas
        """
        """Filtra SSAs com base nos critérios fornecidos."""

    def _validate_dates(self) -> bool:
        """Valida formato das datas"""
        try:
            self._df['EMITIDA_EM'] = pd.to_datetime(self._df['EMITIDA_EM'])
            return True
        except Exception as e:
            self.logger.warning(f"Erro na validação de datas: {str(e)}")
            return False

    def _validate_priorities(self) -> bool:
        """Valida prioridades"""
        valid_priorities = {'ALTA', 'MEDIA', 'BAIXA', 'PROGRAMÁVEL'}
        current_priorities = set(self._df['PRIORIDADE'].unique())
        invalid_priorities = current_priorities - valid_priorities
        
        if invalid_priorities:
            self.logger.warning(f"Prioridades inválidas encontradas: {list(invalid_priorities)}")
            return False
        return True

    def _validate_relationships(self) -> bool:
        """Valida relacionamentos entre SSAs"""
        if 'ORIGEM' not in self._df.columns:
            return True

        origins = set(self._df['ORIGEM'].dropna())
        numbers = set(self._df['NUMERO'].astype(str))
        invalid_origins = origins - numbers

        if invalid_origins:
            self.logger.warning(f"SSAs derivadas com origem inexistente: {list(invalid_origins)}")
            return False
        return True
    
    def validate_data(self) -> Dict[str, bool]:
        """Valida os dados carregados"""
        if self._df is None:
            self.load()

        validation_results = {
            "dates": self._validate_dates(),
            "priorities": self._validate_priorities(),
            "relationships": self._validate_relationships(),
        }

        return validation_results

    def _convert_to_ssa_objects(self):
        """Converte DataFrame em objetos SSAData"""
        self._ssa_objects = []

        for _, row in self._df.iterrows():
            try:
                ssa = SSAData(row.to_dict())
                self._ssa_objects.append(ssa)
            except Exception as e:
                self.logger.warning(f"Erro ao converter registro: {row['NUMERO']}. Erro: {str(e)}")

        self.logger.info(f"Convertidos {len(self._ssa_objects)} registros para objetos SSAData")

    def get_ssa_objects(self) -> List[SSAData]:
        """
        Adicionar cache para melhorar performance

        Returns:
            List[SSAData]: Lista de todos os objetos SSA
        """
        """Retorna lista de objetos SSA com cache."""
        if self._ssa_objects is None:
            if self._df is None:
                self.load()
            self._convert_to_ssa_objects()
        return self._ssa_objects

    # NOVOS MÉTODOS A SEREM IMPLEMENTADOS

    def _validate_data(self) -> bool:
        """
        Implementar validação completa dos dados
        - Verificar consistência das datas
        - Validar códigos de prioridade
        - Verificar relacionamentos entre SSAs
        - Validar formato dos campos obrigatórios
        """
        try:
            validations = {
                "dates": self._validate_dates(),
                "priorities": self._validate_priorities(),
                "relationships": self._validate_relationships(),
                "required_fields": self._validate_required_fields()
            }

            all_valid = all(validations.values())
            if all_valid:
                logger.info("Validação de dados concluída com sucesso")
            else:
                failed = [k for k, v in validations.items() if not v]
                logger.warning(f"Falha nas validações: {failed}")

            return all_valid

        except Exception as e:
            logger.error(f"Erro durante validação: {str(e)}")
            return False

    def _validate_dates(self) -> bool:
        """Valida consistência das datas."""
        valid_dates = self.df.iloc[:, SSAColumns.EMITIDA_EM].notna()
        future_dates = self.df.iloc[:, SSAColumns.EMITIDA_EM] > datetime.now()

        if not valid_dates.all():
            logger.warning(f"Encontradas {(~valid_dates).sum()} datas inválidas")

        if future_dates.any():
            logger.warning(f"Encontradas {future_dates.sum()} datas futuras")

        return valid_dates.all() and not future_dates.any()

    def _validate_priorities(self) -> bool:
        """Valida códigos de prioridade."""
        valid_priorities = ["S3.7", "S3.6", "S3.5"]
        priorities = self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].unique()
        invalid = [p for p in priorities if p not in valid_priorities]

        if invalid:
            logger.warning(f"Prioridades inválidas encontradas: {invalid}")
            return False
        return True

    def _validate_relationships(self) -> bool:
        """Valida relacionamentos entre SSAs."""
        derived = self.df[self.df.iloc[:, SSAColumns.DERIVADA].notna()]
        if derived.empty:
            return True

        parent_ssas = derived.iloc[:, SSAColumns.DERIVADA].unique()
        existing_ssas = self.df.iloc[:, SSAColumns.NUMERO_SSA].unique()

        invalid = [ssa for ssa in parent_ssas if ssa not in existing_ssas]
        if invalid:
            logger.warning(f"SSAs derivadas com origem inexistente: {invalid}")
            return False
        return True

    def _validate_required_fields(self) -> bool:
        """Valida campos obrigatórios."""
        required_fields = [
            SSAColumns.NUMERO_SSA,
            SSAColumns.SITUACAO,
            SSAColumns.SETOR_EXECUTOR,
            SSAColumns.GRAU_PRIORIDADE_EMISSAO,
        ]

        for field in required_fields:
            empty = self.df.iloc[:, field].isna() | (self.df.iloc[:, field] == "")
            if empty.any():
                logger.warning(
                    f"Campo obrigatório {SSAColumns.get_name(field)} vazio em {empty.sum()} registros"
                )
                return False
        return True

    def export_validated_data(self, output_path: str):
        """
        Exporta dados validados com relatório de qualidade.
        
        Args:
            output_path (str): Caminho para salvar os dados exportados
        """
        try:
            # Executa validação completa
            validation_results = {
                "dates": self._validate_dates(),
                "priorities": self._validate_priorities(),
                "relationships": self._validate_relationships(),
                "required_fields": self._validate_required_fields()
            }

            # Prepara relatório de validação
            validation_report = pd.DataFrame([{
                "Data": datetime.now(),
                "Total_SSAs": len(self.df),
                "Datas_Válidas": validation_results["dates"],
                "Prioridades_Válidas": validation_results["priorities"],
                "Relacionamentos_Válidos": validation_results["relationships"],
                "Campos_Obrigatórios_Válidos": validation_results["required_fields"]
            }])

            # Cria arquivo Excel com múltiplas abas
            with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
                # Dados principais
                self.df.to_excel(writer, sheet_name="Dados_SSAs", index=False)

                # Relatório de validação
                validation_report.to_excel(writer, sheet_name="Validação", index=False)

                # Logs de problemas encontrados
                self._export_validation_logs(writer)

                # Estatísticas básicas
                self._export_basic_stats(writer)

            logger.info(f"Dados exportados com sucesso para {output_path}")

        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            raise

    def _export_validation_logs(self, writer: pd.ExcelWriter):
        """
        Exporta logs detalhados de validação.

        Args:
            writer: ExcelWriter para adicionar a aba de logs
        """
        validation_logs = []

        # Verifica datas inválidas
        invalid_dates = self.df[self.df.iloc[:, SSAColumns.EMITIDA_EM].isna()]
        if not invalid_dates.empty:
            for _, row in invalid_dates.iterrows():
                validation_logs.append(
                    {
                        "Tipo": "Data Inválida",
                        "SSA": row.iloc[SSAColumns.NUMERO_SSA],
                        "Detalhes": "Data de emissão ausente ou inválida",
                    }
                )

        # Verifica prioridades inválidas
        valid_priorities = ["S3.7", "S3.6", "S3.5"]
        invalid_priorities = self.df[
            ~self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].isin(valid_priorities)
        ]
        if not invalid_priorities.empty:
            for _, row in invalid_priorities.iterrows():
                validation_logs.append(
                    {
                        "Tipo": "Prioridade Inválida",
                        "SSA": row.iloc[SSAColumns.NUMERO_SSA],
                        "Detalhes": f"Prioridade {row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]} não reconhecida",
                    }
                )

        # Verifica relacionamentos
        derived = self.df[self.df.iloc[:, SSAColumns.DERIVADA].notna()]
        existing_ssas = set(self.df.iloc[:, SSAColumns.NUMERO_SSA])
        for _, row in derived.iterrows():
            parent_ssa = row.iloc[SSAColumns.DERIVADA]
            if parent_ssa not in existing_ssas:
                validation_logs.append(
                    {
                        "Tipo": "Relacionamento Inválido",
                        "SSA": row.iloc[SSAColumns.NUMERO_SSA],
                        "Detalhes": f"SSA origem {parent_ssa} não encontrada",
                    }
                )

        # Exporta logs
        if validation_logs:
            pd.DataFrame(validation_logs).to_excel(
                writer, sheet_name="Logs_Validação", index=False
            )

    def _export_basic_stats(self, writer: pd.ExcelWriter):
        """
        Exporta estatísticas básicas dos dados.

        Args:
            writer: ExcelWriter para adicionar a aba de estatísticas
        """
        stats = []

        # Estatísticas por prioridade
        priority_counts = self.df.iloc[
            :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
        ].value_counts()
        for priority, count in priority_counts.items():
            stats.append(
                {
                    "Categoria": "Prioridade",
                    "Valor": priority,
                    "Quantidade": count,
                    "Percentual": f"{(count/len(self.df)*100):.2f}%",
                }
            )

        # Estatísticas por setor
        sector_counts = self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].value_counts()
        for sector, count in sector_counts.items():
            stats.append(
                {
                    "Categoria": "Setor",
                    "Valor": sector,
                    "Quantidade": count,
                    "Percentual": f"{(count/len(self.df)*100):.2f}%",
                }
            )

        # Estatísticas por estado
        state_counts = self.df.iloc[:, SSAColumns.SITUACAO].value_counts()
        for state, count in state_counts.items():
            stats.append(
                {
                    "Categoria": "Estado",
                    "Valor": state,
                    "Quantidade": count,
                    "Percentual": f"{(count/len(self.df)*100):.2f}%",
                }
            )

        # Exporta estatísticas
        pd.DataFrame(stats).to_excel(writer, sheet_name="Estatísticas", index=False)

    def update_ssa_data(self, ssa_id: str, updates: Dict):
        """
        Atualiza dados de uma SSA específica.
        
        Args:
            ssa_id (str): Número identificador da SSA
            updates (Dict): Dicionário com as atualizações a serem aplicadas
            
        Returns:
            bool: True se a atualização foi bem sucedida
        """
        try:
            # Localiza a SSA
            ssa_mask = self.df.iloc[:, SSAColumns.NUMERO_SSA] == ssa_id
            if not ssa_mask.any():
                logger.error(f"SSA {ssa_id} não encontrada")
                return False

            # Valida atualizações
            if not self._validate_updates(updates):
                logger.error(f"Atualizações inválidas para SSA {ssa_id}")
                return False

            # Registra histórico
            self._record_update_history(ssa_id, updates)

            # Aplica atualizações
            for field, value in updates.items():
                if hasattr(SSAColumns, field.upper()):
                    col_idx = getattr(SSAColumns, field.upper())
                    self.df.loc[ssa_mask, self.df.columns[col_idx]] = value

            # Atualiza objeto SSAData correspondente
            self._update_ssa_object(ssa_id, updates)

            # Limpa cache
            self._cache.clear()

            logger.info(f"SSA {ssa_id} atualizada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar SSA {ssa_id}: {str(e)}")
            return False

    def _validate_updates(self, updates: Dict) -> bool:
        """
        Valida as atualizações propostas.
        
        Args:
            updates (Dict): Dicionário com as atualizações
            
        Returns:
            bool: True se as atualizações são válidas
        """
        valid_fields = {field.lower() for field in dir(SSAColumns) 
                       if not field.startswith('_') and field.isupper()}

        for field in updates:
            if field.lower() not in valid_fields:
                logger.error(f"Campo inválido: {field}")
                return False

            value = updates[field]
            field_upper = field.upper()

            # Validações específicas por tipo de campo
            if field_upper == "GRAU_PRIORIDADE_EMISSAO":
                if value not in ["S3.7", "S3.6", "S3.5"]:
                    logger.error(f"Prioridade inválida: {value}")
                    return False

            elif field_upper == "EMITIDA_EM":
                try:
                    pd.to_datetime(value)
                except:
                    logger.error(f"Data inválida: {value}")
                    return False

        return True

    def _record_update_history(self, ssa_id: str, updates: Dict):
        """
        Registra histórico de atualizações.
        
        Args:
            ssa_id (str): Número identificador da SSA
            updates (Dict): Dicionário com as atualizações
        """
        history_record = {
            "ssa_id": ssa_id,
            "timestamp": datetime.now(),
            "updates": updates
        }

        # TODO Aqui você pode implementar o armazenamento do histórico
        # Por exemplo, em um arquivo de log ou banco de dados
        logger.info(f"Histórico de atualização: {history_record}")

    def _update_ssa_object(self, ssa_id: str, updates: Dict):
        """
        Atualiza o objeto SSAData correspondente.
        
        Args:
            ssa_id (str): Número identificador da SSA
            updates (Dict): Dicionário com as atualizações
        """
        for ssa in self.ssa_objects:
            if ssa.numero == ssa_id:
                for field, value in updates.items():
                    if hasattr(ssa, field.lower()):
                        setattr(ssa, field.lower(), value)
                break

class KPICalculator:
    """Calcula indicadores chave de desempenho (KPIs) para SSAs."""

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o calculador de KPIs.
        
        Args:
            df (pd.DataFrame): DataFrame com os dados das SSAs
        """
        self.df = df
        self.sla_limits = {
            "S3.7": 24,  # horas
            "S3.6": 48,  # horas
            "S3.5": 72   # horas
        }

    # Métodos Implementados

    def calculate_efficiency_metrics(self) -> Dict:
        """
        Calcula métricas básicas de eficiência.

        Returns:
            Dict: Dicionário com métricas de eficiência
        """
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
        """
        Calcula um score geral de saúde do sistema.

        Returns:
            float: Score de 0 a 100
        """
        metrics = self.calculate_efficiency_metrics()
        score = (
            metrics["taxa_programacao"] * 0.5 + metrics["taxa_execucao_simples"] * 0.5
        )
        return round(score * 100, 2)

    # Métodos a serem implementados

    def calculate_time_based_kpis(self) -> Dict:
        """
        Calcula KPIs baseados em tempo.

        Returns:
            Dict: Métricas baseadas em tempo
        """
        time_kpis = {
            "tempo_medio_por_prioridade": self._calculate_avg_time_by_priority(),
            "tempo_medio_programacao": self._calculate_avg_programming_time(),
            "tempo_medio_execucao": self._calculate_avg_execution_time(),
            "gargalos_temporais": self._identify_temporal_bottlenecks(),
            "tendencias_temporais": self._analyze_temporal_trends(),
        }
        return time_kpis

    def _calculate_avg_time_by_priority(self) -> Dict:
        """Calcula tempo médio de atendimento por prioridade."""
        avg_times = {}
        for priority in ["S3.7", "S3.6", "S3.5"]:
            priority_df = self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]
            if not priority_df.empty:
                avg_time = (
                    priority_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                ).dt.total_seconds() / 3600  # convertendo para horas
                avg_times[priority] = abs(avg_time.mean())
        return avg_times

    def _calculate_avg_programming_time(self) -> float:
        """Calcula tempo médio de programação."""
        programmed_ssas = self.df[self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()]
        if programmed_ssas.empty:
            return 0
        return (
            programmed_ssas.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
        ).dt.total_seconds() / 3600  # horas

    def _calculate_avg_execution_time(self) -> float:
        """Calcula tempo médio de execução."""
        executed_ssas = self.df[
            self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()
        ]
        if executed_ssas.empty:
            return 0
        return (
            executed_ssas.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
        ).dt.total_seconds() / 3600  # horas

    def _identify_temporal_bottlenecks(self) -> List[Dict]:
        """Identifica gargalos temporais."""
        bottlenecks = []

        # Análise por estado
        for state in self.df.iloc[:, SSAColumns.SITUACAO].unique():
            state_df = self.df[self.df.iloc[:, SSAColumns.SITUACAO] == state]
            avg_time = (
                state_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
            ).dt.total_seconds() / 3600

            if abs(avg_time.mean()) > 48:  # mais de 48 horas
                bottlenecks.append(
                    {
                        "tipo": "Estado",
                        "valor": state,
                        "tempo_medio": abs(avg_time.mean()),
                        "quantidade_ssas": len(state_df),
                    }
                )

        return bottlenecks

    def _analyze_temporal_trends(self) -> Dict:
        """Analisa tendências temporais."""
        # Agrupa por dia
        daily_counts = self.df.groupby(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date
        ).size()

        # Calcula tendência usando regressão linear
        x = np.arange(len(daily_counts))
        y = daily_counts.values
        slope, intercept = np.polyfit(x, y, 1)

        return {
            "tendencia": slope,
            "media_diaria": daily_counts.mean(),
            "desvio_padrao": daily_counts.std(),
            "pico": daily_counts.max(),
            "vale": daily_counts.min(),
        }

    def calculate_sector_performance(self) -> Dict:
        """
        Calcula KPIs por setor.
        
        Returns:
            Dict: Métricas de performance setorial
        """
        return {
            "taxa_resolucao": self._calculate_resolution_rate_by_sector(),
            "tempo_medio_resposta": self._calculate_response_time_by_sector(),
            "volume_trabalho": self._calculate_workload_by_sector(),
            "eficiencia_setorial": self._calculate_sector_efficiency(),
            "comparativo_setores": self._compare_sectors()
        }

    def _calculate_resolution_rate_by_sector(self) -> Dict:
        """Calcula taxa de resolução por setor."""
        resolution_rates = {}
        for sector in self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            sector_df = self.df[self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == sector]
            resolved = sector_df[
                sector_df.iloc[:, SSAColumns.SITUACAO].isin(["Concluída", "Fechada"])
            ]
            resolution_rates[sector] = (
                len(resolved) / len(sector_df) if len(sector_df) > 0 else 0
            )
        return resolution_rates

    def _calculate_response_time_by_sector(self) -> Dict:
        """Calcula tempo médio de resposta por setor."""
        response_times = {}
        for sector in self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            sector_df = self.df[self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == sector]
            avg_time = (
                sector_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
            ).dt.total_seconds() / 3600
            response_times[sector] = abs(avg_time.mean())
        return response_times

    def _calculate_workload_by_sector(self) -> Dict:
        """Calcula volume de trabalho por setor."""
        return {
            "total_ssas": self.df.iloc[:, SSAColumns.SETOR_EXECUTOR]
            .value_counts()
            .to_dict(),
            "ssas_criticas": self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"
            ]
            .iloc[:, SSAColumns.SETOR_EXECUTOR]
            .value_counts()
            .to_dict(),
            "ssas_pendentes": self.df[
                ~self.df.iloc[:, SSAColumns.SITUACAO].isin(["Concluída", "Fechada"])
            ]
            .iloc[:, SSAColumns.SETOR_EXECUTOR]
            .value_counts()
            .to_dict(),
        }

    def _calculate_sector_efficiency(self) -> Dict:
        """Calcula eficiência setorial."""
        efficiency_metrics = {}
        for sector in self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            sector_df = self.df[self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == sector]

            # Calcula diferentes métricas de eficiência
            metrics = {
                "taxa_cumprimento_sla": self._calculate_sla_compliance(sector_df),
                "taxa_execucao_simples": (
                    len(
                        sector_df[
                            sector_df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Sim"
                        ]
                    )
                    / len(sector_df)
                    if len(sector_df) > 0
                    else 0
                ),
                "tempo_medio_resolucao": abs(
                    (
                        sector_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                    ).dt.total_seconds()
                    / 3600
                ).mean(),
            }

            # Calcula score geral
            efficiency_metrics[sector] = {
                "metricas": metrics,
                "score_geral": np.mean(list(metrics.values())),
            }

        return efficiency_metrics

    def _compare_sectors(self) -> Dict:
        """Realiza comparativo entre setores."""
        sectors = self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique()
        comparisons = {}

        for sector in sectors:
            sector_df = self.df[self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == sector]

            # Calcula métricas comparativas
            comparisons[sector] = {
                "volume_relativo": len(sector_df) / len(self.df),
                "taxa_criticidade": (
                    len(
                        sector_df[
                            sector_df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                            == "S3.7"
                        ]
                    )
                    / len(sector_df)
                    if len(sector_df) > 0
                    else 0
                ),
                "tempo_medio_vs_global": (
                    abs(
                        (
                            sector_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean()
                    / abs(
                        (
                            self.df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean()
                ),
            }

        return comparisons

    def calculate_priority_metrics(self) -> Dict:
        """
        Calcula métricas relacionadas a prioridades.

        Returns:
            Dict: Métricas de prioridade
        """
        return {
            "distribuicao_temporal": self._analyze_priority_distribution(),
            "taxa_atendimento": self._calculate_priority_attendance_rate(),
            "tempo_resposta": self._calculate_priority_response_time(),
            "analise_escalonamento": self._analyze_priority_escalation(),
        }

    def _analyze_priority_distribution(self) -> Dict:
        """Analisa distribuição de prioridades ao longo do tempo."""
        # Agrupa por data e prioridade
        priority_dist = pd.crosstab(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date,
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
            normalize="index",
        )

        return {
            "distribuicao_diaria": priority_dist.to_dict(),
            "tendencia": {
                priority: np.polyfit(
                    range(len(priority_dist)), priority_dist[priority].values, 1
                )[0]
                for priority in priority_dist.columns
            },
        }

    def _calculate_priority_attendance_rate(self) -> Dict:
        """Calcula taxa de atendimento por prioridade."""
        attendance_rates = {}
        for priority in ["S3.7", "S3.6", "S3.5"]:
            priority_df = self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]
            if not priority_df.empty:
                attended = priority_df[
                    priority_df.iloc[:, SSAColumns.SITUACAO].isin(
                        ["Concluída", "Fechada"]
                    )
                ]
                attendance_rates[priority] = {
                    "taxa": len(attended) / len(priority_df),
                    "dentro_sla": self._calculate_sla_compliance(priority_df),
                    "tempo_medio": abs(
                        (
                            priority_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean(),
                }
        return attendance_rates

    def _calculate_priority_response_time(self) -> Dict:
        """Calcula tempo de resposta por prioridade."""
        response_times = {}
        for priority in ["S3.7", "S3.6", "S3.5"]:
            priority_df = self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]
            if not priority_df.empty:
                response_times[priority] = {
                    "media": abs(
                        (
                            priority_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean(),
                    "mediana": abs(
                        (
                            priority_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).median(),
                    "desvio_padrao": abs(
                        (
                            priority_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).std(),
                }
        return response_times

    def _analyze_priority_escalation(self) -> Dict:
        """Analisa padrões de escalonamento de prioridades."""
        escalations = {
            "total_escalonamentos": len(
                self.df[
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO] != 
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                ]
            ),
            "por_prioridade_origem": {},
            "por_setor": {},
            "tendencia_temporal": {}
        }

        # Análise por prioridade de origem
        for priority in ["S3.5", "S3.6", "S3.7"]:
            escalated = self.df[
                (self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority) &
                (self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO] != priority)
            ]
            if not escalated.empty:
                escalations["por_prioridade_origem"][priority] = {
                    "quantidade": len(escalated),
                    "destinos": escalated.iloc[:, SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO].value_counts().to_dict()
                }

        # Análise por setor
        for setor in self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            setor_df = self.df[self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor]
            escalated = setor_df[
                setor_df.iloc[:, SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO] != 
                setor_df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            ]
            if not escalated.empty:
                escalations["por_setor"][setor] = {
                    "quantidade": len(escalated),
                    "taxa": len(escalated) / len(setor_df)
                }

        # Análise temporal
        escalations["tendencia_temporal"] = self._analyze_escalation_trends()

        return escalations

    def _analyze_escalation_trends(self) -> Dict:
        """Analisa tendências temporais de escalonamento."""
        # Agrupa escalonamentos por data
        escalated_by_date = (
            self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO]
                != self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            ]
            .groupby(self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date)
            .size()
        )

        if escalated_by_date.empty:
            return {}

        # Calcula tendência
        x = np.arange(len(escalated_by_date))
        y = escalated_by_date.values
        slope, intercept = np.polyfit(x, y, 1)

        return {
            "tendencia": slope,
            "media_diaria": escalated_by_date.mean(),
            "maximo": escalated_by_date.max(),
            "minimo": escalated_by_date.min(),
        }

    def calculate_responsiveness_metrics(self) -> Dict:
        """
        Calcula métricas de responsividade.

        Returns:
            Dict: Métricas de responsividade
        """
        return {
            "tempo_primeira_resposta": self._calculate_first_response_time(),
            "tempo_entre_atualizacoes": self._calculate_update_intervals(),
            "taxa_sla": self._calculate_sla_compliance(self.df),
            "atrasos_criticos": self._identify_critical_delays(),
        }

    def _calculate_first_response_time(self) -> Dict:
        """Calcula tempo até primeira resposta."""
        response_times = {}

        for priority in ["S3.7", "S3.6", "S3.5"]:
            priority_df = self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]
            if not priority_df.empty:
                # Tempo até primeira programação
                programmed = priority_df[
                    priority_df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].notna()
                ]
                if not programmed.empty:
                    response_times[f"{priority}_programacao"] = abs(
                        (
                            programmed.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean()

                # Tempo até primeira execução
                executed = priority_df[
                    priority_df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()
                ]
                if not executed.empty:
                    response_times[f"{priority}_execucao"] = abs(
                        (
                            executed.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean()

        return response_times

    def _calculate_update_intervals(self) -> Dict:
        """Calcula intervalos entre atualizações."""
        intervals = {"programacao": {}, "execucao": {}}

        # Analisa intervalos de programação
        prog_updates = self.df[
            self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].notna()
        ]
        if not prog_updates.empty:
            intervals["programacao"] = {
                "medio": abs(
                    (
                        prog_updates.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                    ).dt.total_seconds()
                    / 3600
                ).mean(),
                "maximo": abs(
                    (
                        prog_updates.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                    ).dt.total_seconds()
                    / 3600
                ).max(),
            }

        # Analisa intervalos de execução
        exec_updates = self.df[self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()]
        if not exec_updates.empty:
            intervals["execucao"] = {
                "medio": abs(
                    (
                        exec_updates.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                    ).dt.total_seconds()
                    / 3600
                ).mean(),
                "maximo": abs(
                    (
                        exec_updates.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                    ).dt.total_seconds()
                    / 3600
                ).max(),
            }

        return intervals

    def _identify_critical_delays(self) -> List[Dict]:
        """Identifica atrasos críticos."""
        critical_delays = []

        for _, row in self.df.iterrows():
            priority = row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            if priority in self.sla_limits:
                time_limit = self.sla_limits[priority]
                elapsed_time = abs(
                    (row.iloc[SSAColumns.EMITIDA_EM] - datetime.now()).total_seconds()
                    / 3600
                )

                if elapsed_time > time_limit * 2:  # Atraso maior que 2x o SLA
                    critical_delays.append(
                        {
                            "ssa": row.iloc[SSAColumns.NUMERO_SSA],
                            "prioridade": priority,
                            "tempo_decorrido": elapsed_time,
                            "limite_sla": time_limit,
                            "setor": row.iloc[SSAColumns.SETOR_EXECUTOR],
                            "estado": row.iloc[SSAColumns.SITUACAO],
                        }
                    )

        return critical_delays

    def calculate_quality_metrics(self) -> Dict:
        """
        Calcula métricas de qualidade.

        Returns:
            Dict: Métricas de qualidade
        """
        return {
            "taxa_retrabalho": self._calculate_rework_rate(),
            "qualidade_documentacao": self._assess_documentation_quality(),
            "conformidade_procedimentos": self._assess_procedure_compliance(),
            "indicadores_satisfacao": self._calculate_satisfaction_indicators(),
        }

    def _calculate_rework_rate(self) -> Dict:
        """Calcula taxa de retrabalho."""
        rework = {"geral": 0, "por_setor": {}, "por_prioridade": {}}

        # Identifica SSAs com retrabalho (derivadas ou reabertas)
        reworked = self.df[
            (self.df.iloc[:, SSAColumns.DERIVADA].notna())
            | (self.df.iloc[:, SSAColumns.SITUACAO] == "Reaberta")
        ]

        if not reworked.empty:
            total_ssas = len(self.df)
            rework["geral"] = len(reworked) / total_ssas

            # Análise por setor
            for setor in self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
                setor_rework = reworked[
                    reworked.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor
                ]
                setor_total = self.df[
                    self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor
                ]
                rework["por_setor"][setor] = len(setor_rework) / len(setor_total)

            # Análise por prioridade
            for priority in ["S3.7", "S3.6", "S3.5"]:
                priority_rework = reworked[
                    reworked.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
                ]
                priority_total = self.df[
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
                ]
                if len(priority_total) > 0:
                    rework["por_prioridade"][priority] = len(priority_rework) / len(
                        priority_total
                    )

        return rework

    def _assess_documentation_quality(self) -> Dict:
        """Avalia qualidade da documentação."""
        quality_metrics = {
            "completude": self._calculate_documentation_completeness(),
            "detalhamento": self._assess_description_detail(),
            "atualizacao": self._assess_update_quality(),
        }
        return quality_metrics

    def _calculate_documentation_completeness(self) -> float:
        """Calcula completude da documentação."""
        required_fields = [
            SSAColumns.DESC_SSA,
            SSAColumns.LOCALIZACAO,
            SSAColumns.EQUIPAMENTO,
            SSAColumns.SETOR_EXECUTOR,
        ]

        complete_docs = 0
        total_ssas = len(self.df)

        for _, row in self.df.iterrows():
            if all(
                pd.notna(row.iloc[field]) and row.iloc[field].strip() != ""
                for field in required_fields
            ):
                complete_docs += 1

        return complete_docs / total_ssas if total_ssas > 0 else 0

    def _assess_description_detail(self) -> Dict:
        """Avalia nível de detalhamento das descrições."""
        descriptions = self.df.iloc[:, SSAColumns.DESC_SSA].astype(str)

        return {
            "media_palavras": descriptions.str.split().str.len().mean(),
            "com_detalhes_tecnicos": len(
                descriptions[
                    descriptions.str.contains(
                        r"\b(equipamento|sistema|falha|erro|código)\b",
                        case=False,
                        regex=True,
                    )
                ]
            )
            / len(self.df),
            "com_contexto": len(
                descriptions[
                    descriptions.str.contains(
                        r"\b(quando|onde|como|porque|após|durante)\b",
                        case=False,
                        regex=True,
                    )
                ]
            )
            / len(self.df),
        }

    def _assess_update_quality(self) -> Dict:
        """Avalia qualidade das atualizações."""
        updates = self.df.iloc[:, SSAColumns.DESCRICAO_EXECUCAO].astype(str)

        return {
            "com_atualizacao": len(updates[updates != ""]) / len(self.df),
            "detalhamento_medio": updates[updates != ""].str.split().str.len().mean(),
            "atualizacoes_tecnicas": len(
                updates[
                    updates.str.contains(
                        r"\b(realizado|executado|instalado|configurado|ajustado)\b",
                        case=False,
                        regex=True,
                    )
                ]
            )
            / len(self.df),
        }

    def _assess_procedure_compliance(self) -> Dict:
        """Avalia conformidade com procedimentos."""
        compliance = {
            "documentacao": self._calculate_documentation_completeness(),
            "sla": self._calculate_sla_compliance(self.df),
            "fluxo_trabalho": self._assess_workflow_compliance(),
            "responsabilidades": self._assess_responsibility_compliance(),
        }
        return compliance

    def _assess_workflow_compliance(self) -> float:
        """Avalia conformidade com fluxo de trabalho."""
        # Verifica sequência correta de estados
        valid_sequence = len(self.df[
            (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].notna()) &
            (self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()) &
            (
                (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()) |
                (self.df.iloc[:, SSAColumns.SITUACAO].isin(["Concluída", "Fechada"]))
            )
        ]) / len(self.df)

        return valid_sequence

    def _assess_responsibility_compliance(self) -> float:
        """
        Avalia conformidade com atribuição de responsabilidades.
        
        Returns:
            float: Taxa de conformidade
        """
        valid_resp = len(self.df[
            ((self.df.iloc[:, SSAColumns.SITUACAO] != "Nova") &
            (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].notna())) |
            ((self.df.iloc[:, SSAColumns.SITUACAO].isin(["Em Execução", "Concluída"])) &
            (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()))
        ]) / len(self.df)

        return valid_resp

    def calculate_resource_utilization(self) -> Dict:
        """
        Calcula métricas de utilização de recursos.

        Returns:
            Dict: Métricas de utilização de recursos
        """
        return {
            "carga_trabalho": self._calculate_workload_metrics(),
            "distribuicao_tarefas": self._analyze_task_distribution(),
            "eficiencia_alocacao": self._analyze_allocation_efficiency(),
            "sobrecarga": self._identify_overload(),
        }

    def _calculate_workload_metrics(self) -> Dict:
        """Calcula métricas de carga de trabalho."""
        workload = {
            "programacao": {},
            "execucao": {},
            "geral": {"media_ssas_por_responsavel": 0, "desvio_padrao": 0},
        }

        # Análise de programação
        prog_counts = self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].value_counts()
        if not prog_counts.empty:
            workload["programacao"] = {
                "media": prog_counts.mean(),
                "maximo": prog_counts.max(),
                "minimo": prog_counts.min(),
                "desvio_padrao": prog_counts.std(),
            }

        # Análise de execução
        exec_counts = self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].value_counts()
        if not exec_counts.empty:
            workload["execucao"] = {
                "media": exec_counts.mean(),
                "maximo": exec_counts.max(),
                "minimo": exec_counts.min(),
                "desvio_padrao": exec_counts.std(),
            }

        # Métricas gerais
        all_resp = pd.concat(
            [
                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ]
        ).unique()
        total_resp = len([r for r in all_resp if pd.notna(r) and r.strip() != ""])

        if total_resp > 0:
            workload["geral"]["media_ssas_por_responsavel"] = len(self.df) / total_resp
            workload["geral"]["desvio_padrao"] = np.std(
                [
                    len(
                        self.df[
                            (
                                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO]
                                == resp
                            )
                            | (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                        ]
                    )
                    for resp in all_resp
                    if pd.notna(resp) and resp.strip() != ""
                ]
            )

        return workload

    def _analyze_task_distribution(self) -> Dict:
        """Analisa distribuição de tarefas."""
        distribution = {
            "por_responsavel": {},
            "por_tipo": {},
            "por_prioridade": {},
            "indices_distribuicao": {},
        }

        # Análise por responsável
        for resp in pd.concat(
            [
                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ]
        ).unique():
            if pd.notna(resp) and resp.strip() != "":
                resp_ssas = self.df[
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp)
                    | (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                ]
                distribution["por_responsavel"][resp] = {
                    "total": len(resp_ssas),
                    "criticas": len(
                        resp_ssas[
                            resp_ssas.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                            == "S3.7"
                        ]
                    ),
                    "em_execucao": len(
                        resp_ssas[
                            resp_ssas.iloc[:, SSAColumns.SITUACAO] == "Em Execução"
                        ]
                    ),
                }

        # Análise por tipo de execução
        distribution["por_tipo"] = {
            "simples": len(
                self.df[self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Sim"]
            ),
            "complexa": len(
                self.df[self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] != "Sim"]
            ),
        }

        # Análise por prioridade
        for priority in ["S3.7", "S3.6", "S3.5"]:
            priority_ssas = self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]
            distribution["por_prioridade"][priority] = {
                "total": len(priority_ssas),
                "responsaveis_unicos": len(
                    pd.concat(
                        [
                            priority_ssas.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                            priority_ssas.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
                        ]
                    ).unique()
                ),
            }

        # Cálculo de índices de distribuição
        distribution["indices_distribuicao"] = {
            "gini": self._calculate_gini_coefficient(),
            "distribuicao_relativa": self._calculate_relative_distribution(),
        }

        return distribution

    def _calculate_gini_coefficient(self) -> float:
        """Calcula coeficiente de Gini para distribuição de tarefas."""
        workload = [
            len(
                self.df[
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp)
                    | (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                ]
            )
            for resp in pd.concat(
                [
                    self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                    self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
                ]
            ).unique()
            if pd.notna(resp) and resp.strip() != ""
        ]

        workload = np.array(sorted(workload))
        n = len(workload)
        if n == 0:
            return 0

        index = np.arange(1, n + 1)
        return ((2 * np.sum((index * workload))) / (n * np.sum(workload))) - (
            (n + 1) / n
        )

    def _calculate_relative_distribution(self) -> float:
        """Calcula distribuição relativa de tarefas."""
        workload = pd.concat(
            [
                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ]
        ).value_counts()

        if workload.empty:
            return 0

        media = workload.mean()
        desvio = workload.std()

        return desvio / media if media > 0 else float("inf")

    def _analyze_allocation_efficiency(self) -> Dict:
        """Analisa eficiência da alocação de recursos."""
        efficiency = {
            "balanceamento": self._calculate_workload_balance(),
            "especializacao": self._analyze_specialization(),
            "utilizacao": self._calculate_resource_utilization(),
        }
        return efficiency

    def _calculate_workload_balance(self) -> Dict:
        """Calcula balanceamento de carga de trabalho."""
        workload = pd.concat(
            [
                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ]
        ).value_counts()

        if workload.empty:
            return {"coeficiente_variacao": 0, "max_min_ratio": 0, "dentro_limite": 0}

        media = workload.mean()
        desvio = workload.std()

        return {
            "coeficiente_variacao": desvio / media if media > 0 else float("inf"),
            "max_min_ratio": (
                workload.max() / workload.min() if workload.min() > 0 else float("inf")
            ),
            "dentro_limite": len(
                workload[(workload >= 0.8 * media) & (workload <= 1.2 * media)]
            )
            / len(workload),
        }

    def _analyze_specialization(self) -> Dict:
        """Analisa especialização dos recursos."""
        specialization = {}

        for resp in pd.concat(
            [
                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ]
        ).unique():
            if pd.notna(resp) and resp.strip() != "":
                resp_ssas = self.df[
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp)
                    | (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                ]

                if not resp_ssas.empty:
                    # Análise de tipos de SSA
                    tipos = resp_ssas.iloc[:, SSAColumns.SERVICO_ORIGEM].value_counts(
                        normalize=True
                    )
                    # Análise de equipamentos
                    equip = resp_ssas.iloc[:, SSAColumns.EQUIPAMENTO].value_counts(
                        normalize=True
                    )

                    specialization[resp] = {
                        "concentracao_tipo": (
                            1 - (-np.sum(tipos * np.log(tipos)) / np.log(len(tipos)))
                            if len(tipos) > 1
                            else 1
                        ),
                        "concentracao_equip": (
                            1 - (-np.sum(equip * np.log(equip)) / np.log(len(equip)))
                            if len(equip) > 1
                            else 1
                        ),
                    }

        return specialization

    def _calculate_resource_utilization(self) -> Dict:
        """Calcula utilização dos recursos."""
        utilization = {
            "geral": self._calculate_general_utilization(),
            "por_tipo": self._calculate_utilization_by_type(),
            "temporal": self._analyze_temporal_utilization(),
        }
        return utilization

    def _calculate_general_utilization(self) -> float:
        """Calcula utilização geral dos recursos."""
        total_resp = len(
            pd.concat(
                [
                    self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                    self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
                ]
            ).unique()
        )

        if total_resp == 0:
            return 0

        active_resp = len(
            self.df[(self.df.iloc[:, SSAColumns.SITUACAO] == "Em Execução")]
            .iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
            .unique()
        )

        return active_resp / total_resp

    def _calculate_utilization_by_type(self) -> Dict:
        """Calcula utilização por tipo de SSA."""
        utilization = {}

        for tipo in self.df.iloc[:, SSAColumns.SERVICO_ORIGEM].unique():
            tipo_ssas = self.df[self.df.iloc[:, SSAColumns.SERVICO_ORIGEM] == tipo]
            if not tipo_ssas.empty:
                resp_count = len(
                    pd.concat(
                        [
                            tipo_ssas.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                            tipo_ssas.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
                        ]
                    ).unique()
                )

                utilization[tipo] = {
                    "ssas": len(tipo_ssas),
                    "responsaveis": resp_count,
                    "media_por_resp": (
                        len(tipo_ssas) / resp_count if resp_count > 0 else 0
                    ),
                }

        return utilization

    def _analyze_temporal_utilization(self) -> Dict:
        """Analisa utilização temporal dos recursos."""
        # Agrupa por data
        daily_util = self.df.groupby(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date
        ).agg(
            {
                SSAColumns.RESPONSAVEL_PROGRAMACAO: "nunique",
                SSAColumns.RESPONSAVEL_EXECUCAO: "nunique",
            }
        )

        return {
            "media_diaria_prog": daily_util.iloc[
                :, SSAColumns.RESPONSAVEL_PROGRAMACAO
            ].mean(),
            "media_diaria_exec": daily_util.iloc[
                :, SSAColumns.RESPONSAVEL_EXECUCAO
            ].mean(),
            "pico_diario": max(
                daily_util.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].max(),
                daily_util.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].max(),
            ),
        }

    def _identify_overload(self) -> List[Dict]:
        """
        Identifica situações de sobrecarga.
        
        Returns:
            List[Dict]: Lista de situações de sobrecarga identificadas
        """
        overload = []

        # Calcula médias de referência
        avg_load = len(self.df) / len(pd.concat([
            self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
            self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
        ]).unique())

        # Analisa carga por responsável
        for resp in pd.concat([
            self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
            self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
        ]).unique():
            if pd.notna(resp) and resp.strip() != "":
                resp_ssas = self.df[
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp) |
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                ]

                if len(resp_ssas) > 1.5 * avg_load:  # 50% acima da média
                    overload.append({
                        "responsavel": resp,
                        "total_ssas": len(resp_ssas),
                        "percentual_acima_media": (len(resp_ssas) / avg_load - 1) * 100,
                        "ssas_criticas": len(resp_ssas[
                            resp_ssas.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"
                        ]),
                        "media_atraso": resp_ssas.apply(
                            lambda row: (datetime.now() - row.iloc[SSAColumns.EMITIDA_EM]).total_seconds() / 3600,
                            axis=1
                        ).mean(),
                        "recomendacao": self._generate_overload_recommendation(resp_ssas)
                    })

        return sorted(overload, key=lambda x: x["percentual_acima_media"], reverse=True)

    def _generate_overload_recommendation(self, resp_ssas: pd.DataFrame) -> str:
        """
        Gera recomendação para situação de sobrecarga.
        
        Args:
            resp_ssas: DataFrame com SSAs do responsável
            
        Returns:
            str: Recomendação gerada
        """
        critical_count = len(resp_ssas[
            resp_ssas.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"
        ])
        delayed_count = len(resp_ssas[
            resp_ssas.apply(
                lambda row: (datetime.now() - row.iloc[SSAColumns.EMITIDA_EM]).total_seconds() / 3600 > 
                self.sla_limits.get(row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO], 72),
                axis=1
            )
        ])

        recommendations = []
        if critical_count > 0:
            recommendations.append(f"Redistribuir {critical_count} SSAs críticas")
        if delayed_count > 0:
            recommendations.append(f"Priorizar {delayed_count} SSAs em atraso")
        if len(resp_ssas) > 10:  # número arbitrário para exemplo
            recommendations.append("Considerar divisão de carga com outros responsáveis")

        return "; ".join(recommendations) if recommendations else "Monitorar situação"

    def calculate_trend_indicators(self) -> Dict:
        """
        Calcula indicadores de tendência.
        
        Returns:
            Dict: Indicadores de tendência calculados
        """
        return {
            "previsao_demanda": self._forecast_demand(),
            "analise_sazonalidade": self._analyze_seasonality(),
            "padroes": self._identify_patterns(),
            "alertas": self._generate_trend_alerts()
        }

    def _forecast_demand(self) -> Dict:
        """Realiza previsão de demanda."""
        # Agrupa por data
        daily_counts = self.df.groupby(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date
        ).size()

        if len(daily_counts) < 7:  # mínimo de dados para previsão
            return {"error": "Dados insuficientes para previsão"}

        # Calcula tendência linear
        x = np.arange(len(daily_counts))
        y = daily_counts.values
        slope, intercept = np.polyfit(x, y, 1)

        # Calcula médias móveis
        rolling_mean = daily_counts.rolling(window=7).mean()

        # Projeta próximos 7 dias
        last_date = daily_counts.index[-1]
        forecast = {
            (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d"): max(
                0, round(intercept + slope * (len(daily_counts) + i))
            )
            for i in range(1, 8)
        }

        return {
            "tendencia": slope,
            "media_movel": rolling_mean.iloc[-1] if not rolling_mean.empty else 0,
            "previsao_7_dias": forecast,
            "confianca": self._calculate_forecast_confidence(
                daily_counts, slope, intercept
            ),
        }

    def _calculate_forecast_confidence(
        self, daily_counts: pd.Series, slope: float, intercept: float
    ) -> float:
        """
        Calcula nível de confiança da previsão.

        Args:
            daily_counts: Série temporal de contagens diárias
            slope: Coeficiente angular da tendência
            intercept: Intercepto da tendência

        Returns:
            float: Nível de confiança entre 0 e 1
        """
        x = np.arange(len(daily_counts))
        y_pred = slope * x + intercept

        # Calcula R²
        y_mean = daily_counts.mean()
        ss_tot = sum((daily_counts - y_mean) ** 2)
        ss_res = sum((daily_counts - y_pred) ** 2)

        r2 = 1 - (ss_res / ss_tot)

        # Ajusta confiança baseado na quantidade de dados
        confidence = r2 * min(1, len(daily_counts) / 30)  # Máximo com 30 dias de dados

        return max(0, min(1, confidence))  # Limita entre 0 e 1

    def _generate_trend_alerts(self) -> List[Dict]:
        """Gera alertas baseados em tendências."""
        alerts = []

        # Analisa tendências de volume
        volume_trend = self._analyze_volume_trend()
        if volume_trend["variacao"] > 20:  # aumento de 20%
            alerts.append(
                {
                    "tipo": "volume",
                    "severidade": "alta" if volume_trend["variacao"] > 50 else "média",
                    "mensagem": f"Aumento significativo no volume de SSAs: {volume_trend['variacao']:.1f}%",
                    "recomendacao": "Avaliar necessidade de recursos adicionais",
                }
            )

        # Analisa tendências de prioridade
        priority_trend = self._analyze_priority_trend()
        if priority_trend["variacao_criticas"] > 10:  # aumento de 10% em SSAs críticas
            alerts.append(
                {
                    "tipo": "prioridade",
                    "severidade": "alta",
                    "mensagem": f"Aumento em SSAs críticas: {priority_trend['variacao_criticas']:.1f}%",
                    "recomendacao": "Revisar alocação de recursos prioritários",
                }
            )

        return alerts

    def _analyze_volume_trend(self) -> Dict:
        """Analisa tendência de volume."""
        if len(self.df) < 2:
            return {"variacao": 0}

        # Divide período em duas metades
        mid_date = self.df.iloc[:, SSAColumns.EMITIDA_EM].median()
        first_half = len(self.df[self.df.iloc[:, SSAColumns.EMITIDA_EM] <= mid_date])
        second_half = len(self.df[self.df.iloc[:, SSAColumns.EMITIDA_EM] > mid_date])

        if first_half == 0:
            return {"variacao": float("inf")}

        variacao = ((second_half - first_half) / first_half) * 100

        return {
            "variacao": variacao,
            "primeira_metade": first_half,
            "segunda_metade": second_half,
        }

    def _analyze_priority_trend(self) -> Dict:
        """Analisa tendência de prioridades."""
        mid_date = self.df.iloc[:, SSAColumns.EMITIDA_EM].median()

        # Análise de SSAs críticas
        criticas_primeira = len(
            self.df[
                (self.df.iloc[:, SSAColumns.EMITIDA_EM] <= mid_date)
                & (self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7")
            ]
        )

        criticas_segunda = len(
            self.df[
                (self.df.iloc[:, SSAColumns.EMITIDA_EM] > mid_date)
                & (self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7")
            ]
        )

        if criticas_primeira == 0:
            variacao = float("inf")
        else:
            variacao = (
                (criticas_segunda - criticas_primeira) / criticas_primeira
            ) * 100

        return {
            "variacao_criticas": variacao,
            "criticas_primeira_metade": criticas_primeira,
            "criticas_segunda_metade": criticas_segunda,
        }

    def generate_kpi_dashboard(self) -> Dict:
        """
        TODO: Implementar dashboard de KPIs
        - Visão consolidada dos indicadores
        - Comparativos históricos
        - Metas e realizações
        - Alertas e recomendações
        """
        raise NotImplementedError

    # Métodos de suporte a serem implementados

    def _calculate_sla_compliance(self, df: pd.DataFrame) -> float:
        """
        Calcula taxa de cumprimento de SLA.

        Args:
            df: DataFrame para análise

        Returns:
            float: Taxa de cumprimento de SLA
        """
        if df.empty:
            return 0.0

        compliant = 0
        total = len(df)

        for _, row in df.iterrows():
            priority = row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            if priority in self.sla_limits:
                time_limit = self.sla_limits[priority]
                elapsed_time = abs(
                    (row.iloc[SSAColumns.EMITIDA_EM] - datetime.now()).total_seconds()
                    / 3600
                )
                if elapsed_time <= time_limit:
                    compliant += 1

        return compliant / total if total > 0 else 0.0

    def _analyze_seasonality(self) -> Dict:
        """Analisa padrões de sazonalidade."""
        seasonality = {
            "diaria": self._analyze_daily_pattern(),
            "semanal": self._analyze_weekly_pattern(),
            "mensal": self._analyze_monthly_pattern(),
        }
        return seasonality

    def _analyze_daily_pattern(self) -> Dict:
        """Analisa padrão diário."""
        if self.df.empty:
            return {}

        hourly_pattern = (
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.hour.value_counts().sort_index()
        )

        return {
            "pico": int(hourly_pattern.idxmax()),
            "vale": int(hourly_pattern.idxmin()),
            "distribuicao": hourly_pattern.to_dict(),
            "concentracao": float(hourly_pattern.max() / hourly_pattern.sum()),
        }

    def _analyze_weekly_pattern(self) -> Dict:
        """Analisa padrão semanal."""
        if self.df.empty:
            return {}

        weekly_pattern = (
            self.df.iloc[:, SSAColumns.EMITIDA_EM]
            .dt.dayofweek.value_counts()
            .sort_index()
        )
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

        return {
            "dia_pico": days[int(weekly_pattern.idxmax())],
            "dia_vale": days[int(weekly_pattern.idxmin())],
            "distribuicao": {days[i]: v for i, v in weekly_pattern.items()},
            "concentracao": float(weekly_pattern.max() / weekly_pattern.sum()),
        }

    def _analyze_monthly_pattern(self) -> Dict:
        """Analisa padrão mensal."""
        if self.df.empty:
            return {}

        monthly_pattern = self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.day.value_counts().sort_index()

        return {
            "dia_pico": int(monthly_pattern.idxmax()),
            "dia_vale": int(monthly_pattern.idxmin()),
            "distribuicao": monthly_pattern.to_dict(),
            "concentracao": float(monthly_pattern.max() / monthly_pattern.sum())
        }

    def _identify_patterns(self) -> Dict:
        """Identifica padrões nos dados."""
        patterns = {
            "volume": self._analyze_volume_patterns(),
            "prioridade": self._analyze_priority_patterns(),
            "setorial": self._analyze_sector_patterns(),
            "correlacoes": self._analyze_correlations(),
        }
        return patterns

    def _analyze_volume_patterns(self) -> Dict:
        """Analisa padrões de volume."""
        daily_volumes = self.df.groupby(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date
        ).size()

        return {
            "padrao_crescimento": (
                "crescente"
                if daily_volumes.is_monotonic_increasing
                else (
                    "decrescente"
                    if daily_volumes.is_monotonic_decreasing
                    else "variavel"
                )
            ),
            "volatilidade": (
                float(daily_volumes.std() / daily_volumes.mean())
                if not daily_volumes.empty
                else 0
            ),
            "ciclicidade": self._detect_cyclicity(daily_volumes),
        }

    def _detect_cyclicity(self, series: pd.Series) -> Dict:
        """
        Detecta ciclos na série temporal.

        Args:
            series: Série temporal para análise

        Returns:
            Dict: Informações sobre ciclos detectados
        """
        if len(series) < 14:  # mínimo de 2 semanas
            return {"detected": False}

        # Calcula autocorrelação
        autocorr = pd.Series(series).autocorr(lag=7)  # correlação semanal

        return {
            "detected": abs(autocorr) > 0.3,  # limite arbitrário para exemplo
            "forca_semanal": float(autocorr),
            "tipo": "semanal" if abs(autocorr) > 0.3 else "não identificado",
        }

    def get_overall_health_score(self) -> float:
        """
        Calcula score geral de saúde do sistema.
        
        Returns:
            float: Score de 0 a 100
        """
        metrics = self.calculate_efficiency_metrics()
        quality = self.calculate_quality_metrics()
        responsiveness = self.calculate_responsiveness_metrics()

        # Pesos para diferentes aspectos
        weights = {
            "programacao": 0.2,
            "execucao": 0.3,
            "sla": 0.3,
            "qualidade": 0.2
        }

        score = (
            metrics["taxa_programacao"] * weights["programacao"] +
            metrics["taxa_execucao_simples"] * weights["execucao"] +
            self._calculate_sla_compliance(self.df) * weights["sla"] +
            self._calculate_quality_score(quality) * weights["qualidade"]
        )

        return round(score * 100, 2)

    def _calculate_quality_score(self, quality_metrics: Dict) -> float:
        """
        Calcula score de qualidade normalizado.

        Args:
            quality_metrics: Métricas de qualidade calculadas

        Returns:
            float: Score de qualidade entre 0 e 1
        """
        if not quality_metrics:
            return 0

        scores = []

        # Avalia taxa de retrabalho
        if "taxa_retrabalho" in quality_metrics:
            rework_score = 1 - quality_metrics["taxa_retrabalho"].get("geral", 0)
            scores.append(rework_score)

        # Avalia qualidade da documentação
        if "qualidade_documentacao" in quality_metrics:
            doc_metrics = quality_metrics["qualidade_documentacao"]
            doc_score = doc_metrics.get("completude", 0)
            scores.append(doc_score)

        # Avalia conformidade com procedimentos
        if "conformidade_procedimentos" in quality_metrics:
            proc_metrics = quality_metrics["conformidade_procedimentos"]
            proc_score = np.mean(
                [
                    proc_metrics.get("documentacao", 0),
                    proc_metrics.get("sla", 0),
                    proc_metrics.get("fluxo_trabalho", 0),
                ]
            )
            scores.append(proc_score)

        return np.mean(scores) if scores else 0

    def generate_health_report(self) -> Dict:
        """
        Gera relatório completo de saúde do sistema.

        Returns:
            Dict: Relatório detalhado de saúde
        """
        score = self.get_overall_health_score()

        return {
            "score_geral": score,
            "status": self._get_health_status(score),
            "metricas_principais": self._get_main_metrics(),
            "areas_criticas": self._identify_critical_areas(),
            "recomendacoes": self._generate_recommendations(),
            "tendencias": self._get_trend_summary(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _get_health_status(self, score: float) -> Dict:
        """
        Determina status de saúde baseado no score.

        Args:
            score: Score de saúde calculado

        Returns:
            Dict: Status detalhado do sistema
        """
        if score >= 90:
            status = "Excelente"
            description = "Sistema operando em condições ótimas"
            color = "green"
        elif score >= 75:
            status = "Bom"
            description = (
                "Sistema operando normalmente com pequenas melhorias necessárias"
            )
            color = "lightgreen"
        elif score >= 60:
            status = "Regular"
            description = "Sistema operacional mas requer atenção em algumas áreas"
            color = "yellow"
        elif score >= 40:
            status = "Preocupante"
            description = "Sistema necessita de intervenções importantes"
            color = "orange"
        else:
            status = "Crítico"
            description = "Sistema requer ação imediata"
            color = "red"

        return {"status": status, "description": description, "color": color}

    def _get_main_metrics(self) -> Dict:
        """
        Obtém métricas principais sumarizadas.

        Returns:
            Dict: Principais métricas do sistema
        """
        return {
            "volume": {
                "total": len(self.df),
                "media_diaria": len(self.df)
                / len(self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date.unique()),
            },
            "sla": {
                "cumprimento": self._calculate_sla_compliance(self.df),
                "tempo_medio_resposta": self._calculate_avg_response_time(),
            },
            "qualidade": {
                "completude_dados": self._calculate_documentation_completeness(),
                "taxa_retrabalho": self._calculate_rework_rate().get("geral", 0),
            },
            "recursos": {
                "utilizacao": self._calculate_resource_utilization().get("geral", 0),
                "balanceamento": self._calculate_workload_balance(),
            },
        }

    def _identify_critical_areas(self) -> List[Dict]:
        """
        Identifica áreas críticas que requerem atenção.

        Returns:
            List[Dict]: Lista de áreas críticas identificadas
        """
        critical_areas = []

        # Verifica SLA
        sla_compliance = self._calculate_sla_compliance(self.df)
        if sla_compliance < 0.8:  # menos de 80% de cumprimento
            critical_areas.append(
                {
                    "area": "SLA",
                    "severidade": "alta" if sla_compliance < 0.6 else "média",
                    "metrica": f"{sla_compliance*100:.1f}% de cumprimento",
                    "impacto": "Alto risco de insatisfação e atrasos",
                }
            )

        # Verifica carga de trabalho
        workload = self._calculate_workload_balance()
        if workload.get("coeficiente_variacao", 0) > 0.5:  # alta variação
            critical_areas.append(
                {
                    "area": "Distribuição de Carga",
                    "severidade": (
                        "alta" if workload["coeficiente_variacao"] > 0.8 else "média"
                    ),
                    "metrica": f"Variação de {workload['coeficiente_variacao']:.2f}",
                    "impacto": "Possível sobrecarga em alguns recursos",
                }
            )

        # Verifica qualidade
        quality_score = self._calculate_quality_score(self.calculate_quality_metrics())
        if quality_score < 0.7:  # menos de 70% de qualidade
            critical_areas.append(
                {
                    "area": "Qualidade",
                    "severidade": "alta" if quality_score < 0.5 else "média",
                    "metrica": f"{quality_score*100:.1f}% de score",
                    "impacto": "Risco de retrabalho e inconsistências",
                }
            )

        return critical_areas

    def _generate_recommendations(self) -> List[Dict]:
        """
        Gera recomendações baseadas na análise.

        Returns:
            List[Dict]: Lista de recomendações
        """
        recommendations = []

        # Analisa problemas de SLA
        sla_issues = self._identify_critical_delays()
        if sla_issues:
            recommendations.append(
                {
                    "tipo": "SLA",
                    "prioridade": "alta",
                    "acao": "Revisar processo de atendimento",
                    "detalhes": f"Existem {len(sla_issues)} SSAs com atrasos críticos",
                    "impacto_esperado": "Melhoria no tempo de resposta e satisfação",
                }
            )

        # Analisa distribuição de carga
        workload = self._calculate_workload_balance()
        if workload.get("coeficiente_variacao", 0) > 0.5:
            recommendations.append(
                {
                    "tipo": "Recursos",
                    "prioridade": "média",
                    "acao": "Redistribuir carga de trabalho",
                    "detalhes": "Alta variação na distribuição de SSAs",
                    "impacto_esperado": "Melhor utilização dos recursos disponíveis",
                }
            )

        # Analisa qualidade da documentação
        doc_quality = self._assess_documentation_quality()
        if doc_quality.get("completude", 1) < 0.8:
            recommendations.append(
                {
                    "tipo": "Qualidade",
                    "prioridade": "média",
                    "acao": "Melhorar documentação das SSAs",
                    "detalhes": "Documentação incompleta ou inadequada",
                    "impacto_esperado": "Melhor rastreabilidade e qualidade do serviço",
                }
            )

        return recommendations

    def _get_trend_summary(self) -> Dict:
        """
        Gera sumário das principais tendências.

        Returns:
            Dict: Sumário de tendências identificadas
        """
        trends = self.calculate_trend_indicators()

        return {
            "volume": {
                "direcao": (
                    "crescente"
                    if trends["previsao_demanda"].get("tendencia", 0) > 0
                    else "decrescente"
                ),
                "variacao": f"{abs(trends['previsao_demanda'].get('tendencia', 0)):.1f}%",
            },
            "sazonalidade": {
                "padrao": trends["analise_sazonalidade"]["diaria"].get(
                    "pico", "não identificado"
                ),
                "confianca": trends["previsao_demanda"].get("confianca", 0),
            },
            "alertas": len(trends["alertas"]),
            "previsao_proxima_semana": trends["previsao_demanda"].get(
                "previsao_7_dias", {}
            ),
        }

    def _calculate_avg_response_time(self) -> float:
        """
        Calcula tempo médio de resposta global.
        
        Returns:
            float: Tempo médio em horas
        """
        if self.df.empty:
            return 0

        response_times = self.df.apply(
            lambda row: (datetime.now() - row.iloc[SSAColumns.EMITIDA_EM]).total_seconds() / 3600,
            axis=1
        )

        return abs(response_times.mean())

    def get_summary_dashboard(self) -> Dict:
        """
        Gera dados para dashboard resumido.

        Returns:
            Dict: Dados formatados para dashboard
        """
        return {
            "score": {
                "valor": self.get_overall_health_score(),
                "status": self._get_health_status(self.get_overall_health_score()),
                "tendencia": self._analyze_score_trend(),
            },
            "metricas": self._get_main_metrics(),
            "areas_criticas": self._identify_critical_areas(),
            "recomendacoes": self._generate_recommendations()[:3],  # top 3
            "tendencias": self._get_trend_summary(),
        }


    def _analyze_score_trend(self) -> Dict:
        """
        Analisa tendência do score de saúde.
        
        Returns:
            Dict: Análise da tendência do score
        """
        # Divide o período em intervalos
        dates = self.df.iloc[:, SSAColumns.EMITIDA_EM].sort_values()
        total_days = (dates.max() - dates.min()).days
        interval_days = max(1, total_days // 5)  # divide em até 5 períodos
        
        scores = []
        periods = []
        current_date = dates.min()
        
        while current_date <= dates.max():
            next_date = current_date + pd.Timedelta(days=interval_days)
            period_df = self.df[
                (self.df.iloc[:, SSAColumns.EMITIDA_EM] >= current_date) &
                (self.df.iloc[:, SSAColumns.EMITIDA_EM] < next_date)
            ]
            
            if not period_df.empty:
                # Calcula score para o período
                period_score = self.kpi_calculator.get_overall_health_score(period_df)
                scores.append(period_score)
                periods.append(current_date)
            
            current_date = next_date
        
        if len(scores) < 2:
            return {
                "direction": "estável",
                "variation": 0,
                "trend": "insufficient_data"
            }
        
        # Calcula tendência
        slope = np.polyfit(range(len(scores)), scores, 1)[0]
        variation = ((scores[-1] - scores[0]) / scores[0]) * 100 if scores[0] != 0 else float('inf')
        
        result = {
            "direction": "melhorando" if slope > 0 else "piorando",
            "variation": abs(variation),
            "trend": "consistent" if abs(variation) > 10 else "stable",
            "scores": list(zip(periods, scores)),
            "slope": slope
        }
        
        # Adiciona previsão
        if len(scores) >= 3:
            next_score = scores[-1] + slope
            result["forecast"] = {
                "next_period": next_score,
                "confidence": min(1.0, len(scores) / 10)  # maior confiança com mais dados
            }
        
        return result

    def _analyze_bottlenecks(self) -> Dict:
        """
        Analisa gargalos no sistema.

        Returns:
            Dict: Análise de gargalos identificados
        """
        bottlenecks = {"processes": [], "resources": [], "delays": []}

        # Analisa gargalos de processo
        process_times = {}
        for estado in self.df.iloc[:, SSAColumns.SITUACAO].unique():
            estado_df = self.df[self.df.iloc[:, SSAColumns.SITUACAO] == estado]
            avg_time = (
                estado_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
            ).dt.total_seconds() / 3600
            process_times[estado] = abs(avg_time.mean())

            if abs(avg_time.mean()) > 48:  # mais de 48 horas
                bottlenecks["processes"].append(
                    {
                        "type": "estado",
                        "value": estado,
                        "avg_time": abs(avg_time.mean()),
                        "affected_ssas": len(estado_df),
                        "suggestion": (
                            "Revisar processo de aprovação"
                            if "ADM" in estado
                            else "Aumentar recursos disponíveis"
                        ),
                    }
                )

        # Analisa gargalos de recursos
        resource_load = {}
        for resp in pd.concat(
            [
                self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO],
            ]
        ).unique():
            if pd.notna(resp) and resp.strip() != "":
                resp_ssas = self.df[
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp)
                    | (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                ]
                resource_load[resp] = len(resp_ssas)

                if len(resp_ssas) > 10:  # limite arbitrário para exemplo
                    bottlenecks["resources"].append(
                        {
                            "type": "responsavel",
                            "value": resp,
                            "workload": len(resp_ssas),
                            "critical_ssas": len(
                                resp_ssas[
                                    resp_ssas.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                                    == "S3.7"
                                ]
                            ),
                            "suggestion": "Redistribuir carga de trabalho",
                        }
                    )

        # Analisa atrasos significativos
        for priority in ["S3.7", "S3.6", "S3.5"]:
            priority_df = self.df[
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]
            for setor in priority_df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
                setor_df = priority_df[
                    priority_df.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor
                ]
                avg_delay = (
                    setor_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                ).dt.total_seconds() / 3600

                if abs(avg_delay.mean()) > 24:  # mais de 24 horas
                    bottlenecks["delays"].append(
                        {
                            "type": "atraso",
                            "setor": setor,
                            "prioridade": priority,
                            "avg_delay": abs(avg_delay.mean()),
                            "affected_ssas": len(setor_df),
                            "suggestion": (
                                "Priorizar SSAs críticas"
                                if priority == "S3.7"
                                else "Revisar processo de atendimento"
                            ),
                        }
                    )

        return bottlenecks


    def _calculate_efficiency_by_type(self) -> Dict:
        """
        Calcula eficiência por tipo de SSA.

        Returns:
            Dict: Métricas de eficiência por tipo
        """
        efficiency_metrics = {"por_servico": {}, "por_categoria": {}, "comparativos": {}}

        # Análise por serviço de origem
        for servico in self.df.iloc[:, SSAColumns.SERVICO_ORIGEM].unique():
            servico_df = self.df[self.df.iloc[:, SSAColumns.SERVICO_ORIGEM] == servico]

            # Calcula métricas
            total_ssas = len(servico_df)
            concluidas = len(
                servico_df[
                    servico_df.iloc[:, SSAColumns.SITUACAO].isin(["Concluída", "Fechada"])
                ]
            )
            tempo_medio = abs(
                (
                    servico_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                ).dt.total_seconds()
                / 3600
            ).mean()

            efficiency_metrics["por_servico"][servico] = {
                "total_ssas": total_ssas,
                "taxa_conclusao": concluidas / total_ssas if total_ssas > 0 else 0,
                "tempo_medio": tempo_medio,
                "execucao_simples": (
                    len(
                        servico_df[servico_df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Sim"]
                    )
                    / total_ssas
                    if total_ssas > 0
                    else 0
                ),
            }

        # Análise por categoria (baseado em execução simples)
        for is_simple in [True, False]:
            categoria_df = self.df[
                self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES]
                == ("Sim" if is_simple else "Não")
            ]

            if not categoria_df.empty:
                total = len(categoria_df)
                efficiency_metrics["por_categoria"][
                    "simples" if is_simple else "complexa"
                ] = {
                    "total_ssas": total,
                    "tempo_medio": abs(
                        (
                            categoria_df.iloc[:, SSAColumns.EMITIDA_EM] - datetime.now()
                        ).dt.total_seconds()
                        / 3600
                    ).mean(),
                    "taxa_programacao": len(
                        categoria_df[
                            categoria_df.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()
                        ]
                    )
                    / total,
                    "taxa_execucao": len(
                        categoria_df[
                            categoria_df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()
                        ]
                    )
                    / total,
                }

        # Comparativos entre tipos
        all_metrics = efficiency_metrics["por_servico"]
        if all_metrics:
            avg_tempo = np.mean([m["tempo_medio"] for m in all_metrics.values()])
            efficiency_metrics["comparativos"] = {
                "servicos_acima_media": [
                    servico
                    for servico, metrics in all_metrics.items()
                    if metrics["tempo_medio"] > avg_tempo
                ],
                "servicos_mais_eficientes": sorted(
                    all_metrics.keys(),
                    key=lambda x: all_metrics[x]["taxa_conclusao"],
                    reverse=True,
                )[:3],
                "distribuicao_complexidade": {
                    "simples": len(
                        self.df[self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Sim"]
                    )
                    / len(self.df),
                    "complexa": len(
                        self.df[self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Não"]
                    )
                    / len(self.df),
                },
            }

        return efficiency_metrics


    def _generate_performance_alerts(self) -> List[Dict]:
        """
        Gera alertas de performance.
        
        Returns:
            List[Dict]: Lista de alertas gerados
        """
        alerts = []
        
        # Define limiares
        thresholds = {
            "sla": 0.8,  # 80% de cumprimento
            "workload": 10,  # máximo de SSAs por responsável
            "delay": 48,  # máximo de horas de atraso
            "critical": 0.2  # 20% de SSAs críticas
        }
        
        # Verifica SLA
        sla_compliance = self._calculate_sla_compliance(self.df)
        if sla_compliance < thresholds["sla"]:
            alerts.append({
                "type": "sla",
                "severity": "high",
                "metric": "Cumprimento de SLA",
                "value": sla_compliance,
                "threshold": thresholds["sla"],
                "message": f"Taxa de cumprimento de SLA ({sla_compliance*100:.1f}%) abaixo do esperado",
                "recommendation": "Revisar processos de atendimento e alocação de recursos"
            })
        
        # Verifica carga de trabalho
        workload = {}
        for resp in pd.concat([
            self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
            self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
        ]).unique():
            if pd.notna(resp) and resp.strip() != "":
                resp_ssas = self.df[
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp) |
                    (self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp)
                ]
                workload[resp] = len(resp_ssas)
                
                if len(resp_ssas) > thresholds["workload"]:
                    alerts.append({
                        "type": "workload",
                        "severity": "medium",
                        "metric": "Carga de Trabalho",
                        "resource": resp,
                        "value": len(resp_ssas),
                        "threshold": thresholds["workload"],
                        "message": f"Sobrecarga detectada para {resp}",
                        "recommendation": "Redistribuir SSAs entre responsáveis"
                    })
        
        # Verifica atrasos
        delays = self.df.apply(
            lambda row: (datetime.now() - row.iloc[SSAColumns.EMITIDA_EM]).total_seconds() / 3600,
            axis=1
        )
        if delays.max() > thresholds["delay"]:
            delayed_ssas = self.df[delays > thresholds["delay"]]
            alerts.append({
                "type": "delay",
                "severity": "high",
                "metric": "Tempo de Atendimento",
                "value": delays.max(),
                "threshold": thresholds["delay"],
                "affected_ssas": len(delayed_ssas),
                "message": f"SSAs com atraso significativo detectadas",
                "recommendation": "Priorizar SSAs mais antigas"
            })
        
        # Verifica proporção de SSAs críticas
        critical_ratio = len(self.df[
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"
        ]) / len(self.df)
        
        if critical_ratio > thresholds["critical"]:
            alerts.append({
                "type": "critical",
                "severity": "high",
                "metric": "SSAs Críticas",
                "value": critical_ratio,
                "threshold": thresholds["critical"],
                "message": f"Alta proporção de SSAs críticas ({critical_ratio*100:.1f}%)",
                "recommendation": "Investigar causa raiz do aumento de SSAs críticas"
            })
        
        return alerts


class SSADashboard:
    """Dashboard interativo para análise de SSAs."""

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o dashboard.
        
        Args:
            df (pd.DataFrame): DataFrame com os dados das SSAs
        """
        self.df = df
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )

        # Componentes
        self.theme = DashboardTheme()
        self.visualizer = SSAVisualizer(df)
        self.analyzer = SSAAnalyzer(df)
        self.kpi_calculator = KPICalculator(df)

        # Inicializa cache de dados
        self._cache = {}

        # Setup inicial
        self.setup_layout()
        self.setup_callbacks()
        self._setup_export_callbacks()
        self._setup_analysis_callbacks()
        self._setup_alert_system()
        self._setup_customization_options()

    def setup_layout(self):
        """Setup the dashboard layout with basic components"""
        self.app.layout = html.Div(
            [
                html.H1("SSA Dashboard", className="text-center mb-4"),
                # Summary statistics
                html.Div(
                    [
                        html.Div(
                            [html.H4("Total SSAs"), html.H2(len(self.df))],
                            className="stats-card",
                        ),
                        html.Div(
                            [
                                html.H4("Prioridades"),
                                dcc.Graph(figure=self.create_priority_chart()),
                            ],
                            className="stats-card",
                        ),
                    ]
                ),
                # Time series chart
                html.Div(
                    [
                        html.H3("SSAs ao longo do tempo"),
                        dcc.Graph(figure=self.create_timeline_chart()),
                    ]
                ),
                # Data table
                html.Div([html.H3("Lista de SSAs"), self.create_data_table()]),
            ]
        )

    def create_priority_chart(self):
        """Create a bar chart showing SSA priorities"""
        priority_counts = self.df["PRIORIDADE"].value_counts()
        fig = px.bar(
            x=priority_counts.index,
            y=priority_counts.values,
            title="Distribuição de Prioridades",
        )
        return fig

    def create_timeline_chart(self):
        """Create a timeline chart of SSAs"""
        daily_counts = self.df.groupby("EMITIDA_EM").size().reset_index(name="count")
        fig = px.line(daily_counts, x="EMITIDA_EM", y="count", title="SSAs por Data")
        return fig

    def create_data_table(self):
        """Create a data table component"""
        return dash.dash_table.DataTable(
            data=self.df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in self.df.columns],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left"},
        )

    def run(self, debug=False):
        """Run the dashboard server"""
        self.app.run_server(debug=debug)

    def _create_advanced_charts(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """
        Cria visualizações avançadas e interativas.
        
        Args:
            df: DataFrame filtrado para análise
            
        Returns:
            Dict[str, go.Figure]: Dicionário de visualizações
        """
        charts = {
            "temporal": self._create_temporal_visualization(df),
            "network": self._create_network_visualization(df),
            "sankey": self._create_flow_visualization(df),
            "treemap": self._create_hierarchy_visualization(df),
            "heatmap": self._create_correlation_heatmap(df)
        }

        return charts

    def _create_temporal_visualization(self, df: pd.DataFrame) -> go.Figure:
        """Cria visualização temporal interativa."""
        if df.empty:
            return go.Figure()

        # Prepara dados
        temporal_data = df.groupby([
            df.iloc[:, SSAColumns.EMITIDA_EM].dt.date,
            df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
        ]).size().reset_index(name='count')

        # Cria gráfico
        fig = go.Figure()

        for priority in temporal_data.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].unique():
            priority_data = temporal_data[
                temporal_data.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            ]

            fig.add_trace(go.Scatter(
                x=priority_data.iloc[:, SSAColumns.EMITIDA_EM],
                y=priority_data['count'],
                name=priority,
                mode='lines+markers',
                line=dict(
                    width=2,
                    color=DashboardTheme.get_priority_color(priority)
                ),
                marker=dict(
                    size=8,
                    symbol='circle',
                    color=DashboardTheme.get_priority_color(priority)
                ),
                hovertemplate=(
                    "<b>Data:</b> %{x}<br>" +
                    "<b>SSAs:</b> %{y}<br>" +
                    "<b>Prioridade:</b> " + priority +
                    "<extra></extra>"
                )
            ))

        # Configurações do layout
        fig.update_layout(
            title="Evolução Temporal de SSAs por Prioridade",
            xaxis_title="Data",
            yaxis_title="Quantidade de SSAs",
            template="plotly_white",
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            updatemenus=[
                dict(
                    buttons=[
                        dict(
                            args=[{"visible": [True] * len(fig.data)}],
                            label="Todas",
                            method="update"
                        )
                    ] + [
                        dict(
                            args=[{"visible": [i == j for i in range(len(fig.data))]}],
                            label=priority,
                            method="update"
                        )
                        for j, priority in enumerate(temporal_data.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].unique())
                    ],
                    direction="down",
                    showactive=True,
                    x=0.1,
                    xanchor="left",
                    y=1.1,
                    yanchor="top"
                )
            ]
        )

        return fig

    def _create_network_visualization(self, df: pd.DataFrame) -> go.Figure:
        """Cria visualização de rede de relacionamentos."""
        if df.empty:
            return go.Figure()

        # Prepara dados de relacionamento
        relationships = []
        for setor in df.iloc[:, SSAColumns.SETOR_EMISSOR].unique():
            setor_df = df[df.iloc[:, SSAColumns.SETOR_EMISSOR] == setor]
            for executor in setor_df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
                count = len(setor_df[setor_df.iloc[:, SSAColumns.SETOR_EXECUTOR] == executor])
                relationships.append((setor, executor, count))

        # Cria nós únicos
        nodes = list(set([r[0] for r in relationships] + [r[1] for r in relationships]))
        node_indices = {node: i for i, node in enumerate(nodes)}

        # Prepara dados para visualização
        edge_x = []
        edge_y = []
        edge_weights = []
        node_adjacencies = {node: [] for node in nodes}

        for start, end, weight in relationships:
            x0, y0 = self._get_node_position(node_indices[start], len(nodes))
            x1, y1 = self._get_node_position(node_indices[end], len(nodes))

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(weight)

            node_adjacencies[start].append(end)
            node_adjacencies[end].append(start)

        # Cria gráfico
        fig = go.Figure()

        # Adiciona arestas
        fig.add_trace(go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            line=dict(
                width=np.array(edge_weights) / max(edge_weights) * 5,
                color='#888'
            ),
            hoverinfo='none'
        ))

        # Adiciona nós
        node_x = []
        node_y = []
        node_text = []
        node_sizes = []

        for node in nodes:
            x, y = self._get_node_position(node_indices[node], len(nodes))
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"Setor: {node}<br>Conexões: {len(node_adjacencies[node])}")
            node_sizes.append(len(node_adjacencies[node]) * 20)

        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=DashboardTheme.COLORS["primary"],
                line=dict(width=2, color='white')
            ),
            text=nodes,
            textposition="top center",
            hovertext=node_text,
            hoverinfo='text'
        ))

        # Configuração do layout
        fig.update_layout(
            title="Rede de Relacionamentos entre Setores",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            template="plotly_white",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        return fig

    def _get_node_position(self, index: int, total_nodes: int) -> Tuple[float, float]:
        """
        Calcula posição do nó em círculo.
        
        Args:
            index: Índice do nó
            total_nodes: Total de nós
            
        Returns:
            Tuple[float, float]: Coordenadas x, y
        """
        angle = 2 * np.pi * index / total_nodes
        return np.cos(angle), np.sin(angle)

    def _create_flow_visualization(self, df: pd.DataFrame) -> go.Figure:
        """Cria visualização de fluxo Sankey."""
        if df.empty:
            return go.Figure()

        # Prepara dados para o diagrama Sankey
        flow_data = []
        # Emissor -> Executor -> Estado
        for _, row in df.iterrows():
            flow_data.append({
                'source': row.iloc[SSAColumns.SETOR_EMISSOR],
                'target': row.iloc[SSAColumns.SETOR_EXECUTOR],
                'value': 1,
                'priority': row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            })
            flow_data.append({
                'source': row.iloc[SSAColumns.SETOR_EXECUTOR],
                'target': row.iloc[SSAColumns.SITUACAO],
                'value': 1,
                'priority': row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
            })

        # Cria listas únicas de nós
        all_nodes = list(set(
            [d['source'] for d in flow_data] +
            [d['target'] for d in flow_data]
        ))
        node_indices = {node: i for i, node in enumerate(all_nodes)}

        # Prepara dados para plotly
        link_sources = [node_indices[d['source']] for d in flow_data]
        link_targets = [node_indices[d['target']] for d in flow_data]
        link_values = [d['value'] for d in flow_data]
        link_colors = [DashboardTheme.get_priority_color(d['priority']) for d in flow_data]

        # Cria figura
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=DashboardTheme.COLORS["light"]
            ),
            link=dict(
                source=link_sources,
                target=link_targets,
                value=link_values,
                color=link_colors
            )
        )])

        # Configuração do layout
        fig.update_layout(
            title="Fluxo de SSAs no Sistema",
            font_size=10,
            template="plotly_white"
        )

        return fig

    def _create_hierarchy_visualization(self, df: pd.DataFrame) -> go.Figure:
        """Cria visualização hierárquica (treemap)."""
        if df.empty:
            return go.Figure()

        # Prepara dados hierárquicos
        hierarchy_data = []
        for setor in df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            setor_df = df[df.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor]

            for priority in setor_df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].unique():
                priority_df = setor_df[
                    setor_df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
                ]

                for status in priority_df.iloc[:, SSAColumns.SITUACAO].unique():
                    count = len(priority_df[
                        priority_df.iloc[:, SSAColumns.SITUACAO] == status
                    ])

                    hierarchy_data.append({
                        "setor": setor,
                        "prioridade": priority,
                        "status": status,
                        "count": count
                    })

        # Cria listas para treemap
        labels = []
        parents = []
        values = []
        colors = []

        # Nível 1: Setores
        for setor in df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            labels.append(setor)
            parents.append("")
            values.append(len(df[df.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor]))
            colors.append(DashboardTheme.COLORS["primary"])

        # Nível 2: Prioridades
        for item in hierarchy_data:
            setor_priority = f"{item['setor']}_{item['prioridade']}"
            if setor_priority not in labels:
                labels.append(setor_priority)
                parents.append(item['setor'])
                values.append(sum([
                    i['count'] for i in hierarchy_data
                    if i['setor'] == item['setor'] and i['prioridade'] == item['prioridade']
                ]))
                colors.append(DashboardTheme.get_priority_color(item['prioridade']))

        # Nível 3: Status
        for item in hierarchy_data:
            if item['count'] > 0:
                label = f"{item['setor']}_{item['prioridade']}_{item['status']}"
                labels.append(label)
                parents.append(f"{item['setor']}_{item['prioridade']}")
                values.append(item['count'])
                colors.append(DashboardTheme.get_state_color(item['status']))

        # Cria figura
        fig = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            marker=dict(colors=colors),
            textinfo="label+value",
            hovertemplate=(
                "<b>%{label}</b><br>" +
                "Quantidade: %{value}<br>" +
                "<extra></extra>"
            )
        ))

        # Configuração do layout
        fig.update_layout(
            title="Distribuição Hierárquica de SSAs",
            template="plotly_white"
        )

        return fig

    def _create_correlation_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """
        Cria mapa de calor de correlações.
        
        Args:
            df: DataFrame para análise
            
        Returns:
            go.Figure: Mapa de calor de correlações
        """
        if df.empty:
            return go.Figure()

        # Prepara dados para correlação
        correlation_data = pd.DataFrame({
            'setor': df.iloc[:, SSAColumns.SETOR_EXECUTOR],
            'prioridade': df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
            'status': df.iloc[:, SSAColumns.SITUACAO],
            'tempo_resposta': (datetime.now() - df.iloc[:, SSAColumns.EMITIDA_EM]).dt.total_seconds() / 3600,
            'execucao_simples': df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == 'Sim',
            'tem_programacao': df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].notna(),
            'tem_execucao': df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna()
        })

        # Codifica variáveis categóricas
        correlation_data = pd.get_dummies(correlation_data, columns=['setor', 'prioridade', 'status'])

        # Calcula correlações
        corr_matrix = correlation_data.corr()

        # Cria mapa de calor
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            colorbar=dict(
                title='Correlação',
                titleside='right'
            ),
            hoverongaps=False,
            hovertemplate=(
                "<b>X:</b> %{x}<br>" +
                "<b>Y:</b> %{y}<br>" +
                "<b>Correlação:</b> %{z:.2f}<br>" +
                "<extra></extra>"
            )
        ))

        # Configuração do layout
        fig.update_layout(
            title="Mapa de Correlações entre Variáveis",
            template="plotly_white",
            xaxis=dict(tickangle=45),
            yaxis=dict(tickangle=0)
        )

        return fig

    def _create_predictive_visualizations(self, df: pd.DataFrame) -> Dict[str, go.Figure]:
        """
        Cria visualizações preditivas.
        
        Args:
            df: DataFrame para análise
            
        Returns:
            Dict[str, go.Figure]: Visualizações preditivas
        """
        predictions = {
            "volume": self._create_volume_prediction(df),
            "sla": self._create_sla_prediction(df),
            "workload": self._create_workload_prediction(df),
            "trends": self._create_trend_prediction(df)
        }

        return predictions

    def _create_volume_prediction(self, df: pd.DataFrame) -> go.Figure:
        """Cria previsão de volume."""
        if df.empty:
            return go.Figure()

        # Agrupa por data
        daily_volume = df.groupby(
            df.iloc[:, SSAColumns.EMITIDA_EM].dt.date
        ).size().reset_index()
        daily_volume.columns = ['date', 'volume']

        # Prepara dados para previsão
        X = np.arange(len(daily_volume)).reshape(-1, 1)
        y = daily_volume['volume'].values

        # Ajusta modelo linear
        model = LinearRegression()
        model.fit(X, y)

        # Projeta próximos 7 dias
        future_dates = [
            daily_volume['date'].iloc[-1] + pd.Timedelta(days=i)
            for i in range(1, 8)
        ]
        future_X = np.arange(len(X), len(X) + 7).reshape(-1, 1)
        predictions = model.predict(future_X)

        # Cria visualização
        fig = go.Figure()

        # Dados históricos
        fig.add_trace(go.Scatter(
            x=daily_volume['date'],
            y=daily_volume['volume'],
            mode='lines+markers',
            name='Histórico',
            line=dict(color=DashboardTheme.COLORS["primary"])
        ))

        # Previsões
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Previsão',
            line=dict(
                color=DashboardTheme.COLORS["warning"],
                dash='dash'
            )
        ))

        # Intervalo de confiança
        confidence = np.std(y) * 1.96  # 95% de confiança
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions + confidence,
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions - confidence,
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(68, 68, 68, 0.2)',
            fill='tonexty',
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.update_layout(
            title="Previsão de Volume de SSAs",
            xaxis_title="Data",
            yaxis_title="Quantidade de SSAs",
            template="plotly_white",
            hovermode='x unified'
        )

        return fig

    def _create_sla_prediction(self, df: pd.DataFrame) -> go.Figure:
        """Cria previsão de cumprimento de SLA."""
        if df.empty:
            return go.Figure()

        # Calcula cumprimento de SLA por dia
        sla_compliance = []
        for date in df.iloc[:, SSAColumns.EMITIDA_EM].dt.date.unique():
            day_df = df[df.iloc[:, SSAColumns.EMITIDA_EM].dt.date == date]
            compliance = self.kpi_calculator._calculate_sla_compliance(day_df)
            sla_compliance.append({
                'date': date,
                'compliance': compliance
            })

        sla_df = pd.DataFrame(sla_compliance)

        # Prepara dados para previsão
        X = np.arange(len(sla_df)).reshape(-1, 1)
        y = sla_df['compliance'].values

        # Ajusta modelo logístico
        model = LogisticRegression()
        model.fit(X, y > 0.8)  # Classifica como bom se > 80%

        # Projeta próximos 7 dias
        future_dates = [
            sla_df['date'].iloc[-1] + pd.Timedelta(days=i)
            for i in range(1, 8)
        ]
        future_X = np.arange(len(X), len(X) + 7).reshape(-1, 1)
        predictions_prob = model.predict_proba(future_X)[:, 1]

        # Cria visualização
        fig = go.Figure()

        # Dados históricos
        fig.add_trace(go.Scatter(
            x=sla_df['date'],
            y=sla_df['compliance'],
            mode='lines+markers',
            name='Histórico',
            line=dict(color=DashboardTheme.COLORS["primary"])
        ))

        # Previsões
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions_prob,
            mode='lines+markers',
            name='Probabilidade',
            line=dict(
                color=DashboardTheme.COLORS["warning"],
                dash='dash'
            )
        ))

        # Linha de meta
        fig.add_hline(
            y=0.8,
            line_dash="dot",
            line_color="red",
            annotation_text="Meta (80%)"
        )

        fig.update_layout(
            title="Previsão de Cumprimento de SLA",
            xaxis_title="Data",
            yaxis_title="Taxa de Cumprimento",
            template="plotly_white",
            hovermode='x unified'
        )

        return fig

    def _create_workload_prediction(self, df: pd.DataFrame) -> go.Figure:
        """Cria previsão de carga de trabalho."""
        if df.empty:
            return go.Figure()

        # Calcula carga por responsável por dia
        workload_data = []
        for date in df.iloc[:, SSAColumns.EMITIDA_EM].dt.date.unique():
            day_df = df[df.iloc[:, SSAColumns.EMITIDA_EM].dt.date == date]

            # Conta SSAs ativas por responsável
            active_ssas = day_df[
                ~day_df.iloc[:, SSAColumns.SITUACAO].isin(['Concluída', 'Fechada'])
            ]

            workload = len(active_ssas) / len(
                pd.concat([
                    active_ssas.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO],
                    active_ssas.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
                ]).unique()
            ) if not active_ssas.empty else 0

            workload_data.append({
                'date': date,
                'workload': workload
            })

        workload_df = pd.DataFrame(workload_data)

        # Prepara dados para previsão
        X = np.arange(len(workload_df)).reshape(-1, 1)
        y = workload_df['workload'].values

        # Ajusta modelo de regressão
        model = LinearRegression()
        model.fit(X, y)

        # Projeta próximos 7 dias
        future_dates = [
            workload_df['date'].iloc[-1] + pd.Timedelta(days=i)
            for i in range(1, 8)
        ]
        future_X = np.arange(len(X), len(X) + 7).reshape(-1, 1)
        predictions = model.predict(future_X)

        # Cria visualização
        fig = go.Figure()

        # Dados históricos
        fig.add_trace(go.Scatter(
            x=workload_df['date'],
            y=workload_df['workload'],
            mode='lines+markers',
            name='Histórico',
            line=dict(color=DashboardTheme.COLORS["primary"])
        ))

        # Previsões
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Previsão',
            line=dict(
                color=DashboardTheme.COLORS["warning"],
                dash='dash'
            )
        ))

        # Linha de capacidade ideal
        media_historica = workload_df['workload'].mean()
        fig.add_hline(
            y=media_historica,
            line_dash="dot",
            line_color="green",
            annotation_text="Média Histórica"
        )

        fig.update_layout(
            title="Previsão de Carga de Trabalho por Responsável",
            xaxis_title="Data",
            yaxis_title="SSAs/Responsável",
            template="plotly_white",
            hovermode='x unified'
        )

        return fig

    def _create_trend_prediction(self, df: pd.DataFrame) -> go.Figure:
        """Cria previsão de tendências."""
        if df.empty:
            return go.Figure()

        # Analisa tendências por tipo de SSA
        trends = []
        for col in [SSAColumns.GRAU_PRIORIDADE_EMISSAO, SSAColumns.SETOR_EXECUTOR]:
            daily_counts = df.groupby([
                df.iloc[:, SSAColumns.EMITIDA_EM].dt.date,
                df.iloc[:, col]
            ]).size().unstack(fill_value=0)

            # Calcula tendência para cada categoria
            for category in daily_counts.columns:
                slope, intercept = np.polyfit(
                    range(len(daily_counts)), 
                    daily_counts[category], 
                    1
                )
                trends.append({
                    'categoria': f"{SSAColumns.get_name(col)}: {category}",
                    'tendencia': slope,
                    'media': daily_counts[category].mean()
                })

        # Ordena por magnitude da tendência
        trends_df = pd.DataFrame(trends)
        trends_df['tendencia_abs'] = abs(trends_df['tendencia'])
        trends_df = trends_df.sort_values('tendencia_abs', ascending=True)

        # Cria visualização
        fig = go.Figure()

        # Barras de tendência
        fig.add_trace(go.Bar(
            y=trends_df['categoria'],
            x=trends_df['tendencia'],
            orientation='h',
            marker_color=[
                DashboardTheme.COLORS["success"] if x > 0 else DashboardTheme.COLORS["danger"]
                for x in trends_df['tendencia']
            ],
            name='Tendência'
        ))

        fig.update_layout(
            title="Análise de Tendências por Categoria",
            xaxis_title="Variação Diária Média",
            yaxis_title="Categoria",
            template="plotly_white",
            showlegend=True,
            height=max(400, len(trends_df) * 30)  # Ajusta altura baseado no número de categorias
        )

        return fig

    def _setup_analysis_callbacks(self):
        """Configura callbacks para análises avançadas."""
        @self.app.callback(
            [
                Output("analysis-content", "children"),
                Output("analysis-title", "children")
            ],
            [
                Input("analysis-type-select", "value"),
                Input("date-range-filter", "start_date"),
                Input("date-range-filter", "end_date")
            ]
        )
        def update_analysis_content(analysis_type, start_date, end_date):
            """
            Atualiza conteúdo da análise baseado na seleção.
            
            Args:
                analysis_type: Tipo de análise selecionada
                start_date: Data inicial do período
                end_date: Data final do período
            """
            # Filtra dados pelo período
            mask = (self.df.iloc[:, SSAColumns.EMITIDA_EM] >= start_date) & (
                self.df.iloc[:, SSAColumns.EMITIDA_EM] <= end_date
            )
            df_filtered = self.df[mask]

            if analysis_type == "predictive":
                return self._create_predictive_analysis(df_filtered)
            elif analysis_type == "correlation":
                return self._create_correlation_analysis(df_filtered)
            elif analysis_type == "flow":
                return self._create_flow_analysis(df_filtered)
            elif analysis_type == "performance":
                return self._create_performance_analysis(df_filtered)
            else:
                return self._create_overview_analysis(df_filtered)

    def _create_predictive_analysis(self, df: pd.DataFrame) -> Tuple[List[dbc.Card], str]:
        """
        Cria análise preditiva.
        
        Args:
            df: DataFrame filtrado para análise
            
        Returns:
            Tuple[List[dbc.Card], str]: Conteúdo e título da análise
        """
        predictions = self._create_predictive_visualizations(df)

        content = [
            # Card de Previsão de Volume
            dbc.Card([
                dbc.CardHeader(html.H5("Previsão de Volume")),
                dbc.CardBody([
                    dcc.Graph(figure=predictions["volume"]),
                    html.P("Análise de tendências e projeção de volume de SSAs")
                ])
            ], className="mb-4"),
            
            # Card de Previsão de SLA
            dbc.Card([
                dbc.CardHeader(html.H5("Previsão de SLA")),
                dbc.CardBody([
                    dcc.Graph(figure=predictions["sla"]),
                    html.P("Projeção de cumprimento de SLA")
                ])
            ], className="mb-4"),
            
            # Card de Previsão de Carga
            dbc.Card([
                dbc.CardHeader(html.H5("Previsão de Carga")),
                dbc.CardBody([
                    dcc.Graph(figure=predictions["workload"]),
                    html.P("Análise de tendências de carga de trabalho")
                ])
            ], className="mb-4"),
            
            # Card de Tendências
            dbc.Card([
                dbc.CardHeader(html.H5("Análise de Tendências")),
                dbc.CardBody([
                    dcc.Graph(figure=predictions["trends"]),
                    html.P("Identificação de padrões e tendências")
                ])
            ])
        ]

        return content, "Análise Preditiva"

    def _create_correlation_analysis(self, df: pd.DataFrame) -> Tuple[List[dbc.Card], str]:
        """
        Cria análise de correlações.
        
        Args:
            df: DataFrame filtrado para análise
            
        Returns:
            Tuple[List[dbc.Card], str]: Conteúdo e título da análise
        """
        # Cria heatmap de correlação
        heatmap = self._create_correlation_heatmap(df)

        # Identifica correlações significativas
        correlations = self._identify_significant_correlations(df)

        content = [
            # Card do Mapa de Calor
            dbc.Card([
                dbc.CardHeader(html.H5("Mapa de Correlações")),
                dbc.CardBody([
                    dcc.Graph(figure=heatmap),
                    html.P("Visualização de correlações entre variáveis")
                ])
            ], className="mb-4"),
            
            # Card de Correlações Significativas
            dbc.Card([
                dbc.CardHeader(html.H5("Correlações Significativas")),
                dbc.CardBody([
                    html.Div([
                        dbc.Alert([
                            html.H6(f"{corr['var1']} × {corr['var2']}"),
                            html.P(f"Correlação: {corr['correlation']:.2f}"),
                            html.P(corr['interpretation'])
                        ], color=corr['color'])
                        for corr in correlations
                    ])
                ])
            ])
        ]

        return content, "Análise de Correlações"

    def _identify_significant_correlations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identifica correlações significativas nos dados.
        
        Args:
            df: DataFrame para análise
            
        Returns:
            List[Dict]: Lista de correlações significativas
        """
        correlations = []

        # Prepara dados para correlação
        correlation_data = pd.DataFrame({
            'tempo_resposta': (datetime.now() - df.iloc[:, SSAColumns.EMITIDA_EM]).dt.total_seconds() / 3600,
            'tem_programacao': df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].notna(),
            'tem_execucao': df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].notna(),
            'is_critica': df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == 'S3.7',
            'is_simples': df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == 'Sim'
        })

        # Calcula correlações
        corr_matrix = correlation_data.corr()

        # Identifica correlações significativas (|corr| > 0.3)
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > 0.3:
                    correlations.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': corr,
                        'color': 'success' if corr > 0 else 'danger',
                        'interpretation': self._interpret_correlation(
                            corr_matrix.columns[i],
                            corr_matrix.columns[j],
                            corr
                        )
                    })

        return sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)

    def _interpret_correlation(self, var1: str, var2: str, correlation: float) -> str:
        """
        Interpreta o significado de uma correlação.
        
        Args:
            var1: Primeira variável
            var2: Segunda variável
            correlation: Valor da correlação
            
        Returns:
            str: Interpretação da correlação
        """
        direction = "positiva" if correlation > 0 else "negativa"
        strength = (
            "forte" if abs(correlation) > 0.7 else
            "moderada" if abs(correlation) > 0.5 else
            "fraca"
        )

        interpretations = {
            ('tempo_resposta', 'tem_programacao'): {
                'positive': 'SSAs programadas tendem a ter maior tempo de resposta',
                'negative': 'SSAs programadas tendem a ter menor tempo de resposta'
            },
            ('tempo_resposta', 'is_critica'): {
                'positive': 'SSAs críticas estão levando mais tempo',
                'negative': 'SSAs críticas estão sendo tratadas mais rapidamente'
            },
            ('is_simples', 'tem_execucao'): {
                'positive': 'SSAs simples são executadas mais rapidamente',
                'negative': 'SSAs simples estão demorando mais para execução'
            }
        }

        key = tuple(sorted([var1, var2]))
        if key in interpretations:
            specific = interpretations[key]['positive' if correlation > 0 else 'negative']
            return f"Correlação {direction} {strength}: {specific}"

        return f"Correlação {direction} {strength} entre {var1} e {var2}"

    def _create_flow_analysis(self, df: pd.DataFrame) -> Tuple[List[dbc.Card], str]:
        """
        Cria análise de fluxo.
        
        Args:
            df: DataFrame filtrado para análise
            
        Returns:
            Tuple[List[dbc.Card], str]: Conteúdo e título da análise
        """
        # Cria visualizações de fluxo
        sankey = self._create_flow_visualization(df)
        network = self._create_network_visualization(df)
        treemap = self._create_hierarchy_visualization(df)

        content = [
            # Card do Diagrama Sankey
            dbc.Card([
                dbc.CardHeader(html.H5("Fluxo de SSAs")),
                dbc.CardBody([
                    dcc.Graph(figure=sankey),
                    html.P("Visualização do fluxo de SSAs entre setores e estados")
                ])
            ], className="mb-4"),
            
            # Card da Rede de Relacionamentos
            dbc.Card([
                dbc.CardHeader(html.H5("Rede de Relacionamentos")),
                dbc.CardBody([
                    dcc.Graph(figure=network),
                    html.P("Visualização das relações entre setores")
                ])
            ], className="mb-4"),
            
            # Card da Hierarquia
            dbc.Card([
                dbc.CardHeader(html.H5("Estrutura Hierárquica")),
                dbc.CardBody([
                    dcc.Graph(figure=treemap),
                    html.P("Visualização hierárquica da distribuição de SSAs")
                ])
            ])
        ]

        return content, "Análise de Fluxo"

    def _create_performance_analysis(self, df: pd.DataFrame) -> Tuple[List[dbc.Card], str]:
        """
        Cria análise de performance.
        
        Args:
            df: DataFrame filtrado para análise
            
        Returns:
            Tuple[List[dbc.Card], str]: Conteúdo e título da análise
        """
        # Calcula KPIs
        kpis = self.kpi_calculator.calculate_efficiency_metrics()
        quality = self.kpi_calculator.calculate_quality_metrics()
        responsiveness = self.kpi_calculator.calculate_responsiveness_metrics()

        # Cria gráficos de performance
        performance_charts = self._create_performance_charts(df)

        content = [
            # Card de KPIs
            dbc.Card([
                dbc.CardHeader(html.H5("Indicadores de Performance")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{kpis['taxa_programacao']*100:.1f}%"),
                                    html.P("Taxa de Programação")
                                ])
                            ], className="text-center")
                        ]),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{kpis['taxa_execucao_simples']*100:.1f}%"),
                                    html.P("Taxa de Execução Simples")
                                ])
                            ], className="text-center")
                        ]),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{responsiveness.get('taxa_sla', 0)*100:.1f}%"),
                                    html.P("Cumprimento de SLA")
                                ])
                            ], className="text-center")
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Cards de Gráficos de Performance
            *[
                dbc.Card([
                    dbc.CardHeader(html.H5(title)),
                    dbc.CardBody([
                        dcc.Graph(figure=fig),
                        html.P(description)
                    ])
                ], className="mb-4")
                for title, fig, description in performance_charts
            ]
        ]

        return content, "Análise de Performance"


# Funções de verificação de dependências e inicialização


def check_dependencies():
    """
    Verifica e instala dependências necessárias.

    Raises:
        Exception: Se houver erro na instalação de dependências
    """
    dependencies = {
        "xlsxwriter": "xlsxwriter",
        "dash-bootstrap-components": "dash-bootstrap-components",
        "plotly": "plotly",
        "pandas": "pandas",
        "pdfkit": "pdfkit",
    }

    missing_deps = []

    for module, package in dependencies.items():
        try:
            __import__(module)
            logger.info(f"Dependência {module} encontrada")
        except ImportError:
            missing_deps.append(package)
            logger.warning(f"Dependência {module} não encontrada")

    if missing_deps:
        try:
            import subprocess

            for package in missing_deps:
                logger.info(f"Instalando {package}...")
                subprocess.check_call(["pip", "install", package])
                logger.info(f"{package} instalado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao instalar dependências: {str(e)}")
            raise

    # Verificações adicionais
    try:
        import pdfkit

        pdfkit_config = pdfkit.configuration()
        if pdfkit_config.wkhtmltopdf:
            logger.info("wkhtmltopdf encontrado")
        else:
            logger.warning(
                "wkhtmltopdf não encontrado. A exportação para PDF pode não funcionar."
            )
    except Exception as e:
        logger.warning(f"Erro ao verificar wkhtmltopdf: {str(e)}")


# TODO: Implementar verificações adicionais de sistema
def check_system_requirements():
    """
    Verifica requisitos do sistema.
    - Memória disponível
    - Espaço em disco
    - Versão do Python
    - Configurações de rede
    """
    raise NotImplementedError


# TODO: Implementar configuração de logging avançada
def setup_advanced_logging():
    """
    Configura sistema de logging avançado.
    - Rotação de logs
    - Diferentes níveis por módulo
    - Formatação personalizada
    - Integração com sistemas externos
    """
    raise NotImplementedError


def main():
    """Função principal do programa."""
    try:
        # Verifica dependências
        check_dependencies()

        # Configuração de logging
        logger.info("Iniciando aplicação...")

        # Carrega os dados
        logger.info("Iniciando carregamento dos dados...")
        excel_path = r"C:\Users\menon\git\trabalho\SCRAP-SAM\Downloads\SSAs Pendentes Geral - 28-10-2024_1221PM.xlsx"
        loader = DataLoader(excel_path)
        df = loader.load_data()
        logger.info(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")

        # Processamento inicial dos dados
        ssas = loader.get_ssa_objects()
        logger.info(f"Convertidos {len(ssas)} registros para objetos SSAData")

        # Análise inicial
        ssas_alta_prioridade = loader.filter_ssas(prioridade="S3.7")
        logger.info(f"Total de SSAs com alta prioridade: {len(ssas_alta_prioridade)}")

        # Gera relatório inicial
        logger.info("Gerando relatório inicial...")
        reporter = SSAReporter(df)
        reporter.save_excel_report("relatorio_ssas.xlsx")
        logger.info("Relatório Excel gerado com sucesso")

        # Inicia o dashboard
        logger.info("Iniciando dashboard...")
        app = SSADashboard(df)

        # Configurações do servidor
        host = "0.0.0.0"  # Permite acesso externo
        port = 8050
        debug = True

        logger.info(f"Iniciando servidor em {host}:{port}")
        app.run_server(debug=debug, host=host, port=port)

    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.info("Finalizando aplicação...")

    def _create_performance_charts(self, df: pd.DataFrame) -> List[Tuple[str, go.Figure, str]]:
        """
        Cria gráficos para análise de performance.
        
        Args:
            df: DataFrame para análise
            
        Returns:
            List[Tuple[str, go.Figure, str]]: Lista de (título, figura, descrição)
        """
        charts = []
        
        # Evolução temporal de performance (continuação)
        temporal_perf.update_layout(
            title="Evolução de Performance",
            xaxis_title="Data",
            yaxis_title="Score",
            template="plotly_white",
            hovermode='x unified'
        )
        
        charts.append((
            "Evolução Temporal",
            temporal_perf,
            "Evolução dos indicadores de performance ao longo do tempo"
        ))

        # Performance por setor
        sector_perf = go.Figure()
        sector_metrics = {}
        
        for sector in df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            sector_df = df[df.iloc[:, SSAColumns.SETOR_EXECUTOR] == sector]
            sector_metrics[sector] = {
                'sla': self.kpi_calculator._calculate_sla_compliance(sector_df),
                'quality': self.kpi_calculator._calculate_quality_score(
                    self.kpi_calculator.calculate_quality_metrics()
                ),
                'efficiency': self.kpi_calculator.calculate_efficiency_metrics()['taxa_execucao_simples']
            }

        sector_perf.add_trace(go.Bar(
            name='SLA',
            x=list(sector_metrics.keys()),
            y=[m['sla'] for m in sector_metrics.values()],
            marker_color=DashboardTheme.COLORS["primary"]
        ))
        
        sector_perf.add_trace(go.Bar(
            name='Qualidade',
            x=list(sector_metrics.keys()),
            y=[m['quality'] for m in sector_metrics.values()],
            marker_color=DashboardTheme.COLORS["success"]
        ))
        
        sector_perf.add_trace(go.Bar(
            name='Eficiência',
            x=list(sector_metrics.keys()),
            y=[m['efficiency'] for m in sector_metrics.values()],
            marker_color=DashboardTheme.COLORS["info"]
        ))
        
        sector_perf.update_layout(
            title="Performance por Setor",
            xaxis_title="Setor",
            yaxis_title="Score",
            template="plotly_white",
            barmode='group'
        )
        
        charts.append((
            "Performance Setorial",
            sector_perf,
            "Comparativo de performance entre setores"
        ))

        # Distribuição de tempos de resposta
        response_times = df.apply(
            lambda row: (datetime.now() - row.iloc[SSAColumns.EMITIDA_EM]).total_seconds() / 3600,
            axis=1
        )
        
        time_dist = go.Figure(data=[
            go.Histogram(
                x=response_times,
                nbinsx=30,
                marker_color=DashboardTheme.COLORS["primary"]
            )
        ])
        
        time_dist.add_vline(
            x=response_times.mean(),
            line_dash="dash",
            line_color="red",
            annotation_text="Média"
        )
        
        time_dist.update_layout(
            title="Distribuição de Tempos de Resposta",
            xaxis_title="Horas",
            yaxis_title="Frequência",
            template="plotly_white"
        )
        
        charts.append((
            "Tempos de Resposta",
            time_dist,
            "Análise da distribuição dos tempos de resposta"
        ))

        return charts

    def _setup_alert_system(self):
        """Configura sistema de alertas."""
        @self.app.callback(
            Output("alert-container", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_alerts(n):
            """Atualiza alertas baseado nas condições atuais."""
            alerts = []
            
            # Verifica SLA
            sla_compliance = self.kpi_calculator._calculate_sla_compliance(self.df)
            if sla_compliance < 0.8:
                alerts.append(
                    dbc.Alert(
                        [
                            html.H4("Alerta de SLA", className="alert-heading"),
                            html.P(f"Taxa de cumprimento de SLA está em {sla_compliance*100:.1f}%"),
                            html.Hr(),
                            html.P(
                                "Recomendação: Revisar priorização e alocação de recursos",
                                className="mb-0"
                            )
                        ],
                        color="danger",
                        dismissable=True
                    )
                )

            # Verifica sobrecarga
            overload = self.kpi_calculator._identify_overload()
            if overload:
                alerts.append(
                    dbc.Alert(
                        [
                            html.H4("Alerta de Sobrecarga", className="alert-heading"),
                            html.P(f"Detectados {len(overload)} casos de sobrecarga"),
                            html.Hr(),
                            html.P(
                                "Recomendação: Redistribuir carga de trabalho",
                                className="mb-0"
                            )
                        ],
                        color="warning",
                        dismissable=True
                    )
                )

            # Verifica tendências
            trends = self.kpi_calculator.calculate_trend_indicators()
            if trends["alertas"]:
                alerts.append(
                    dbc.Alert(
                        [
                            html.H4("Alerta de Tendência", className="alert-heading"),
                            html.P(f"Detectadas {len(trends['alertas'])} tendências significativas"),
                            html.Hr(),
                            html.P(
                                trends["alertas"][0]["mensagem"],
                                className="mb-0"
                            )
                        ],
                        color="info",
                        dismissable=True
                    )
                )

            return alerts

    def _setup_customization_options(self):
        """Configura opções de customização."""
        @self.app.callback(
            Output("dashboard-container", "style"),
            [Input("theme-selector", "value")]
        )
        def update_theme(theme):
            """Atualiza tema do dashboard."""
            if theme == "dark":
                return {
                    "backgroundColor": DashboardTheme.COLORS["dark"],
                    "color": "white",
                    "minHeight": "100vh"
                }
            return {
                "backgroundColor": DashboardTheme.COLORS["light"],
                "color": "black",
                "minHeight": "100vh"
            }

        @self.app.callback(
            [Output(f"chart-{i}", "style") for i in range(6)],
            [Input("layout-selector", "value")]
        )
        def update_layout(layout):
            """Atualiza layout dos gráficos."""
            if layout == "compact":
                return [{"height": "300px"} for _ in range(6)]
            return [{"height": "500px"} for _ in range(6)]

    def _setup_export_functionality(self):
        """Configura funcionalidades de exportação."""
        @self.app.callback(
            Output("download-dataframe-xlsx", "data"),
            [Input("btn-export-excel", "n_clicks")],
            [State("date-range-filter", "start_date"),
             State("date-range-filter", "end_date")]
        )
        def export_excel(n_clicks, start_date, end_date):
            """Exporta dados para Excel."""
            if not n_clicks:
                raise PreventUpdate

            # Filtra dados pelo período
            mask = (self.df.iloc[:, SSAColumns.EMITIDA_EM] >= start_date) & (
                self.df.iloc[:, SSAColumns.EMITIDA_EM] <= end_date
            )
            df_filtered = self.df[mask]

            # Prepara arquivo
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Dados principais
                df_filtered.to_excel(writer, sheet_name='Dados', index=False)
                
                # Análises
                self._export_analysis_sheets(writer, df_filtered)
                
                # Métricas
                self._export_metrics_sheet(writer, df_filtered)

            data = output.getvalue()
            return dcc.send_bytes(data, f"analise_ssas_{datetime.now():%Y%m%d}.xlsx")

    def _export_analysis_sheets(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Exporta abas de análise."""
        # Performance
        performance = pd.DataFrame([
            self.kpi_calculator.calculate_efficiency_metrics()
        ])
        performance.to_excel(writer, sheet_name='Performance', index=False)

        # Tendências
        trends = pd.DataFrame([
            self.kpi_calculator.calculate_trend_indicators()
        ])
        trends.to_excel(writer, sheet_name='Tendências', index=False)

        # Correlações
        correlations = pd.DataFrame(
            self._identify_significant_correlations(df)
        )
        correlations.to_excel(writer, sheet_name='Correlações', index=False)

    def _export_metrics_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Exporta aba de métricas."""
        metrics = []
        
        # Métricas por setor
        for setor in df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            setor_df = df[df.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor]
            metrics.append({
                'setor': setor,
                'total_ssas': len(setor_df),
                'sla': self.kpi_calculator._calculate_sla_compliance(setor_df),
                'tempo_medio': setor_df.apply(
                    lambda row: (datetime.now() - row.iloc[SSAColumns.EMITIDA_EM]).total_seconds() / 3600,
                    axis=1
                ).mean()
            })

        pd.DataFrame(metrics).to_excel(writer, sheet_name='Métricas', index=False)

    def run_server(self, debug: bool = True, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Inicia o servidor do dashboard.
        
        Args:
            debug: Modo debug
            host: Host do servidor
            port: Porta do servidor
        """
        try:
            logger.info(f"Iniciando servidor em {host}:{port}")
            self.app.run_server(debug=debug, host=host, port=port)
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {e}")
            raise


# TODO: Implementar funções utilitárias adicionais


def setup_error_handling():
    """
    Configura sistema avançado de tratamento de erros.
    
    Returns:
        Dict: Configurações de tratamento de erros
    """
    def error_handler(error: Exception, context: str = None) -> Dict:
        """Handler personalizado de erros."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        }

        # Log do erro
        logger.error(
            f"Erro em {context}: {error_info['type']}\n"
            f"Mensagem: {error_info['message']}\n"
            f"Traceback: {error_info['traceback']}"
        )

        # Notificação (se configurada)
        if hasattr(config, "NOTIFY_ERRORS") and config.NOTIFY_ERRORS:
            send_error_notification(error_info)

        return error_info

    def send_error_notification(error_info: Dict):
        """Envia notificação de erro."""
        try:
            # Implementar integração com sistema de notificação
            pass
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")

    return {
        "handler": error_handler,
        "log_dir": "logs/errors",
        "notification_enabled": True
    }


def setup_performance_monitoring():
    """
    Configura sistema de monitoramento de performance.

    Returns:
        PerformanceMonitor: Monitor de performance configurado
    """

    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {
                "response_times": [],
                "memory_usage": [],
                "cpu_usage": [],
                "active_users": 0,
                "start_time": datetime.now(),
            }
            self.running = False
            self.monitor_thread = None

        def _start_monitoring(self):
            """Inicia threads de monitoramento."""
            import threading

            def monitor_resources():
                while self.running:
                    try:
                        self.metrics["memory_usage"].append(self._get_memory_usage())
                        self.metrics["cpu_usage"].append(self._get_cpu_usage())

                        # Limita tamanho do histórico
                        if len(self.metrics["memory_usage"]) > 1000:
                            self.metrics["memory_usage"] = self.metrics["memory_usage"][
                                -1000:
                            ]
                        if len(self.metrics["cpu_usage"]) > 1000:
                            self.metrics["cpu_usage"] = self.metrics["cpu_usage"][
                                -1000:
                            ]

                        time.sleep(60)  # Coleta a cada minuto
                    except Exception as e:
                        logger.error(f"Erro no monitoramento: {e}")
                        time.sleep(60)  # Aguarda antes de tentar novamente

            self.running = True
            self.monitor_thread = threading.Thread(
                target=monitor_resources, daemon=True
            )
            self.monitor_thread.start()

        def start(self):
            """Inicia monitoramento."""
            if not self.running:
                self._start_monitoring()
                logger.info("Monitoramento de performance iniciado")

        def stop(self):
            """Para monitoramento."""
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            logger.info("Monitoramento de performance interrompido")

        def _get_memory_usage(self) -> float:
            """
            Obtém uso de memória.

            Returns:
                float: Uso de memória em MB
            """
            import psutil

            return psutil.Process().memory_info().rss / 1024 / 1024

        def _get_cpu_usage(self) -> float:
            """
            Obtém uso de CPU.

            Returns:
                float: Porcentagem de uso de CPU
            """
            import psutil

            return psutil.Process().cpu_percent()

        def log_response_time(self, response_time: float):
            """
            Registra tempo de resposta.

            Args:
                response_time: Tempo de resposta em segundos
            """
            self.metrics["response_times"].append(response_time)
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        def get_metrics(self) -> Dict:
            """
            Retorna métricas atuais.

            Returns:
                Dict: Métricas coletadas
            """
            avg_response_time = (
                sum(self.metrics["response_times"])
                / len(self.metrics["response_times"])
                if self.metrics["response_times"]
                else 0
            )

            return {
                "avg_response_time": avg_response_time,
                "memory_mb": (
                    self.metrics["memory_usage"][-1]
                    if self.metrics["memory_usage"]
                    else 0
                ),
                "cpu_percent": (
                    self.metrics["cpu_usage"][-1] if self.metrics["cpu_usage"] else 0
                ),
                "active_users": self.metrics["active_users"],
                "uptime": (datetime.now() - self.metrics["start_time"]).total_seconds(),
                "history": {
                    "memory": self.metrics["memory_usage"][-60:],  # últimos 60 minutos
                    "cpu": self.metrics["cpu_usage"][-60:],
                    "response_times": self.metrics["response_times"][
                        -100:
                    ],  # últimas 100 respostas
                },
            }

        def analyze_performance(self) -> Dict:
            """
            Analisa métricas de performance.

            Returns:
                Dict: Análise de performance
            """
            metrics = self.get_metrics()

            # Define limiares
            thresholds = {
                "memory": 1024,  # 1GB
                "cpu": 80,  # 80%
                "response": 1.0,  # 1 segundo
            }

            # Analisa tendências
            memory_trend = (
                (metrics["history"]["memory"][-1] - metrics["history"]["memory"][0])
                / metrics["history"]["memory"][0]
                if metrics["history"]["memory"]
                else 0
            )

            cpu_trend = (
                (metrics["history"]["cpu"][-1] - metrics["history"]["cpu"][0])
                / metrics["history"]["cpu"][0]
                if metrics["history"]["cpu"]
                else 0
            )

            return {
                "status": (
                    "critical"
                    if any(
                        [
                            metrics["memory_mb"] > thresholds["memory"],
                            metrics["cpu_percent"] > thresholds["cpu"],
                            metrics["avg_response_time"] > thresholds["response"],
                        ]
                    )
                    else (
                        "warning"
                        if any(
                            [
                                metrics["memory_mb"] > thresholds["memory"] * 0.8,
                                metrics["cpu_percent"] > thresholds["cpu"] * 0.8,
                                metrics["avg_response_time"]
                                > thresholds["response"] * 0.8,
                            ]
                        )
                        else "normal"
                    )
                ),
                "metrics": metrics,
                "thresholds": thresholds,
                "trends": {
                    "memory": (
                        "increasing"
                        if memory_trend > 0.1
                        else "decreasing" if memory_trend < -0.1 else "stable"
                    ),
                    "cpu": (
                        "increasing"
                        if cpu_trend > 0.1
                        else "decreasing" if cpu_trend < -0.1 else "stable"
                    ),
                },
                "recommendations": self._generate_recommendations(metrics, thresholds),
            }

        def _generate_recommendations(
            self, metrics: Dict, thresholds: Dict
        ) -> List[str]:
            """
            Gera recomendações baseadas nas métricas.

            Args:
                metrics: Métricas atuais
                thresholds: Limiares definidos

            Returns:
                List[str]: Lista de recomendações
            """
            recommendations = []

            if metrics["memory_mb"] > thresholds["memory"]:
                recommendations.append(
                    "Memória alta: considerar otimização ou aumento de recursos"
                )

            if metrics["cpu_percent"] > thresholds["cpu"]:
                recommendations.append(
                    "CPU sobrecarregada: verificar processos e considerar otimização"
                )

            if metrics["avg_response_time"] > thresholds["response"]:
                recommendations.append(
                    "Tempo de resposta alto: verificar gargalos e otimizar consultas"
                )

            return recommendations

    return PerformanceMonitor()


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yml"
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or create default"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logging.info("Configuration loaded successfully")
                return config
        except FileNotFoundError:
            # Create default config
            default_config = {
                "data": {
                    "excel_path": "data/ssa_data.xlsx",
                    "sheet_name": "SSAs",
                    "backup_dir": "backups",
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "monitoring": {"interval": 60},
            }

            # Ensure config directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

            # Save default config
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f)

            logging.info("Default configuration created")
            return default_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)


class ConfigurationManager:
    """Gerenciador de configurações."""

    def __init__(self):
        """Inicializa o gerenciador de configurações."""
        self.config = {}
        self._watchers: List[Callable] = []
        self.load_config()

    def load_config(self):
        """
        Carrega configuração do arquivo JSON.
        Se o arquivo não existir, cria configuração padrão.
        """
        try:
            if Path("config.json").exists():
                with open("config.json", "r") as f:
                    self.config = json.load(f)
                logging.info("Configuration loaded successfully")
            else:
                self.create_default_config()
                self.save_config()
                logging.info("Created and saved default configuration")
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            self.create_default_config()

    def create_default_config(self):
        """
        Cria configuração padrão.
        """
        self.config = {
            "debug": True,
            "host": "localhost",
            "port": 8000,
            "log_level": "INFO",
            "backup": {
                "enabled": True,
                "interval": 24,  # horas
                "retention": 30,  # dias
            },
            "security": {
                "enabled": True,
                "session_timeout": 30,  # minutos
                "max_attempts": 3,
            },
            "maintenance": {
                "enabled": True,
                "log_retention": 90,  # dias
                "archive_after": 365,  # dias
            },
            "data": {
                "excel_path": r"C:\Users\menon\git\trabalho\SCRAP-SAM\Downloads\SSAs Pendentes Geral - 28-10-2024_1221PM.xlsx"
            },
        }
        logging.info("Default configuration created")

    def save_config(self):
        """
        Salva configuração atual no arquivo JSON.
        """
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")

    def validate_config(self) -> bool:
        """
        Valida configurações atuais.

        Returns:
            bool: True se configurações são válidas
        """
        try:
            schema = {
                "debug": bool,
                "host": str,
                "port": int,
                "log_level": lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR"],
                "backup.enabled": bool,
                "backup.interval": lambda x: isinstance(x, int) and x > 0,
                "backup.retention": lambda x: isinstance(x, int) and x > 0,
                "security.enabled": bool,
                "security.session_timeout": lambda x: isinstance(x, int) and x > 0,
                "security.max_attempts": lambda x: isinstance(x, int) and x > 0,
                "maintenance.enabled": bool,
                "maintenance.log_retention": lambda x: isinstance(x, int) and x > 0,
                "maintenance.archive_after": lambda x: isinstance(x, int) and x > 0,
            }

            for key, validator in schema.items():
                value = self.get(key)
                if value is None:
                    logger.error(f"Configuração ausente: {key}")
                    return False
                if not validator(value):
                    logger.error(f"Configuração inválida: {key}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Erro ao validar configurações: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração por chave aninhada.

        Args:
            key: Chave no formato "section.subsection.value"
            default: Valor padrão se chave não existir

        Returns:
            Valor da configuração ou default
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        Define valor de configuração.

        Args:
            key: Chave da configuração
            value: Valor a ser definido
        """
        keys = key.split(".")
        target = self.config

        for k in keys[:-1]:
            target = target.setdefault(k, {})

        target[keys[-1]] = value
        self.save_config()
        self._notify_watchers(key, value)

    def add_watcher(self, callback: Callable):
        """
        Adiciona uma função callback para monitorar mudanças.

        Args:
            callback: Função a ser chamada quando houver mudanças
        """
        if callback not in self._watchers:
            self._watchers.append(callback)

    def remove_watcher(self, callback: Callable):
        """
        Remove uma função callback do monitoramento.

        Args:
            callback: Função a ser removida
        """
        if callback in self._watchers:
            self._watchers.remove(callback)

    def watch(self, key: str, callback: Callable):
        """
        Adiciona observador para mudanças em configuração.

        Args:
            key: Chave a observar
            callback: Função a ser chamada quando valor mudar
        """
        self._watchers.append({"key": key, "callback": callback})

    def _notify_watchers(self, key: str, value: Any):
        """
        Notifica todos os watchers sobre mudanças nas configurações.
        """
        for watcher in self._watchers:
            try:
                if isinstance(watcher, dict):
                    if watcher["key"] == key:
                        watcher["callback"](value)
                else:
                    watcher(self.config)
            except Exception as e:
                logger.error(f"Erro ao notificar watcher: {e}")


def setup_security():
    """
    Configura sistema de segurança.
    
    Returns:
        Dict: Configurações de segurança
    """
    class SecurityManager:
        def __init__(self):
            self.active_sessions = {}
            self.blocked_ips = set()
            self.attempt_counts = {}

        def authenticate(self, username: str, password: str, ip: str) -> bool:
            """Autentica usuário."""
            if ip in self.blocked_ips:
                logger.warning(f"Tentativa de acesso de IP bloqueado: {ip}")
                return False

            # Verifica tentativas de login
            if self.attempt_counts.get(ip, 0) >= 5:
                self.blocked_ips.add(ip)
                logger.warning(f"IP bloqueado após múltiplas tentativas: {ip}")
                return False

            # Validação de credenciais (implementar integração com sistema de autenticação)
            is_valid = self._validate_credentials(username, password)

            if not is_valid:
                self.attempt_counts[ip] = self.attempt_counts.get(ip, 0) + 1
                logger.warning(f"Tentativa de login inválida de {ip} para usuário {username}")
                return False

            # Limpa tentativas após sucesso
            self.attempt_counts.pop(ip, None)

            # Cria sessão
            session_id = self._generate_session_id()
            self.active_sessions[session_id] = {
                "username": username,
                "ip": ip,
                "created_at": datetime.now()
            }

            return True

        def _validate_credentials(self, username: str, password: str) -> bool:
            """Valida credenciais do usuário."""
            # Implementar integração com sistema de autenticação
            return True

        def _generate_session_id(self) -> str:
            """Gera ID de sessão único."""
            import uuid
            return str(uuid.uuid4())

        def validate_session(self, session_id: str, ip: str) -> bool:
            """Valida sessão ativa."""
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]
            if session["ip"] != ip:
                logger.warning(f"IP diferente para sessão {session_id}: esperado {session['ip']}, recebido {ip}")
                return False

            # Verifica expiração
            if (datetime.now() - session["created_at"]).total_seconds() > 3600:  # 1 hora
                self.active_sessions.pop(session_id)
                return False

            return True

        def audit_log(self, action: str, user: str, details: Dict):
            """Registra log de auditoria."""
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "user": user,
                "details": details
            }

            logger.info(f"Audit: {audit_entry}")
            # Implementar persistência do log de auditoria

    return SecurityManager()


class MaintenanceManager:
    """Gerenciador de manutenção do sistema."""

    def run(self):
        # Add your maintenance logic here
        pass

    def load_config(self):
        """
        Load configuration from JSON file.
        If file doesn't exist, create default configuration.
        """
        try:
            if Path("config.json").exists():
                with open("config.json", "r") as f:
                    self.config = json.load(f)
                logging.info("Configuration loaded successfully")
            else:
                self.create_default_config()
                self.save_config()
                logging.info("Created and saved default configuration")
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            self.create_default_config()

    def create_default_config(self):
        """
        Create default configuration settings.
        """
        self.config = {
            "debug": True,
            "host": "localhost",
            "port": 8000,
            "log_level": "INFO",
            "backup": {
                "enabled": True,
                "interval": 24,  # horas
                "retention": 30,  # dias
            },
            "security": {
                "enabled": True,
                "session_timeout": 30,  # minutos
                "max_attempts": 3,
            },
            "maintenance": {
                "enabled": True,
                "log_retention": 90,  # dias
                "archive_after": 365,  # dias
            },
        }
        logging.info("Default configuration created")

    def __init__(self):
        self.config = {}
        self._watchers: List[Callable] = []
        self.load_config()

    def save_config(self):
        """
        Save current configuration to JSON file.
        """
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")

    def validate_config(self) -> bool:
        """
        Valida configurações atuais.

        Returns:
            bool: True se configurações são válidas
        """
        try:
            schema = {
                "debug": bool,
                "host": str,
                "port": int,
                "log_level": lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR"],
                "backup.enabled": bool,
                "backup.interval": lambda x: isinstance(x, int) and x > 0,
                "backup.retention": lambda x: isinstance(x, int) and x > 0,
                "security.enabled": bool,
                "security.session_timeout": lambda x: isinstance(x, int) and x > 0,
                "security.max_attempts": lambda x: isinstance(x, int) and x > 0,
                "maintenance.enabled": bool,
                "maintenance.log_retention": lambda x: isinstance(x, int) and x > 0,
                "maintenance.archive_after": lambda x: isinstance(x, int) and x > 0,
            }

            for key, validator in schema.items():
                value = self.get(key)
                if value is None:
                    logger.error(f"Configuração ausente: {key}")
                    return False
                if not validator(value):
                    logger.error(f"Configuração inválida: {key}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Erro ao validar configurações: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração por chave aninhada.

        Args:
            key: Chave no formato "section.subsection.value"
            default: Valor padrão se chave não existir

        Returns:
            Valor da configuração ou default
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_config(self, key, default=None):
        """
        Safely get a configuration value.
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Define valor de configuração.

        Args:
            key: Chave da configuração
            value: Valor a ser definido
        """
        keys = key.split(".")
        target = self.config

        for k in keys[:-1]:
            target = target.setdefault(k, {})

        target[keys[-1]] = value
        self.save_config()
        self._notify_watchers(key, value)

    def add_watcher(self, callback: Callable):
        """
        Adiciona uma função callback para monitorar mudanças.

        Args:
            callback: Função a ser chamada quando houver mudanças
        """
        if callback not in self._watchers:
            self._watchers.append(callback)

    def remove_watcher(self, callback: Callable):
        """
        Remove uma função callback do monitoramento.

        Args:
            callback: Função a ser removida
        """
        if callback in self._watchers:
            self._watchers.remove(callback)

    def watch(self, key: str, callback: Callable):
        """
        Adiciona observador para mudanças em configuração.

        Args:
            key: Chave a observar
            callback: Função a ser chamada quando valor mudar
        """
        self._watchers.append({"key": key, "callback": callback})

    def _notify_watchers(self, key: str, value: Any):
        """
        Notifica todos os watchers sobre mudanças nas configurações.
        """
        for watcher in self._watchers:
            try:
                if isinstance(watcher, dict):
                    if watcher["key"] == key:
                        watcher["callback"](value)
                else:
                    watcher(self.config)
            except Exception as e:
                logger.error(f"Erro ao notificar watcher: {e}")

    def export_config(self, format: str = "json") -> str:
        """
        Exporta configurações em formato específico.

        Args:
            format: Formato de exportação ('json' ou 'yaml')

        Returns:
            str: Configurações formatadas
        """
        if format == "json":
            return json.dumps(self.config, indent=4)
        elif format == "yaml":
            import yaml

            return yaml.dump(self.config, default_flow_style=False)
        else:
            raise ValueError(f"Formato não suportado: {format}")


class BackupManager:
    """Gerenciador de backup do sistema."""
    
    def __init__(self):
        """Inicializa o gerenciador de backup."""
        self.backup_dir = "backups"
        self.max_backups = 10
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, data: pd.DataFrame) -> str:
        """
        Cria backup dos dados.
        
        Args:
            data: DataFrame para backup
            
        Returns:
            str: Caminho do arquivo de backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.pkl"
        filepath = os.path.join(self.backup_dir, filename)
        
        # Salva dados
        data.to_pickle(filepath)
        
        # Mantém limite de backups
        self._cleanup_old_backups()
        
        logger.info(f"Backup criado: {filepath}")
        return filepath
    
    def _cleanup_old_backups(self):
        """Remove backups antigos."""
        backups = sorted([
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("backup_") and f.endswith(".pkl")
        ])
        
        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            os.remove(oldest)
            logger.info(f"Backup removido: {oldest}")
    
    def restore_backup(self, filepath: str) -> pd.DataFrame:
        """
        Restaura backup.
        
        Args:
            filepath: Caminho do arquivo de backup
            
        Returns:
            pd.DataFrame: Dados restaurados
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Backup não encontrado: {filepath}")
        
        # Carrega dados
        data = pd.read_pickle(filepath)
        logger.info(f"Backup restaurado: {filepath}")
        
        return data
    
    def list_backups(self) -> List[Dict]:
        """
        Lista backups disponíveis.
        
        Returns:
            List[Dict]: Lista de backups com metadados
        """
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.startswith("backup_") and filename.endswith(".pkl"):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime)
                })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup(self):
        """Limpa recursos do gerenciador de backup."""
        try:
            logger.info("Finalizando gerenciador de backup")
        except Exception as e:
            logger.error(f"Erro ao finalizar gerenciador de backup: {e}")


def setup_backup() -> BackupManager:
    """
    Configura sistema de backup.
    
    Returns:
        BackupManager: Instância configurada do gerenciador de backup
        
    Raises:
        Exception: Se houver erro na configuração
    """
    try:
        manager = BackupManager()
        logger.info("Sistema de backup configurado com sucesso")
        return manager
    except Exception as e:
        logger.error(f"Erro ao configurar sistema de backup: {e}")
        raise


def setup_maintenance() -> MaintenanceManager:
    """
    Configura e retorna uma instância do gerenciador de manutenção.
    
    Returns:
        MaintenanceManager: Instância configurada do gerenciador
    
    Raises:
        Exception: Se houver erro na configuração
    """
    try:
        manager = MaintenanceManager()
        logger.info("Sistema de manutenção configurado com sucesso")
        return manager
    except Exception as e:
        logger.error(f"Erro ao configurar sistema de manutenção: {e}")
        raise

class ResourceManager:
    """Gerenciador de recursos do sistema."""

    def __init__(self):
        self.resources = {
            "memory": self._monitor_memory(),
            "cpu": self._monitor_cpu(),
            "disk": self._monitor_disk(),
            "network": self._monitor_network(),
        }
        self._alerts = []
        self._thresholds = {
            "memory": 0.8,  # 80%
            "cpu": 0.9,  # 90%
            "disk": 0.85,  # 85%
        }

    def _monitor_memory(self) -> Dict:
        """
        Monitora uso de memória.

        Returns:
            Dict: Estatísticas de memória
        """
        import psutil

        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
        }

    def _monitor_cpu(self) -> Dict:
        """
        Monitora uso de CPU.

        Returns:
            Dict: Estatísticas de CPU
        """
        import psutil

        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
        }

    def _monitor_disk(self) -> Dict:
        """
        Monitora uso de disco.

        Returns:
            Dict: Estatísticas de disco
        """
        import psutil

        disk = psutil.disk_usage("/")
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }

    def _monitor_network(self) -> Dict:
        """
        Monitora uso de rede.

        Returns:
            Dict: Estatísticas de rede
        """
        import psutil

        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }

    def check_resources(self) -> List[Dict]:
        """
        Verifica estado dos recursos.

        Returns:
            List[Dict]: Lista de alertas
        """
        self._alerts = []
        self.resources = {
            "memory": self._monitor_memory(),
            "cpu": self._monitor_cpu(),
            "disk": self._monitor_disk(),
            "network": self._monitor_network(),
        }

        # Verifica memória
        if self.resources["memory"]["percent"] > self._thresholds["memory"] * 100:
            self._alerts.append(
                {
                    "resource": "memory",
                    "severity": "high",
                    "message": f"Uso de memória alto: {self.resources['memory']['percent']}%",
                    "timestamp": datetime.now(),
                }
            )

        # Verifica CPU
        if self.resources["cpu"]["percent"] > self._thresholds["cpu"] * 100:
            self._alerts.append(
                {
                    "resource": "cpu",
                    "severity": "high",
                    "message": f"Uso de CPU alto: {self.resources['cpu']['percent']}%",
                    "timestamp": datetime.now(),
                }
            )

        # Verifica disco
        if self.resources["disk"]["percent"] > self._thresholds["disk"] * 100:
            self._alerts.append(
                {
                    "resource": "disk",
                    "severity": "high",
                    "message": f"Uso de disco alto: {self.resources['disk']['percent']}%",
                    "timestamp": datetime.now(),
                }
            )

        return self._alerts

    def optimize_resources(self):
        """Otimiza uso de recursos."""
        try:
            # Limpa memória não utilizada
            import gc

            gc.collect()

            # Limpa cache de dados se necessário
            if self.resources["memory"]["percent"] > 90:
                self._clear_data_cache()

            # Otimiza uso de disco
            if self.resources["disk"]["percent"] > 90:
                self._optimize_disk_usage()

            logger.info("Otimização de recursos concluída")
        except Exception as e:
            logger.error(f"Erro ao otimizar recursos: {e}")

    def _clear_data_cache(self):
        """Limpa cache de dados."""
        # Implementar limpeza de cache específica
        pass

    def _optimize_disk_usage(self):
        """Otimiza uso de disco."""
        # Implementar otimização de disco
        pass

    def get_resource_metrics(self) -> Dict:
        """
        Retorna métricas de recursos.

        Returns:
            Dict: Métricas de recursos
        """
        return {
            "current": self.resources,
            "alerts": self._alerts,
            "thresholds": self._thresholds,
        }

    def set_threshold(self, resource: str, value: float):
        """
        Define limite para recurso.

        Args:
            resource: Tipo de recurso
            value: Valor limite (0-1)
        """
        if resource not in self._thresholds:
            raise ValueError(f"Recurso inválido: {resource}")
        if not 0 <= value <= 1:
            raise ValueError("Valor deve estar entre 0 e 1")

        self._thresholds[resource] = value
        logger.info(f"Limite de {resource} definido para {value*100}%")

    def start_monitoring(self, interval: int = 60):
        """
        Inicia monitoramento periódico.

        Args:
            interval: Intervalo em segundos
        """
        import threading

        def monitor():
            while True:
                self.check_resources()
                time.sleep(interval)

        threading.Thread(target=monitor, daemon=True).start()
        logger.info(f"Monitoramento iniciado com intervalo de {interval}s")

class AdvancedLogger:
    """Sistema avançado de logging."""

    def __init__(self):
        self.log_dir = "logs"
        self.handlers = {}
        self.setup_logging()

    def setup_logging(self):
        """Configura sistema de logging."""
        import logging.handlers

        # Cria diretório de logs
        os.makedirs(self.log_dir, exist_ok=True)

        # Configuração base
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Handler para arquivo com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)

        # Handler para erros
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, 'error.log'),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)

        # Handler para auditoria
        audit_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, 'audit.log'),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )

        # Formatadores
        standard_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
        )
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s'
        )

        # Aplica formatadores
        file_handler.setFormatter(standard_formatter)
        error_handler.setFormatter(detailed_formatter)
        audit_handler.setFormatter(audit_formatter)

        # Registra handlers
        self.handlers = {
            'file': file_handler,
            'error': error_handler,
            'audit': audit_handler
        }

        # Adiciona handlers ao logger root
        for handler in self.handlers.values():
            logging.getLogger('').addHandler(handler)

    def audit_log(self, action: str, user: str, details: Dict):
        """
        Registra log de auditoria.
        
        Args:
            action: Ação realizada
            user: Usuário responsável
            details: Detalhes da ação
        """
        audit_message = f"USER: {user} - ACTION: {action} - DETAILS: {json.dumps(details)}"
        logging.getLogger('audit').info(audit_message)

    def get_logs(self, level: str = None, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """
        Recupera logs filtrados.
        
        Args:
            level: Nível de log
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            List[Dict]: Logs filtrados
        """
        logs = []
        log_files = {
            'INFO': 'app.log',
            'ERROR': 'error.log',
            'AUDIT': 'audit.log'
        }

        files_to_check = [log_files[level]] if level else log_files.values()

        for filename in files_to_check:
            filepath = os.path.join(self.log_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        log_entry = self._parse_log_line(line)
                        if log_entry and self._filter_log_entry(log_entry, level, start_date, end_date):
                            logs.append(log_entry)

        return sorted(logs, key=lambda x: x['timestamp'])

    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """
        Converte linha de log em dicionário.
        
        Args:
            line: Linha do log
            
        Returns:
            Optional[Dict]: Entrada de log parseada
        """
        try:
            # Formato: timestamp - name - level - message
            parts = line.strip().split(' - ', 3)
            if len(parts) < 4:
                return None

            return {
                'timestamp': datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S,%f'),
                'name': parts[1],
                'level': parts[2],
                'message': parts[3]
            }
        except Exception:
            return None

    def _filter_log_entry(self, entry: Dict, level: str, start_date: datetime, end_date: datetime) -> bool:
        """
        Filtra entrada de log.
        
        Args:
            entry: Entrada de log
            level: Nível desejado
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            bool: True se entrada atende filtros
        """
        if level and entry['level'] != level:
            return False

        if start_date and entry['timestamp'] < start_date:
            return False

        if end_date and entry['timestamp'] > end_date:
            return False

        return True


def main():
    """Função principal do sistema."""
    resources_to_cleanup: List[Tuple[str, Any]] = []
    logger = logging.getLogger(__name__)

    try:
        # Inicialização básica
        logger.info("Iniciando aplicação...")
        
        # Carrega configuração
        config = Config()
        excel_path = config.get('data', {}).get('excel_path')
        
        if not excel_path:
            raise ValueError("Caminho do arquivo Excel não definido na configuração")

        # Sistema de logging
        logging.basicConfig(
            level=config.get('logging', {}).get('level', 'INFO'),
            format=config.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        # Gerenciador de recursos
        resource_manager = ResourceManager()
        resource_manager.start_monitoring()
        resources_to_cleanup.append(('resource_manager', resource_manager))

        # Monitor de performance
        performance_monitor = setup_performance_monitoring()
        resources_to_cleanup.append(('performance_monitor', performance_monitor))

        # Sistema de backup
        backup_manager = setup_backup()
        resources_to_cleanup.append(('backup_manager', backup_manager))
        logger.info("Sistema de backup configurado com sucesso")

        # Sistema de manutenção
        maintenance_manager = setup_maintenance()
        resources_to_cleanup.append(('maintenance_manager', maintenance_manager))
        logger.info("Sistema de manutenção configurado com sucesso")

        # Inicia thread de monitoramento de manutenção
        maintenance_thread = threading.Thread(
            target=run_maintenance_loop,
            args=(maintenance_manager,),
            daemon=True
        )
        maintenance_thread.start()

        # Sistema de segurança
        security_manager = setup_security()
        resources_to_cleanup.append(('security_manager', security_manager))

        # Carregamento e processamento de dados
        logger.info("Iniciando carregamento dos dados...")
        loader = DataLoader(excel_path)

        try:
            # Carrega os dados
            df = loader.load()
            logger.info(f"Dados carregados com sucesso. Total de SSAs: {len(df)}")

            # Backup inicial dos dados
            backup_manager.create_backup(df)

            # Processamento dos dados
            ssas = loader.get_ssa_objects()
            logger.info(f"Convertidos {len(ssas)} registros para objetos SSAData")

            # Análise inicial
            ssas_alta_prioridade = loader.filter_ssas(prioridade="S3.7")
            logger.info(f"Total de SSAs com alta prioridade: {len(ssas_alta_prioridade)}")

            # Gera relatório inicial
            logger.info("Gerando relatório inicial...")
            reporter = SSAReporter(df)
            reporter.save_excel_report("relatorio_ssas.xlsx")
            logger.info("Relatório Excel gerado com sucesso")

            # Verifica recursos
            resource_alerts = resource_manager.check_resources()
            if resource_alerts:
                logger.warning(f"Alertas de recursos detectados: {len(resource_alerts)}")
                for alert in resource_alerts:
                    logger.warning(f"Alerta: {alert['message']}")

            # Inicia dashboard
            logger.info("Iniciando dashboard...")
            app = SSADashboard(df)

            # Configurações do servidor
            host = config.get('server', {}).get('host', '0.0.0.0')
            port = config.get('server', {}).get('port', 8050)
            debug = config.get('server', {}).get('debug', False)

            logger.info(f"Iniciando servidor em {host}:{port}")
            app.run_server(debug=debug, host=host, port=port)

        except Exception as e:
            logger.error(f"Erro ao processar dados: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}")
        logger.error(traceback.format_exc())
        raise

    finally:
        logger.info("Finalizando aplicação...")
        # Cleanup de recursos em ordem reversa
        for resource_name, resource in reversed(resources_to_cleanup):
            try:
                if hasattr(resource, "stop"):
                    resource.stop()
                elif hasattr(resource, "cleanup"):
                    resource.cleanup()
                elif hasattr(resource, "close"):
                    resource.close()
                logger.info(f"Finalizado {resource_name}")
            except Exception as e:
                logger.error(f"Erro ao limpar recurso {resource_name}: {e}")


def run_maintenance_loop(maintenance_manager):
    """Executa o loop de manutenção em uma thread separada."""
    while True:
        try:
            maintenance_manager.run()
            time.sleep(60)  # Verifica a cada minuto
        except Exception as e:
            logger.error(f"Erro no loop de manutenção: {e}")
            time.sleep(60)  # Continua tentando mesmo com erro


if __name__ == "__main__":
    main()
