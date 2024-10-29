# Imports (no topo do arquivo)
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import logging
from dash import dash_table
from typing import Dict, List, Optional
import warnings
import traceback
import xlsxwriter

# Depois de todos os imports
warnings.filterwarnings("ignore")


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
        self.ssa_objects = []  # Lista para armazenar os objetos SSAData

    def load_data(self) -> pd.DataFrame:
        """Carrega dados do Excel com as configurações corretas."""
        try:
            self.df = pd.read_excel(
                self.excel_path,
                header=2,  # Cabeçalho na terceira linha
            )

            # Força conversão explícita das colunas importantes
            self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.to_datetime(
                self.df.iloc[:, SSAColumns.EMITIDA_EM], errors="coerce"
            )

            # Converte para string as colunas que precisam ser string
            string_columns = [
                SSAColumns.NUMERO_SSA,
                SSAColumns.SITUACAO,
                SSAColumns.SEMANA_CADASTRO,
                SSAColumns.GRAU_PRIORIDADE_EMISSAO,
            ]
            for col in string_columns:
                self.df.iloc[:, col] = self.df.iloc[:, col].astype(str)

            # Converte os dados para objetos SSAData
            self._convert_to_objects()

            return self.df

        except Exception as e:
            logging.error(f"Erro ao carregar dados: {e}")
            raise

    def _convert_to_objects(self):
        """Converte as linhas do DataFrame em objetos SSAData."""
        try:
            self.ssa_objects = []
            for idx, row in self.df.iterrows():
                try:
                    ssa = SSAData(
                        numero=str(row.iloc[SSAColumns.NUMERO_SSA]),
                        situacao=str(row.iloc[SSAColumns.SITUACAO]),
                        derivada=str(row.iloc[SSAColumns.DERIVADA]),
                        localizacao=str(row.iloc[SSAColumns.LOCALIZACAO]),
                        desc_localizacao=str(row.iloc[SSAColumns.DESC_LOCALIZACAO]),
                        equipamento=str(row.iloc[SSAColumns.EQUIPAMENTO]),
                        semana_cadastro=str(row.iloc[SSAColumns.SEMANA_CADASTRO]),
                        emitida_em=row.iloc[SSAColumns.EMITIDA_EM],
                        descricao=str(row.iloc[SSAColumns.DESC_SSA]),
                        setor_emissor=str(row.iloc[SSAColumns.SETOR_EMISSOR]),
                        setor_executor=str(row.iloc[SSAColumns.SETOR_EXECUTOR]),
                        solicitante=str(row.iloc[SSAColumns.SOLICITANTE]),
                        servico_origem=str(row.iloc[SSAColumns.SERVICO_ORIGEM]),
                        prioridade_emissao=str(
                            row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                        ),
                        prioridade_planejamento=str(
                            row.iloc[SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO]
                        ),
                        execucao_simples=str(row.iloc[SSAColumns.EXECUCAO_SIMPLES]),
                        responsavel_programacao=str(
                            row.iloc[SSAColumns.RESPONSAVEL_PROGRAMACAO]
                        ),
                        semana_programada=str(row.iloc[SSAColumns.SEMANA_PROGRAMADA]),
                        responsavel_execucao=str(
                            row.iloc[SSAColumns.RESPONSAVEL_EXECUCAO]
                        ),
                        descricao_execucao=str(row.iloc[SSAColumns.DESCRICAO_EXECUCAO]),
                        sistema_origem=str(row.iloc[SSAColumns.SISTEMA_ORIGEM]),
                        anomalia=str(row.iloc[SSAColumns.ANOMALIA]),
                    )
                    self.ssa_objects.append(ssa)
                except Exception as e:
                    logging.error(f"Erro ao converter linha {idx}: {e}")
                    continue
            logging.info(f"Convertidos {len(self.ssa_objects)} registros para SSAData")
        except Exception as e:
            logging.error(f"Erro durante conversão para objetos: {e}")
            raise

    def get_ssa_objects(self) -> List[SSAData]:
        """Retorna a lista de objetos SSAData."""
        if not self.ssa_objects:
            self._convert_to_objects()
        return self.ssa_objects

    def filter_ssas(
        self,
        setor: Optional[str] = None,
        prioridade: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[SSAData]:
        """Filtra SSAs com base nos critérios fornecidos."""
        filtered_ssas = self.get_ssa_objects()

        if setor:
            filtered_ssas = [
                ssa for ssa in filtered_ssas if ssa.setor_executor == setor
            ]

        if prioridade:
            filtered_ssas = [
                ssa for ssa in filtered_ssas if ssa.prioridade_emissao == prioridade
            ]

        if data_inicio:
            filtered_ssas = [
                ssa for ssa in filtered_ssas if ssa.emitida_em >= data_inicio
            ]

        if data_fim:
            filtered_ssas = [ssa for ssa in filtered_ssas if ssa.emitida_em <= data_fim]

        return filtered_ssas


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


class SSAAnalyzer:
    """Análise específica para os dados de SSA."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def analyze_by_priority(self) -> Dict:
        """Analisa SSAs por grau de prioridade."""
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
        """Analisa distribuição de SSAs por setor."""
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
        """Analisa status de execução das SSAs."""
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
        """Analisa tendências de prioridade ao longo do tempo."""
        return pd.crosstab(
            self.df.iloc[:, SSAColumns.EMITIDA_EM].dt.date,
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO],
        ).reset_index()

    def analyze_workload(self) -> pd.DataFrame:
        """Analisa carga de trabalho por setor/responsável."""
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
        self.df = df

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

            # Gera análise temporal apenas se a coluna de data estiver correta
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

            # Resto das análises que não dependem de data
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
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """Define o layout do dashboard."""
        # Obter datas min e max com tratamento de erro
        try:
            date_col = self.df.iloc[:, SSAColumns.EMITIDA_EM]
            valid_dates = date_col[date_col.notna()]
            min_date = valid_dates.min() if not valid_dates.empty else None
            max_date = valid_dates.max() if not valid_dates.empty else None

            # Converter para string no formato que o DatePickerRange aceita
            min_date_str = (
                min_date.strftime("%Y-%m-%d") if min_date is not None else None
            )
            max_date_str = (
                max_date.strftime("%Y-%m-%d") if max_date is not None else None
            )
        except Exception as e:
            logging.warning(f"Erro ao processar datas: {e}")
            min_date_str = None
            max_date_str = None

        self.app.layout = dbc.Container(
            [
                # Cabeçalho
                dbc.Row(
                    [
                        dbc.Col(
                            html.H1(
                                "Dashboard de Análise de SSAs",
                                className="text-primary mb-4",
                            ),
                            width=12,
                        )
                    ]
                ),
                # Filtros
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Filtros", className="text-secondary mb-3"),
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                # Filtro de Setor
                                                html.Label(
                                                    f"{SSAColumns.get_name(SSAColumns.SETOR_EXECUTOR)}:"
                                                ),
                                                dcc.Dropdown(
                                                    id="setor-filter",
                                                    options=[
                                                        {"label": x, "value": x}
                                                        for x in sorted(
                                                            self.df.iloc[
                                                                :,
                                                                SSAColumns.SETOR_EXECUTOR,
                                                            ].unique()
                                                        )
                                                        if pd.notna(x)
                                                    ],
                                                    multi=True,
                                                ),
                                                # Filtro de Prioridade
                                                html.Label(
                                                    f"{SSAColumns.get_name(SSAColumns.GRAU_PRIORIDADE_EMISSAO)}:",
                                                    className="mt-3",
                                                ),
                                                dcc.Dropdown(
                                                    id="priority-filter",
                                                    options=[
                                                        {"label": x, "value": x}
                                                        for x in sorted(
                                                            self.df.iloc[
                                                                :,
                                                                SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                                                            ].unique()
                                                        )
                                                        if pd.notna(x)
                                                    ],
                                                    multi=True,
                                                ),
                                                # Filtro de Data
                                                html.Label(
                                                    f"{SSAColumns.get_name(SSAColumns.EMITIDA_EM)}:",
                                                    className="mt-3",
                                                ),
                                                (
                                                    dcc.DatePickerRange(
                                                        id="date-filter",
                                                        start_date=min_date_str,
                                                        end_date=max_date_str,
                                                        display_format="DD/MM/YYYY",
                                                    )
                                                    if min_date_str and max_date_str
                                                    else html.Div(
                                                        "Datas não disponíveis"
                                                    )
                                                ),
                                            ]
                                        )
                                    ]
                                ),
                            ],
                            width=3,
                        ),
                        # KPIs
                        dbc.Col(
                            [
                                html.H4(
                                    "Indicadores Principais",
                                    className="text-secondary mb-3",
                                ),
                                self.create_kpi_cards(),
                            ],
                            width=9,
                        ),
                    ]
                ),
                # Gráficos
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader("Distribuição por Prioridade"),
                                    dbc.CardBody(dcc.Graph(id="priority-chart")),
                                ]
                            ),
                            width=6,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader("Carga por Setor"),
                                    dbc.CardBody(dcc.Graph(id="sector-chart")),
                                ]
                            ),
                            width=6,
                        ),
                    ],
                    className="mt-4",
                ),
                # Tabela de detalhes
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4(
                                    "Detalhamento", className="text-secondary mt-4 mb-3"
                                ),
                                self._create_data_table(),
                            ],
                            width=12,
                        )
                    ]
                ),
            ],
            fluid=True,
        )

    def _create_data_table(self):
        """Cria tabela de dados com tratamento de erro."""
        try:
            return dash_table.DataTable(
                id="ssa-table",
                columns=[
                    {"name": SSAColumns.get_name(col), "id": str(col)}
                    for col in [
                        SSAColumns.NUMERO_SSA,
                        SSAColumns.SITUACAO,
                        SSAColumns.SETOR_EXECUTOR,
                        SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                        SSAColumns.EMITIDA_EM,
                    ]
                ],
                page_size=10,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left"},
                style_header={
                    "backgroundColor": "rgb(230, 230, 230)",
                    "fontWeight": "bold",
                },
            )
        except Exception as e:
            logging.error(f"Erro ao criar tabela: {e}")
            return html.Div("Erro ao carregar tabela de dados")

    def setup_callbacks(self):
        """Configura os callbacks para interatividade."""

        @self.app.callback(
            [
                Output("ssa-table", "data"),
                Output("priority-chart", "figure"),
                Output("sector-chart", "figure"),
            ],
            [
                Input("setor-filter", "value"),
                Input("priority-filter", "value"),
                Input("date-filter", "start_date"),
                Input("date-filter", "end_date"),
            ],
        )
        def update_data(setores, prioridades, start_date, end_date):
            """Atualiza os dados com base nos filtros."""
            try:
                df_filtered = self.df.copy()

                # Aplica filtros
                if setores:
                    df_filtered = df_filtered[
                        df_filtered.iloc[:, SSAColumns.SETOR_EXECUTOR].isin(setores)
                    ]
                if prioridades:
                    df_filtered = df_filtered[
                        df_filtered.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].isin(
                            prioridades
                        )
                    ]
                if start_date:
                    df_filtered = df_filtered[
                        df_filtered.iloc[:, SSAColumns.EMITIDA_EM].dt.date
                        >= pd.to_datetime(start_date).date()
                    ]
                if end_date:
                    df_filtered = df_filtered[
                        df_filtered.iloc[:, SSAColumns.EMITIDA_EM].dt.date
                        <= pd.to_datetime(end_date).date()
                    ]

                # Cria visualizações
                viz = SSAVisualizer(df_filtered)

                # Retorna dados atualizados
                return (
                    df_filtered.to_dict("records"),
                    viz.create_priority_chart(),
                    viz.create_sector_workload(),
                )
            except Exception as e:
                logging.error(f"Erro ao atualizar dashboard: {e}")
                # Retorna dados vazios em caso de erro
                return [], {}, {}

    def run_server(self, debug=True, port=8050):
        """Inicia o servidor do dashboard."""
        try:
            logging.info(f"Iniciando servidor na porta {port}")
            self.app.run_server(debug=debug, port=port)
        except Exception as e:
            logging.error(f"Erro ao iniciar servidor: {e}")
            raise

    def create_kpi_cards(self):
        """Cria cards para os KPIs principais."""
        return dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("Total de SSAs", className="card-title"),
                                    html.H3(len(self.df), className="text-primary"),
                                ]
                            )
                        ]
                    )
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("Alta Prioridade", className="card-title"),
                                    html.H3(
                                        len(
                                            self.df[
                                                self.df.iloc[
                                                    :,
                                                    SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                                                ]
                                                == "S3.7"
                                            ]
                                        ),
                                        className="text-danger",
                                    ),
                                ]
                            )
                        ]
                    )
                ),
            ]
        )


def check_dependencies():
    """Verifica e instala dependências necessárias."""
    try:
        import xlsxwriter
    except ImportError:
        logging.warning("xlsxwriter não encontrado. Tentando instalar...")
        import subprocess

        subprocess.check_call(["pip", "install", "xlsxwriter"])
        logging.info("xlsxwriter instalado com sucesso")


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
        loader = DataLoader(
            r"C:\Users\menon\git\trabalho\SCRAP-SAM\Downloads\SSAs Pendentes Geral - 28-10-2024_1221PM.xlsx"
        )
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
        dashboard.run_server(debug=True, port=8050)

    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}")
        logger.error(traceback.format_exc())
        raise
