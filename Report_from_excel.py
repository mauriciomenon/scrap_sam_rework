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
import pdfkit

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
        self.ssa_objects = []

    def load_data(self) -> pd.DataFrame:
        """Carrega dados do Excel com as configurações corretas."""
        try:
            # Carrega o Excel pulando as duas primeiras linhas
            self.df = pd.read_excel(
                self.excel_path,
                header=2,  # Cabeçalho na terceira linha
            )

            # Converte a coluna de data usando o formato brasileiro específico
            try:
                self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.to_datetime(
                    self.df.iloc[:, SSAColumns.EMITIDA_EM],
                    format="%d/%m/%Y %H:%M:%S",
                    errors="coerce",
                )

                # Log do resultado da conversão
                valid_dates = self.df.iloc[:, SSAColumns.EMITIDA_EM].notna().sum()
                total_dates = len(self.df)
                logging.info(
                    f"Convertidas {valid_dates} de {total_dates} datas com sucesso"
                )

                if valid_dates == 0:
                    logging.error("Nenhuma data foi convertida com sucesso")
                elif valid_dates < total_dates:
                    logging.warning(
                        f"Algumas datas ({total_dates - valid_dates}) não puderam ser convertidas"
                    )

            except Exception as e:
                logging.error(f"Erro ao processar datas: {str(e)}")
                self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.NaT

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
                self.df.iloc[:, col] = (
                    self.df.iloc[:, col].astype(str).replace("nan", "")
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
                self.df.iloc[:, col] = (
                    self.df.iloc[:, col].astype(str).replace("nan", None)
                )

            # Padroniza prioridades para maiúsculas
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] = (
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                .str.upper()
                .str.strip()
            )

            # Remove linhas com número da SSA vazio
            self.df = self.df[self.df.iloc[:, SSAColumns.NUMERO_SSA].str.strip() != ""]

            # Converte para objetos SSAData
            self._convert_to_objects()

            # Log exemplo das primeiras datas convertidas para verificação
            if not self.df.empty:
                sample_dates = self.df.iloc[:5, SSAColumns.EMITIDA_EM]
                logging.info("Exemplos de datas convertidas:")
                for idx, date in enumerate(sample_dates):
                    logging.info(f"Linha {idx + 1}: {date}")

            return self.df

        except Exception as e:
            logging.error(f"Erro ao carregar dados: {str(e)}")
            raise

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

    def _format_date(self, date):
        """Formata a data para exibição."""
        if pd.isna(date):
            return ""
        return date.strftime("%d/%m/%Y")

    def _get_initial_stats(self):
        """Calcula estatísticas iniciais para o dashboard."""
        total_ssas = len(self.df)
        ssas_por_prioridade = self.df.iloc[
            :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
        ].value_counts()
        ssas_criticas = len(
            self.df[self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"]
        )

        # Contagem por setor
        ssas_por_setor = (
            self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].value_counts().head(5)
        )

        # Datas únicas para mostrar períodos
        datas = pd.to_datetime(self.df.iloc[:, SSAColumns.EMITIDA_EM])
        data_mais_antiga = datas.min()
        data_mais_recente = datas.max()

        return {
            "total": total_ssas,
            "criticas": ssas_criticas,
            "por_prioridade": ssas_por_prioridade,
            "por_setor": ssas_por_setor,
            "periodo": f"{self._format_date(data_mais_antiga)} até {self._format_date(data_mais_recente)}",
        }

    def setup_layout(self):
        """Define o layout do dashboard."""
        stats = self._get_initial_stats()

        self.app.layout = dbc.Container(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            html.H1("Dashboard de SSAs", className="text-primary mb-4"),
                            width=12,
                        )
                    ]
                ),
                # Período de análise
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                f"Período de análise: {stats['periodo']}",
                                className="text-muted mb-4",
                            ),
                            width=12,
                        )
                    ]
                ),
                # Cards com KPIs
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Total de SSAs", className="card-title"
                                            ),
                                            html.H2(
                                                f"{stats['total']:,}",
                                                className="text-primary",
                                            ),
                                        ]
                                    )
                                ],
                                className="mb-4",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "SSAs Críticas (S3.7)",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{stats['criticas']:,}",
                                                className="text-danger",
                                            ),
                                        ]
                                    )
                                ],
                                className="mb-4",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Taxa de Criticidade",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{(stats['criticas']/stats['total']*100):.1f}%",
                                                className="text-warning",
                                            ),
                                        ]
                                    )
                                ],
                                className="mb-4",
                            ),
                            width=4,
                        ),
                    ]
                ),
                # Gráficos
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Distribuição por Prioridade"),
                                        dbc.CardBody(dcc.Graph(id="priority-chart")),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Top 5 Setores"),
                                        dbc.CardBody(dcc.Graph(id="sector-chart")),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=6,
                        ),
                    ]
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
                                                    {"name": "Data", "id": "data"},
                                                    {
                                                        "name": "Prioridade",
                                                        "id": "prioridade",
                                                    },
                                                    {"name": "Setor", "id": "setor"},
                                                    {"name": "Status", "id": "status"},
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
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=12,
                        ),
                    ]
                ),
            ],
            fluid=True,
            className="p-4",
        )

    def _prepare_table_data(self):
        """Prepara os dados para a tabela de SSAs."""
        table_data = []
        for idx, row in self.df.iterrows():
            date = pd.to_datetime(row.iloc[SSAColumns.EMITIDA_EM])
            table_data.append(
                {
                    "numero": row.iloc[SSAColumns.NUMERO_SSA],
                    "data": self._format_date(date),
                    "prioridade": row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                    "setor": row.iloc[SSAColumns.SETOR_EXECUTOR],
                    "status": row.iloc[SSAColumns.SITUACAO],
                }
            )
        return table_data

    def setup_callbacks(self):
        """Configura os callbacks para interatividade."""

        @self.app.callback(
            [Output("priority-chart", "figure"), Output("sector-chart", "figure")],
            [Input("ssa-table", "data")],  # Usar a tabela como trigger
        )
        def update_charts(_):
            # Gráfico de prioridades
            priority_data = self.df.iloc[
                :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
            ].value_counts()
            priority_fig = go.Figure(
                data=[
                    go.Bar(
                        x=priority_data.index,
                        y=priority_data.values,
                        text=priority_data.values,
                        textposition="auto",
                    )
                ]
            )
            priority_fig.update_layout(
                title="Distribuição por Prioridade",
                xaxis_title="Prioridade",
                yaxis_title="Quantidade",
                template="plotly_white",
            )

            # Gráfico de setores
            sector_data = (
                self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].value_counts().head(5)
            )
            sector_fig = go.Figure(
                data=[
                    go.Bar(
                        x=sector_data.index,
                        y=sector_data.values,
                        text=sector_data.values,
                        textposition="auto",
                    )
                ]
            )
            sector_fig.update_layout(
                title="Top 5 Setores",
                xaxis_title="Setor",
                yaxis_title="Quantidade",
                template="plotly_white",
            )

            return priority_fig, sector_fig

    def run_server(self, debug=True, port=8050):
        """Inicia o servidor do dashboard."""
        self.app.run_server(debug=debug, port=port)


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
