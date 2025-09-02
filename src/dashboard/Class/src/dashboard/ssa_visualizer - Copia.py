import pandas as pd
import plotly.graph_objects as go
import logging
from datetime import datetime, date
from ..data.ssa_columns import SSAColumns
from ..utils.log_manager import LogManager


class SSAVisualizer:
    """Gera visualizações específicas para SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.week_analyzer = WeekAnalyzer(df)

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
        """Retorna configuração padrão de layout para gráficos."""
        base_layout = {
            "title": title,
            "template": "plotly_white",
            "showlegend": True,
            "margin": {"l": 50, "r": 20, "t": 50, "b": 50},
        }

        if xaxis_title is not None:
            base_layout["xaxis_title"] = xaxis_title
        if yaxis_title is not None:
            base_layout["yaxis_title"] = yaxis_title

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
            "default": {
                "xaxis": {"showgrid": True, "gridcolor": "lightgray"},
                "yaxis": {"showgrid": True, "gridcolor": "lightgray"},
            },
        }

        type_config = chart_specific.get(chart_type, chart_specific["default"])
        base_layout.update(type_config)

        if x_values is not None and "xaxis" in base_layout:
            base_layout["xaxis"].update(
                {"tickmode": "array", "ticktext": x_values, "tickvals": x_values}
            )

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
            self._get_standard_layout(
                title=f"Distribuição de SSAs por {SSAColumns.get_name(SSAColumns.GRAU_PRIORIDADE_EMISSAO)}",
                xaxis_title="Grau de Prioridade",
                yaxis_title="Quantidade",
                chart_type="bar",
            )
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
                chart_type="bar",
                barmode="stack",
            )
        )

        return fig

    def create_week_chart(self, use_programmed: bool = True) -> go.Figure:
        """Cria gráfico de SSAs por semana com dados completos."""
        analysis = self.week_analyzer.analyze_weeks(use_programmed)

        if analysis.empty:
            return go.Figure().update_layout(
                title=(
                    "SSAs Programadas por Semana"
                    if use_programmed
                    else "SSAs por Semana de Cadastro"
                )
            )

        # Criar um DataFrame pivotado para mostrar prioridades por semana
        pivot_data = pd.pivot_table(
            analysis,
            values="count",
            index="year_week",
            columns="prioridade",
            fill_value=0,
            aggfunc="sum",
        )

        fig = go.Figure()

        # Adicionar barras para cada prioridade
        for priority in pivot_data.columns:
            fig.add_trace(
                go.Bar(
                    name=priority,
                    x=pivot_data.index,
                    y=pivot_data[priority],
                    text=pivot_data[priority],
                    textposition="auto",
                    customdata=analysis[analysis["prioridade"] == priority][
                        "numero_ssa"
                    ].tolist(),
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
            template="plotly_white",
            barmode="stack",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis={"tickangle": -45},
            margin={"l": 50, "r": 20, "t": 50, "b": 100},
        )

        return fig


    def add_weeks_in_state_chart(self, df_filtered=None) -> go.Figure:
        """Cria gráfico mostrando distribuição de SSAs por tempo no estado."""
        df_to_use = df_filtered if df_filtered is not None else self.df
        weeks_in_state = self.week_analyzer.calculate_weeks_in_state()
        valid_weeks = weeks_in_state.dropna()

        if valid_weeks.empty:
            return self._create_empty_chart()

        value_counts = valid_weeks.value_counts().sort_index()
        max_weeks = value_counts.index.max()

        if max_weeks > 50:
            bins = list(range(0, int(max_weeks) + 10, 10))
            labels = [f"{bins[i]}-{bins[i+1]-1} semanas" for i in range(len(bins) - 1)]
            binned_data = pd.cut(value_counts.index, bins=bins, labels=labels, right=False)
            value_counts = value_counts.groupby(binned_data).sum()
        else:
            value_counts.index = [f"{int(x)} semanas" for x in value_counts.index]

        hover_text = []
        ssas_by_interval = {}

        for interval in value_counts.index:
            if pd.isna(interval) or str(interval).strip() == "":
                continue

            try:
                if isinstance(interval, str) and "-" in interval:
                    start, end = map(lambda x: int(x.split()[0]), interval.split("-"))
                    mask = (weeks_in_state >= start) & (weeks_in_state <= end)
                else:
                    weeks = int(interval.split()[0])
                    mask = weeks_in_state == weeks

                ssas = df_to_use[mask].iloc[:, SSAColumns.NUMERO_SSA].tolist()
                ssas_by_interval[str(interval)] = ssas

                ssa_preview = "<br>".join(ssas[:5])
                if len(ssas) > 5:
                    ssa_preview += f"<br>... (+{len(ssas)-5} SSAs)"

                hover_text.append(
                    f"<b>{interval}</b><br>"
                    f"<b>Total SSAs:</b> {len(ssas)}<br>"
                    f"<b>SSAs:</b><br>{ssa_preview}"
                )

            except Exception as e:
                logging.warning(f"Erro ao processar intervalo {interval}: {str(e)}")
                continue

        valid_indices = [
            i for i in range(len(hover_text)) if str(value_counts.index[i]).strip() != ""
        ]

        if not valid_indices:
            return self._create_empty_chart()

        fig = go.Figure(
            [
                go.Bar(
                    x=[value_counts.index[i] for i in valid_indices],
                    y=[value_counts.values[i] for i in valid_indices],
                    text=[value_counts.values[i] for i in valid_indices],
                    textposition="auto",
                    name="SSAs por Semana",
                    marker_color="rgb(64, 83, 177)",
                    hovertext=[hover_text[i] for i in valid_indices],
                    hoverinfo="text",
                    customdata=[list(ssas_by_interval.values())[i] for i in valid_indices],
                    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                    showlegend=False,
                )
            ]
        )

        fig.update_layout(
            title="Distribuição de SSAs por Tempo no Estado Atual",
            xaxis_title="Tempo no Estado",
            yaxis_title="Quantidade de SSAs",
            template="plotly_white",
            showlegend=False,
            xaxis={"tickangle": -45},
            margin={"l": 50, "r": 20, "t": 50, "b": 100},
            annotations=[
                {
                    "text": "Clique nas barras para ver detalhes das SSAs",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.98,
                    "y": 0.02,
                    "showarrow": False,
                    "font": {"size": 10, "color": "gray"},
                    "xanchor": "right",
                }
            ],
        )

        return fig


class WeekAnalyzer:
    """Analisa dados de semanas das SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.current_date = date.today()
        self.current_year = self.current_date.year
        self.current_week = self.current_date.isocalendar()[1]

    def calculate_weeks_in_state(self) -> pd.Series:
        """Calcula quantas semanas cada SSA está em seu estado atual."""

        def get_week_number(week_str):
            if pd.isna(week_str) or not str(week_str).strip():
                return None
            try:
                week_str = str(week_str).replace(".0", "")
                if len(week_str) != 6:
                    return None
                return int(week_str[4:])
            except ValueError:
                return None

        weeks_in_state = self.df.iloc[:, SSAColumns.SEMANA_CADASTRO].apply(get_week_number)
        current_week = int(self.current_date.strftime("%Y%W")[4:])

        # Garante que a diferença seja sempre positiva
        return weeks_in_state.apply(
            lambda x: max(0, current_week - x) if x is not None else None
        )

    def analyze_weeks(self, use_programmed: bool = True) -> pd.DataFrame:
        """Analisa distribuição de SSAs por semana com validação melhorada."""
        week_column = (
            SSAColumns.SEMANA_PROGRAMADA if use_programmed else SSAColumns.SEMANA_CADASTRO
        )

        week_data = []
        for _, row in self.df.iterrows():
            week_str = str(row.iloc[week_column])
            if pd.notna(week_str) and week_str != "None" and week_str != "":
                try:
                    if len(week_str) == 6:  # Formato correto YYYYWW
                        year = int(week_str[:4])
                        week = int(week_str[4:])

                        if 0 < week <= 53 and 2000 <= year <= 2100:  # Validação básica
                            week_data.append(
                                {
                                    "year": year,
                                    "week": week,
                                    "year_week": week_str,
                                    "prioridade": row.iloc[
                                        SSAColumns.GRAU_PRIORIDADE_EMISSAO
                                    ],
                                    "numero_ssa": row.iloc[SSAColumns.NUMERO_SSA],
                                }
                            )
                except (ValueError, TypeError):
                    continue

        if not week_data:
            return pd.DataFrame()

        df_weeks = pd.DataFrame(week_data)

        # Organizar os dados
        analysis = (
            df_weeks.groupby(["year_week", "prioridade"])
            .agg({"numero_ssa": lambda x: list(x), "year": "first", "week": "first"})
            .reset_index()
        )

        # Adicionar contagem
        analysis["count"] = analysis["numero_ssa"].str.len()

        # Ordenar por ano e semana
        analysis = analysis.sort_values(["year", "week"])

        return analysis


    def _create_empty_chart(self) -> go.Figure:
        """Creates an empty chart with a title when no data is available."""
        return go.Figure().update_layout(
            title="Distribuição de SSAs por Tempo no Estado Atual",
            xaxis_title="",
            yaxis_title="",
            annotations=[
                {
                    "text": "Nenhum dado disponível para os filtros selecionados",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 14},
                    "x": 0.5,
                    "y": 0.5,
                }
            ],
        )
