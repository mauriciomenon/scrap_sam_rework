# src/dashboard/ssa_dashboard.py
import dash
from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging
from typing import Any, cast
from datetime import datetime
from flask import request
from .ssa_visualizer import SSAVisualizer
from .kpi_calculator import KPICalculator
from ..data.ssa_columns import SSAColumns
from ..utils.log_manager import LogManager


class SSADashboard:
    """Dashboard interativo para análise de SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )

        # Configurar logger
        self.logger = LogManager()
        
        # User interaction history - addresses "o que acabei de falar" request
        self.user_history = []

        # Configurar servidor Flask subjacente
        server = self.app.server

        # Adicionar middleware para logging
        @server.before_request
        def log_request_info():
            self.logger.log_with_ip("INFO", f"Acesso à rota: {request.path}")
            # Log user interactions to history
            if request.path != '/favicon.ico' and request.path != '/_dash-dependencies':
                self._add_to_history(f"Acessou: {request.path}", "navigation")

        self.visualizer = SSAVisualizer(df)
        self.kpi_calc = KPICalculator(df)
        self.week_analyzer = self.visualizer.week_analyzer
        self.setup_layout()
        self.setup_callbacks()
    
    def _add_to_history(self, action: str, action_type: str = "action"):
        """Add user action to history - answers 'what did I just say/do'."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.user_history.append({
            'time': timestamp,
            'action': action,
            'type': action_type
        })
        # Keep only last 10 items
        if len(self.user_history) > 10:
            self.user_history.pop(0)
    
    def _get_recent_history_html(self):
        """Get recent user history as HTML - shows 'what I just said/did'."""
        if not self.user_history:
            return html.P("Nenhuma ação recente", className="text-muted")
        
        history_items = []
        for item in reversed(self.user_history[-5:]):  # Show last 5 items
            history_items.append(
                html.Li([
                    html.Span(item['time'], className="text-primary fw-bold"),
                    html.Span(" - ", className="text-muted"),
                    html.Span(item['action'])
                ])
            )
        
        return html.Ul(history_items, className="list-unstyled")

    def _get_initial_stats(self):
        """Calcula estatísticas iniciais para o dashboard."""
        try:
            # Estatísticas básicas
            total_ssas = len(self.df)

            # Estatísticas de prioridade
            prioridades = self.df.iloc[
                :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
            ].value_counts()
            ssas_criticas = len(
                self.df[
                    self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].str.upper()
                    == "S3.7"
                ]
            )
            taxa_criticidade = (
                (ssas_criticas / total_ssas * 100) if total_ssas > 0 else 0
            )

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
                .replace("", np.nan)
                .dropna()
                .nunique(),
                "execucao": self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
                .replace("", np.nan)
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
                "por_prioridade": pd.Series(dtype="object"),
                "por_setor": pd.Series(dtype="object"),
                "por_estado": pd.Series(dtype="object"),
                "periodo": {"inicio": "N/A", "fim": "N/A"},
                "responsaveis": {"programacao": 0, "execucao": 0},
            }

    def _get_state_counts(self):
        """Obtém contagem de SSAs por estado."""
        return self.df.iloc[:, SSAColumns.SITUACAO].value_counts().to_dict()

    def _get_programmed_by_week(self):
        """Obtém SSAs programadas por semana."""
        week_info = getattr(self.week_analyzer, "analyze_week_distribution", lambda: pd.DataFrame())()
        if isinstance(week_info, pd.DataFrame) and not week_info.empty and "week_count" in week_info:
            return week_info["week_count"]
        return pd.Series(dtype="int64")  # Retorna série vazia se não houver dados

    def _get_responsaveis(self):
        """Obtém lista de responsáveis únicos."""
        prog = self.df.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO].unique()
        exec_ = self.df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].unique()
        return {
            "programacao": sorted([x for x in prog if pd.notna(x) and x != ""]),
            "execucao": sorted([x for x in exec_ if pd.notna(x) and x != ""]),
        }

    def _get_chart_config(self):
        """
        Returns updated chart configuration with royal blue theme.

        Returns:
            dict: Chart configuration settings
        """
        return {
            "displayModeBar": True,
            "scrollZoom": False,
            "modeBarButtonsToRemove": [
                "pan2d",
                "select2d",
                "lasso2d",
                "autoScale2d",
                "zoom2d",
            ],
            "displaylogo": False,
            "responsive": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": "chart",
                "height": 500,
                "width": 700,
                "scale": 2,
            },
            "plotlyServerURL": "",
            "theme": {
                "colors": [
                    "#1e3799",  # Primary
                    "#4a69bd",  # Secondary
                    "#6a89cc",  # Info
                    "#78e08f",  # Success
                    "#e55039",  # Danger
                ]
            },
        }

    def _chart_config(self) -> Any:
        """Return Plotly config typed as Any to satisfy Dash component typing."""
        return cast(Any, self._get_chart_config())

    def run_server(self, debug: bool = True, port: int = 8080, host: str = "0.0.0.0"):
        """Inicia o servidor do dashboard com compatibilidade entre versões do Dash."""
        self.logger.log_with_ip("INFO", "Iniciando servidor do dashboard")
        try:
            run = getattr(self.app, "run", None)
            if callable(run):
                self.app.run(debug=debug, port=port, host=host)
            else:
                # Fallback para versões antigas
                self.app.run_server(debug=debug, port=port, host=host)
        except Exception as e:
            self.logger.log_with_ip("ERROR", f"Erro ao iniciar servidor: {str(e)}")

    def _create_hover_text(self, ssas, title):
        """Creates hover text for charts."""
        if len(ssas) == 0:
            return "Nenhuma SSA encontrada"

        ssa_preview = "<br>".join(ssas[:5])
        if len(ssas) > 5:
            ssa_preview += f"<br>... (+{len(ssas)-5} SSAs)"

        return (
            f"<b>{title}</b><br>"
            f"<b>Total SSAs:</b> {len(ssas)}<br>"
            f"<b>Primeiras SSAs:</b><br>{ssa_preview}"
        )

    def _create_ssa_list(self, ssas):
        """Creates clickable SSA list with copy and link functionality."""
        if not ssas or len(ssas) == 0:
            return html.Div("Nenhuma SSA encontrada para este período/categoria.")

        return html.Div(
            [
                html.Button(
                    f"Copiar todas ({len(ssas)})",
                    id="copy-all-ssas",
                    n_clicks=0,
                    style={
                        "marginBottom": "10px",
                        "padding": "5px 10px",
                        "backgroundColor": "#f8f9fa",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "4px",
                        "cursor": "pointer",
                    },
                ),
                html.Div(
                    ",".join(str(ssa) for ssa in ssas),
                    id="all-ssas-data",
                    style={"display": "none"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.A(
                                    str(ssa),
                                    href=f"https://osprd.itaipu/SAM_SMA/SSAPublicView.aspx?SerialNumber={ssa}&language=pt",
                                    target="_blank",
                                    id=f"ssa-link-{ssa}",
                                    style={
                                        "textDecoration": "none",
                                        "color": "inherit",
                                        "flex": "1",
                                    },
                                ),
                                html.Button(
                                    "📋",
                                    id={"type": "copy-button", "index": i},
                                    title=str(ssa),
                                    style={
                                        "cursor": "pointer",
                                        "border": "none",
                                        "background": "none",
                                        "padding": "0 5px",
                                    },
                                ),
                            ],
                            style={
                                "padding": "3px 8px",
                                "margin": "1px 0",
                                "background": "#f8f9fa",
                                "borderRadius": "3px",
                                "display": "flex",
                                "alignItems": "center",
                                "width": "200px",
                                "transition": "background-color 0.2s",
                            },
                        )
                        for i, ssa in enumerate(ssas)
                        if ssa
                    ],
                    style={
                        "maxHeight": "500px",
                        "overflowY": "auto",
                        "padding": "5px",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "2px",
                    },
                ),
            ]
        )

    def _enhance_bar_chart(self, fig, chart_type, title, df_filtered=None):
        """Enhances bar chart with hover info and clickable data."""
        df_to_use = df_filtered if df_filtered is not None else self.df

        try:
            for trace in fig.data:
                if isinstance(trace, go.Bar):
                    hover_text = []
                    customdata = []
                    new_y = []

                    # Safely obtain x values without relying on truthiness of numpy arrays
                    x_vals = getattr(trace, "x", None)
                    if x_vals is None:
                        categories = []
                    elif isinstance(x_vals, (list, tuple, pd.Index)):
                        categories = list(x_vals)
                    else:
                        try:
                            categories = list(x_vals)
                        except Exception:
                            categories = []

                    for cat in categories:
                        mask = None
                        if chart_type == "resp_prog":
                            mask = (
                                df_to_use.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO]
                                == cat
                            )
                        elif chart_type == "resp_exec":
                            mask = (
                                df_to_use.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO]
                                == cat
                            )
                        elif chart_type == "state":
                            mask = df_to_use.iloc[:, SSAColumns.SITUACAO] == cat
                        elif chart_type == "week_programmed":
                            mask = df_to_use.iloc[
                                :, SSAColumns.SEMANA_PROGRAMADA
                            ] == str(cat)
                            if getattr(trace, "name", None):
                                mask = mask & (
                                    df_to_use.iloc[
                                        :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
                                    ]
                                    == getattr(trace, "name", None)
                                )
                        elif chart_type == "week_registration":
                            mask = df_to_use.iloc[:, SSAColumns.SEMANA_CADASTRO] == str(
                                cat
                            )
                            if getattr(trace, "name", None):
                                mask = mask & (
                                    df_to_use.iloc[
                                        :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
                                    ]
                                    == getattr(trace, "name", None)
                                )
                        else:
                            continue

                        if mask is not None:
                            ssas = (
                                df_to_use[mask]
                                .iloc[:, SSAColumns.NUMERO_SSA]
                                .astype(str)
                                .tolist()
                            )
                        else:
                            ssas = []

                        new_y.append(len(ssas))

                        # Texto do hover
                        ssa_preview = "<br>".join(ssas[:5])
                        if len(ssas) > 5:
                            ssa_preview += f"<br>... (+{len(ssas)-5} SSAs)"

                        title_text = str(cat)
                        if getattr(trace, "name", None):
                            title_text += f" - {getattr(trace, 'name', None)}"

                        hover_text.append(
                            f"<b>{title_text}</b><br>"
                            f"Total SSAs: {len(ssas)}<br>"
                            f"SSAs:<br>{ssa_preview}"
                        )
                        customdata.append(ssas)

                    trace.update(
                        y=new_y,
                        text=new_y,  # Atualiza os rótulos das barras
                        hovertext=hover_text,
                        hoverinfo="text",
                        customdata=customdata,
                        textposition="auto",
                        hoverlabel=dict(
                            bgcolor="white", font_size=12, font_family="Arial"
                        ),
                    )

            fig.update_layout(
                dragmode="pan",
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True),
            )

        except Exception as e:
            logging.error(f"Erro ao melhorar gráfico: {str(e)}")
            return fig

        return fig

    def _create_resp_prog_chart(self, df_filtered):
        """
        Creates the bar chart for programming responsibles.

        Args:
            df_filtered (pd.DataFrame): Filtered dataframe containing SSA data

        Returns:
            go.Figure: Plotly figure object with the bar chart
        """
        try:
            # Get counts for each responsible
            resp_prog_counts = df_filtered.iloc[
                :, SSAColumns.RESPONSAVEL_PROGRAMACAO
            ].value_counts()

            if resp_prog_counts.empty:
                return self._create_empty_chart("SSAs por Responsável na Programação")

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=resp_prog_counts.index,
                        y=resp_prog_counts.values,
                        text=resp_prog_counts.values,
                        textposition="auto",
                        marker_color="#4a69bd",  # Consistent with theme
                        hovertemplate="<b>%{x}</b><br>"
                        + "SSAs: %{y}<br>"
                        + "<extra></extra>",
                    )
                ]
            )

            fig.update_layout(
                title="SSAs por Responsável na Programação",
                xaxis_title="Responsável",
                yaxis_title="Quantidade",
                template="plotly_white",
                showlegend=False,
                xaxis={"tickangle": -45},
                margin={"l": 50, "r": 20, "t": 50, "b": 100},
                hoverlabel={"bgcolor": "white"},
                yaxis={"gridcolor": "#eee"},
            )

            return fig
        except Exception as e:
            logging.error(
                f"Erro ao criar gráfico de responsáveis na programação: {str(e)}"
            )
            return self._create_empty_chart("SSAs por Responsável na Programação")

    def _create_resp_exec_chart(self, df):
        """Cria o gráfico de responsáveis na execução."""
        resp_exec_counts = df.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO].value_counts()

        fig = go.Figure(
            data=[
                go.Bar(
                    x=resp_exec_counts.index,
                    y=resp_exec_counts.values,
                    text=resp_exec_counts.values,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="SSAs por Responsável na Execução",
            xaxis_title="Responsável",
            yaxis_title="Quantidade",
            template="plotly_white",
            showlegend=False,
            xaxis={"tickangle": -45},
            margin={"l": 50, "r": 20, "t": 50, "b": 100},
        )

        return fig

    def _create_detail_state_chart(self, df):
        """Cria o gráfico de detalhamento por estado."""
        state_counts = df.iloc[:, SSAColumns.SITUACAO].value_counts()

        # Cores específicas para cada estado
        state_colors = {
            "AAD": "#007bff",  # Azul
            "ADM": "#28a745",  # Verde
            "AAT": "#dc3545",  # Vermelho
            "SPG": "#ffc107",  # Amarelo
            "AIM": "#17a2b8",  # Ciano
            "APV": "#6610f2",  # Roxo
            "APG": "#fd7e14",  # Laranja
            "SCD": "#20c997",  # Verde água
            "ADI": "#e83e8c",  # Rosa
            "APL": "#6c757d",  # Cinza
        }

        fig = go.Figure(
            data=[
                go.Bar(
                    x=state_counts.index,
                    y=state_counts.values,
                    text=state_counts.values,
                    textposition="auto",
                    showlegend=False,
                    marker_color="rgb(64, 83, 177)",
                )
            ]
        )

        fig.update_layout(
            title="SSAs Pendentes por Estado",
            xaxis_title="Estado",
            yaxis_title="Quantidade",
            template="plotly_white",
            showlegend=False,
            margin={"l": 50, "r": 20, "t": 50, "b": 50},
        )

        return fig

    def _create_detail_week_chart(self, df):
        """Cria o gráfico de detalhamento por semana."""
        filtered_visualizer = SSAVisualizer(df)
        return filtered_visualizer.create_week_chart(use_programmed=True)

    def _prepare_table_data(self, df):
        """Prepara dados para a tabela com informações adicionais."""
        return [
            {
                "numero": f"[{row.iloc[SSAColumns.NUMERO_SSA]}](https://osprd.itaipu/SAM_SMA/SSAPublicView.aspx?SerialNumber={row.iloc[SSAColumns.NUMERO_SSA]}&language=pt)",
                "estado": row.iloc[SSAColumns.SITUACAO],
                "setor_emissor": row.iloc[SSAColumns.SETOR_EMISSOR],
                "setor_executor": row.iloc[SSAColumns.SETOR_EXECUTOR],
                "resp_prog": row.iloc[SSAColumns.RESPONSAVEL_PROGRAMACAO],
                "resp_exec": row.iloc[SSAColumns.RESPONSAVEL_EXECUCAO],
                "semana_prog": row.iloc[SSAColumns.SEMANA_PROGRAMADA],
                "prioridade": row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO],
                "data_emissao": (
                    row.iloc[SSAColumns.EMITIDA_EM].strftime("%d/%m/%Y %H:%M")
                    if pd.notnull(row.iloc[SSAColumns.EMITIDA_EM])
                    else ""
                ),
                "descricao": row.iloc[SSAColumns.DESC_SSA],
            }
            for idx, row in df.iterrows()
        ]

    def setup_callbacks(self):
        """Configure all dashboard callbacks with enhanced features."""

        # Callback to handle user notes/commands input
        @self.app.callback(
            [
                Output("user-note-input", "value"),
                Output("user-history-display", "children", allow_duplicate=True)
            ],
            [Input("add-note-btn", "n_clicks")],
            [State("user-note-input", "value")],
            prevent_initial_call=True
        )
        def handle_user_note(n_clicks, note_text):
            """Handle user-entered notes - directly answers 'what I said'."""
            if n_clicks and note_text and note_text.strip():
                # Add user's own words to history
                self._add_to_history(f"Você disse: '{note_text.strip()}'", "user_input")
                return "", self._get_recent_history_html()
            return note_text or "", self._get_recent_history_html()

        # Callback to update user history display
        @self.app.callback(
            Output("user-history-display", "children"),
            [
                Input("resp-prog-filter", "value"),
                Input("resp-exec-filter", "value"),
                Input("setor-emissor-filter", "value"),
                Input("setor-executor-filter", "value"),
            ]
        )
        def update_history_display(resp_prog, resp_exec, setor_emissor, setor_executor):
            """Update the user history display when filters change."""
            # Log filter changes to history
            filters_applied = []
            if resp_prog:
                filters_applied.append(f"Responsável Prog.: {resp_prog}")
            if resp_exec:
                filters_applied.append(f"Responsável Exec.: {resp_exec}")
            if setor_emissor:
                filters_applied.append(f"Setor Emissor: {setor_emissor}")
            if setor_executor:
                filters_applied.append(f"Setor Executor: {setor_executor}")
            
            if filters_applied:
                self._add_to_history(f"Aplicou filtros: {', '.join(filters_applied)}", "filter")
            
            return self._get_recent_history_html()

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
            [
                Input("resp-prog-filter", "value"),
                Input("resp-exec-filter", "value"),
                Input("setor-emissor-filter", "value"),
                Input("setor-executor-filter", "value"),
            ],
        )
        def update_all_charts(resp_prog, resp_exec, setor_emissor, setor_executor):
            """Update all charts with filter data."""
            if any([resp_prog, resp_exec, setor_emissor, setor_executor]):
                self.logger.log_with_ip(
                    "INFO",
                    f"Filtros aplicados - Prog: {resp_prog}, Exec: {resp_exec}, "
                    f"Emissor: {setor_emissor}, Executor: {setor_executor}",
                )
                
                # Add to user history for better feedback
                filters_applied = []
                if resp_prog:
                    filters_applied.append(f"Resp. Prog: {resp_prog}")
                if resp_exec:
                    filters_applied.append(f"Resp. Exec: {resp_exec}")
                if setor_emissor:
                    filters_applied.append(f"Setor Emissor: {setor_emissor}")
                if setor_executor:
                    filters_applied.append(f"Setor Executor: {setor_executor}")
                
                if filters_applied:
                    self._add_to_history(f"Filtrou dados: {', '.join(filters_applied)}", "data_filter")

            df_filtered = self.df.copy()

            # Aplicar filtros
            if resp_prog:
                df_filtered = df_filtered[
                    df_filtered.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp_prog
                ]
            if resp_exec:
                df_filtered = df_filtered[
                    df_filtered.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp_exec
                ]
            if setor_emissor:
                df_filtered = df_filtered[
                    df_filtered.iloc[:, SSAColumns.SETOR_EMISSOR] == setor_emissor
                ]
            if setor_executor:
                df_filtered = df_filtered[
                    df_filtered.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor_executor
                ]

            # Criar visualizador filtrado
            filtered_visualizer = SSAVisualizer(df_filtered)

            # Criar os cards de resumo
            resp_cards = self._create_resp_summary_cards(df_filtered)

            # Gerar gráficos com informações de hover e click
            fig_prog = self._enhance_bar_chart(
                self._create_resp_prog_chart(df_filtered),
                "resp_prog",
                "SSAs por Programador",
                df_filtered,
            )

            fig_exec = self._enhance_bar_chart(
                self._create_resp_exec_chart(df_filtered),
                "resp_exec",
                "SSAs por Executor",
                df_filtered,
            )

            # Gráficos de semana com hover e click
            fig_programmed_week = self._enhance_bar_chart(
                filtered_visualizer.create_week_chart(use_programmed=True),
                "week_programmed",
                "SSAs Programadas",
                df_filtered,
            )

            fig_registration_week = self._enhance_bar_chart(
                filtered_visualizer.create_week_chart(use_programmed=False),
                "week_registration",
                "SSAs Cadastradas",
                df_filtered,
            )

            detail_style = (
                {"display": "block"}
                if any([resp_prog, resp_exec, setor_emissor, setor_executor])
                else {"display": "none"}
            )

            fig_detail_state = self._enhance_bar_chart(
                self._create_detail_state_chart(df_filtered),
                "state",
                "SSAs por Estado",
                df_filtered,
            )

            fig_detail_week = self._enhance_bar_chart(
                filtered_visualizer.create_week_chart(),
                "week_detail",
                "SSAs por Semana",
                df_filtered,
            )

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

        @self.app.callback(
            [
                Output("ssa-modal", "is_open"),
                Output("ssa-modal-body", "children"),
                Output("ssa-modal-title", "children"),
            ],
            [
                Input("weeks-in-state-chart", "clickData"),
                Input("resp-prog-chart", "clickData"),
                Input("resp-exec-chart", "clickData"),
                Input("programmed-week-chart", "clickData"),
                Input("registration-week-chart", "clickData"),
                Input("detail-state-chart", "clickData"),
                Input("detail-week-chart", "clickData"),
                Input("close-modal", "n_clicks"),
            ],
            [State("ssa-modal", "is_open")],
        )
        def toggle_modal(
            weeks_click,
            prog_click,
            exec_click,
            prog_week_click,
            reg_week_click,
            detail_state_click,
            detail_week_click,
            close_clicks,
            is_open,
        ):
            """Handle modal opening/closing and content."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return False, "", ""

            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if trigger_id == "close-modal":
                return False, "", ""

            try:
                click_mapping = {
                    "weeks-in-state-chart": (weeks_click, "SSAs no intervalo"),
                    "resp-prog-chart": (prog_click, "SSAs do programador"),
                    "resp-exec-chart": (exec_click, "SSAs do executor"),
                    "programmed-week-chart": (
                        prog_week_click,
                        "SSAs programadas na semana",
                    ),
                    "registration-week-chart": (
                        reg_week_click,
                        "SSAs cadastradas na semana",
                    ),
                    "detail-state-chart": (detail_state_click, "SSAs no estado"),
                    "detail-week-chart": (
                        detail_week_click,
                        "SSAs na semana (detalhe)",
                    ),
                }

                if trigger_id in click_mapping:
                    click_data, title_prefix = click_mapping[trigger_id]
                    if (
                        not click_data
                        or "points" not in click_data
                        or not click_data["points"]
                    ):
                        return False, "", ""

                    point_data = click_data["points"][0]
                    label = point_data.get("x", "")
                    ssas = point_data.get("customdata", [])

                    if isinstance(ssas, (list, tuple)):
                        ssas = [str(ssa).strip() for ssa in ssas if ssa]
                    else:
                        ssas = []

                    if ssas:
                        self.logger.log_with_ip(
                            "INFO", f"Visualização de SSAs: {title_prefix} {label}"
                        )

                    ssa_list = self._create_ssa_list(ssas)
                    title = f"{title_prefix} {label} ({len(ssas)} SSAs)"

                    return True, ssa_list, title

            except Exception as e:
                self.logger.log_with_ip("ERROR", f"Erro no modal: {str(e)}")
                return False, "", ""

            return False, "", ""

        # Callback para copiar SSAs
        self.app.clientside_callback(
            """
            function(n_clicks) {
                if (!n_clicks) return null;

                function copy(text) {
                    try {
                        if (navigator.clipboard && window.isSecureContext) {
                            return navigator.clipboard.writeText(text);
                        }
                    } catch (e) { /* ignore */ }
                    const ta = document.createElement('textarea');
                    ta.value = text || '';
                    ta.setAttribute('readonly', '');
                    ta.style.position = 'fixed';
                    ta.style.left = '-9999px';
                    document.body.appendChild(ta);
                    ta.focus();
                    ta.select();
                    try { document.execCommand('copy'); } catch (e) {}
                    document.body.removeChild(ta);
                    return Promise.resolve();
                }

                const el = document.getElementById('all-ssas-data');
                if (!el) return null;
                const allSSAs = (el.textContent || '').trim();
                return copy(allSSAs).then(function() {
                    const btn = document.getElementById('copy-all-ssas');
                    if (!btn) return true;
                    btn.textContent = 'Copiado!';
                    btn.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                        const count = allSSAs ? allSSAs.split(',').filter(Boolean).length : 0;
                        btn.textContent = `Copiar todas (${count})`;
                        btn.style.backgroundColor = '#f8f9fa';
                    }, 1500);
                    return true;
                });
            }
            """,
            Output("copy-all-ssas", "data-copied"),
            Input("copy-all-ssas", "n_clicks"),
        )

        self.app.clientside_callback(
            """
            function(n_clicks, id) {
                if (!n_clicks) return null;

                function copy(text) {
                    try {
                        if (navigator.clipboard && window.isSecureContext) {
                            return navigator.clipboard.writeText(text);
                        }
                    } catch (e) { /* ignore */ }
                    const ta = document.createElement('textarea');
                    ta.value = text || '';
                    ta.setAttribute('readonly', '');
                    ta.style.position = 'fixed';
                    ta.style.left = '-9999px';
                    document.body.appendChild(ta);
                    ta.focus();
                    ta.select();
                    try { document.execCommand('copy'); } catch (e) {}
                    document.body.removeChild(ta);
                    return Promise.resolve();
                }

                const domId = (typeof id === 'string') ? id : (id && id.type ? JSON.stringify(id) : null);
                if (!domId) return null;
                let button = document.getElementById(domId);
                if (!button && typeof id === 'object') {
                    // Fallback: try to find by data-dash-id when Dash rewrites IDs
                    const all = document.querySelectorAll('[data-dash-is-loading]');
                    for (let el of all) { if (el.id === domId) { button = el; break; } }
                }
                if (!button) return null;

                const ssa = button.title || button.getAttribute('title') || '';
                return copy(ssa).then(function() {
                    const originalText = button.textContent;
                    button.textContent = '✓';
                    button.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.backgroundColor = 'transparent';
                    }, 1500);
                    return true;
                });
            }
            """,
            Output({"type": "copy-button", "index": MATCH}, "data-copied"),
            Input({"type": "copy-button", "index": MATCH}, "n_clicks"),
            State({"type": "copy-button", "index": MATCH}, "id"),
        )

        # Callback para atualização automática
        @self.app.callback(
            Output("state-data", "data"), Input("interval-component", "n_intervals")
        )
        def update_data(n):
            """Update data periodically."""
            if n:  # Só atualiza após o primeiro intervalo
                self.logger.log_with_ip("INFO", "Atualização automática dos dados")
            return {}

    def _create_resp_summary_cards(self, df_filtered):
        """
        Creates summary cards for filtered dashboard data showing state distribution.

        Args:
            df_filtered (pd.DataFrame): Filtered DataFrame containing SSA data

        Returns:
            dbc.Row: Bootstrap row containing state summary cards
        """
        # Get state counts from filtered DataFrame
        state_counts = df_filtered.iloc[:, SSAColumns.SITUACAO].value_counts()
        total_count = len(df_filtered)

        # Calculate percentages
        def get_percentage(value):
            return (value / total_count * 100) if total_count > 0 else 0

        # Define royal blue color palette
        colors = {
            "primary": "#1e3799",  # Deep Royal Blue
            "secondary": "#4a69bd",  # Medium Royal Blue
            "info": "#6a89cc",  # Light Royal Blue
            "warning": "#4a69bd",  # Medium Royal Blue (for consistency)
            "danger": "#e55039",  # Soft Red for contrast
            "success": "#78e08f",  # Soft Green for contrast
        }

        # Define state cards with updated styling and order
        state_info = [
            ("TOTAL", total_count, "primary", "TOTAL DE SSAs"),
            ("APL", state_counts.get("APL", 0), "secondary", "AGUARDANDO PLANEJAMENTO"),
            ("APG", state_counts.get("APG", 0), "info", "AGUARDANDO PROGRAMAÇÃO"),
            (
                "AAD",
                state_counts.get("AAD", 0),
                "secondary",
                "AGUARDANDO ATUALIZAÇÃO DESENHOS",
            ),
            ("ADM", state_counts.get("ADM", 0), "info", "AGUARDANDO DEPTO. MANUTENÇÃO"),
            (
                "AAT",
                state_counts.get("AAT", 0),
                "secondary",
                "AGUARDANDO ATEND. TERCEIROS",
            ),
            ("APV", state_counts.get("APV", 0), "info", "AGUARDANDO PROVISIONAMENTO"),
            (
                "AIM",
                state_counts.get("AIM", 0),
                "secondary",
                "AGUARDANDO ENG. MANUTENÇÃO",
            ),
            (
                "SCD",
                state_counts.get("SCD", 0),
                "info",
                "SSA CANCELADA AG. APROV. DIV.",
            ),
            ("SEE", state_counts.get("SEE", 0), "success", "SERVIÇO EM EXECUÇÃO"),
            ("SAD", state_counts.get("SAD", 0), "success", "SERVIÇO A DISPOSIÇÃO"),
            ("ADI", state_counts.get("ADI", 0), "danger", "AGUARDANDO APROV. DIVISÃO"),
        ]

        # Create the state cards ribbon
        state_cards = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H6(
                                    "Estado:",
                                    className="me-2 mb-0",
                                    style={"color": colors["primary"]},
                                ),
                                html.H5(
                                    "Todos",
                                    className="mb-0",
                                    style={
                                        "fontWeight": "bold",
                                        "color": colors["primary"],
                                    },
                                ),
                            ],
                            className="d-flex align-items-center",
                        )
                    ],
                    width="auto",
                ),
            ]
            + [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    state,
                                                    className="mb-1",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "fontWeight": "bold",
                                                        "color": colors[color],
                                                        "lineHeight": "1.2",
                                                    },
                                                ),
                                                html.H3(
                                                    str(value),
                                                    className="mb-0",
                                                    style={
                                                        "fontWeight": "bold",
                                                        "color": colors[color],
                                                    },
                                                ),
                                                html.Small(
                                                    f"({get_percentage(value):.1f}%)",
                                                    style={"color": "#6c757d"},
                                                ),
                                            ],
                                            className="text-center",
                                        )
                                    ],
                                    className="p-2",
                                )
                            ],
                            className="mb-0",
                            style={
                                "width": "110px",
                                "height": "85px",
                                "borderLeft": f"4px solid {colors[color]}",
                                "backgroundColor": "#ffffff",
                                "boxShadow": "0 2px 4px rgba(30, 55, 153, 0.1)",
                                "borderRadius": "4px",
                            },
                        ),
                        dbc.Tooltip(
                            tooltip,
                            target=f"state-{state}",
                            placement="top",
                        ),
                    ],
                    width="auto",
                    id=f"state-{state}",
                )
                for state, value, color, tooltip in state_info
            ],
            className="mb-3 g-2 flex-nowrap align-items-center",
            style={
                "overflowX": "auto",
                "overflowY": "hidden",
                "paddingBottom": "18px",
                "marginBottom": "30px",
                "position": "sticky",
                "top": "0",
                "backgroundColor": "white",
                "zIndex": "1000",
                "boxShadow": "0 2px 4px rgba(30, 55, 153, 0.1)",
                "minHeight": "90px",
                "paddingTop": "10px",
                "borderRadius": "4px",
            },
        )

        return state_cards

    # Duplicate _get_chart_config removed (kept single definition above)

    def setup_layout(self):
        """
        Define o layout completo do dashboard.
        Remove o ribbon de estatísticas inicial e mantém apenas o ribbon de estados.
        Inclui todos os gráficos, tabelas e funcionalidades adicionais.
        """
        stats = self._get_initial_stats()
        state_counts = self._get_state_counts()

        self.app.layout = dbc.Container(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H1(
                                            "Dashboard de SSAs Pendentes",
                                            className="text-primary mb-0",
                                        ),
                                        html.Small(
                                            f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                            className="text-muted",
                                        ),
                                    ]
                                )
                            ],
                            width=8,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader([
                                            html.H6("Últimas Ações", className="mb-0"),
                                            html.Small("(O que você acabou de fazer)", className="text-muted")
                                        ]),
                                        dbc.CardBody([
                                            html.Div(id="user-history-display"),
                                            html.Hr(className="my-2"),
                                            html.Small("Adicionar nota:", className="text-muted"),
                                            dbc.InputGroup([
                                                dbc.Input(
                                                    id="user-note-input",
                                                    placeholder="Digite sua ação/nota...",
                                                    size="sm"
                                                ),
                                                dbc.Button(
                                                    "Adicionar",
                                                    id="add-note-btn",
                                                    size="sm",
                                                    color="primary"
                                                )
                                            ], size="sm")
                                        ], style={"max-height": "160px", "overflow-y": "auto"})
                                    ],
                                    className="small"
                                )
                            ],
                            width=4,
                        ),
                    ],
                    className="mb-4 pt-3",
                ),
                # Filtros expandidos
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Responsável Programação:", className="fw-bold"
                                ),
                                dcc.Dropdown(
                                    id="resp-prog-filter",
                                    options=[
                                        {"label": resp, "value": resp}
                                        for resp in self._get_responsaveis()[
                                            "programacao"
                                        ]
                                    ],
                                    placeholder="Selecione um responsável...",
                                    className="mb-2",
                                    clearable=True,
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                html.Label(
                                    "Responsável Execução:", className="fw-bold"
                                ),
                                dcc.Dropdown(
                                    id="resp-exec-filter",
                                    options=[
                                        {"label": resp, "value": resp}
                                        for resp in self._get_responsaveis()["execucao"]
                                    ],
                                    placeholder="Selecione um responsável...",
                                    className="mb-2",
                                    clearable=True,
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                html.Label("Setor Emissor:", className="fw-bold"),
                                dcc.Dropdown(
                                    id="setor-emissor-filter",
                                    options=[
                                        {"label": setor, "value": setor}
                                        for setor in sorted(
                                            self.df.iloc[
                                                :, SSAColumns.SETOR_EMISSOR
                                            ].unique()
                                        )
                                    ],
                                    placeholder="Selecione um setor emissor...",
                                    className="mb-2",
                                    clearable=True,
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                html.Label("Setor Executor:", className="fw-bold"),
                                dcc.Dropdown(
                                    id="setor-executor-filter",
                                    options=[
                                        {"label": setor, "value": setor}
                                        for setor in sorted(
                                            self.df.iloc[
                                                :, SSAColumns.SETOR_EXECUTOR
                                            ].unique()
                                        )
                                    ],
                                    placeholder="Selecione um setor executor...",
                                    className="mb-2",
                                    clearable=True,
                                ),
                            ],
                            width=3,
                        ),
                    ],
                    className="mb-3",
                    style={
                        "position": "relative",
                        "zIndex": "1001",
                        "backgroundColor": "white",
                        "padding": "10px 0",
                    },
                ),
                # Cards de resumo do usuário (apenas ribbon de estados)
                dbc.Row(
                    [dbc.Col([html.Div(id="resp-summary-cards")], width=12)],
                    className="mb-4",
                ),
                # Gráficos principais
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "SSAs por Responsável na Programação",
                                            className="fw-bold bg-light",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(
                                                    dcc.Graph(
                                                        id="resp-prog-chart",
                                                        config=self._chart_config(),
                                                    ),
                                                    color="primary",
                                                )
                                            ]
                                        ),
                                    ],
                                    className="h-100 shadow-sm",
                                )
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "SSAs por Responsável na Execução",
                                            className="fw-bold bg-light",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(
                                                    dcc.Graph(
                                                        id="resp-exec-chart",
                                                        config=self._chart_config(),
                                                    ),
                                                    color="primary",
                                                )
                                            ]
                                        ),
                                    ],
                                    className="h-100 shadow-sm",
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
                                        dbc.CardHeader(
                                            "SSAs Programadas por Semana",
                                            className="fw-bold bg-light",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(
                                                    dcc.Graph(
                                                        id="programmed-week-chart",
                                                        config=self._chart_config(),
                                                    ),
                                                    color="primary",
                                                )
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                )
                            ],
                            width=12,
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "SSAs por Semana de Cadastro",
                                            className="fw-bold bg-light",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(
                                                    dcc.Graph(
                                                        id="registration-week-chart",
                                                        config=self._chart_config(),
                                                    ),
                                                    color="primary",
                                                )
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                )
                            ],
                            width=12,
                        ),
                    ],
                    className="mb-4",
                ),
                # Gráfico de tempo no estado
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "Tempo no Estado Atual",
                                            className="fw-bold bg-light",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(
                                                    dcc.Graph(
                                                        id="weeks-in-state-chart",
                                                        config=self._chart_config(),
                                                    ),
                                                    color="primary",
                                                )
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                )
                            ],
                            width=12,
                        ),
                    ],
                    className="mb-4",
                ),
                # Seção de detalhamento
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H4(
                                            "Detalhamento por Responsável",
                                            className="mb-3 fw-bold text-primary",
                                        )
                                    ],
                                    width=12,
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    "SSAs Pendentes por Estado",
                                                    className="fw-bold bg-light",
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        dbc.Spinner(
                                                            dcc.Graph(
                                                                id="detail-state-chart",
                                                                config=self._chart_config(),
                                                            ),
                                                            color="primary",
                                                        )
                                                    ]
                                                ),
                                            ],
                                            className="shadow-sm",
                                        )
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    "SSAs por Semana (Detalhado)",
                                                    className="fw-bold bg-light",
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        dbc.Spinner(
                                                            dcc.Graph(
                                                                id="detail-week-chart",
                                                                config=self._chart_config(),
                                                            ),
                                                            color="primary",
                                                        )
                                                    ]
                                                ),
                                            ],
                                            className="shadow-sm",
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
                # Tabela de SSAs com larguras ajustadas
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "Lista de SSAs",
                                                            className="fw-bold",
                                                        ),
                                                        html.Small(
                                                            " (Clique nas colunas para ordenar)",
                                                            className="text-muted ms-2",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="bg-light",
                                        ),
                                        dbc.CardBody(
                                            [
                                                dash_table.DataTable(
                                                    id="ssa-table",
                                                    columns=[
                                                        {
                                                            "name": "SSA",
                                                            "id": "numero",
                                                            "presentation": "markdown",
                                                        },
                                                        {
                                                            "name": "Estado",
                                                            "id": "estado",
                                                        },
                                                        {
                                                            "name": "Emissor",
                                                            "id": "setor_emissor",
                                                        },
                                                        {
                                                            "name": "Executor",
                                                            "id": "setor_executor",
                                                        },
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
                                                        {
                                                            "name": "Data Emissão",
                                                            "id": "data_emissao",
                                                        },
                                                        {
                                                            "name": "Descrição",
                                                            "id": "descricao",
                                                        },
                                                    ],
                                                    style_table={
                                                        "overflowX": "auto",
                                                        "minWidth": "100%",
                                                        "marginBottom": "20px",
                                                    },
                                                    style_cell={
                                                        "textAlign": "left",
                                                        "padding": "5px",
                                                        "whiteSpace": "normal",
                                                        "height": "auto",
                                                        "fontSize": "11px",
                                                        "fontFamily": "Arial",
                                                        "lineHeight": "12px",
                                                        "minWidth": "0px",
                                                        "maxWidth": "500px",
                                                    },
                                                    style_cell_conditional=cast(Any, [
                                                        {
                                                            "if": {
                                                                "column_id": "numero"
                                                            },
                                                            "width": "70px",
                                                            "maxWidth": "70px",
                                                            "minWidth": "70px",
                                                        },
                                                        # ... (rest of style_cell_conditional remains the same)
                                                    ]),
                                                    style_header={
                                                        "backgroundColor": "rgb(230, 230, 230)",
                                                        "fontWeight": "bold",
                                                        "textAlign": "left",
                                                        "padding": "2px",
                                                        "whiteSpace": "normal",
                                                        "height": "auto",
                                                        "fontSize": "11px",
                                                        "fontFamily": "Arial",
                                                    },
                                                    style_data={
                                                        "whiteSpace": "normal",
                                                        "height": "auto",
                                                        "lineHeight": "12px",
                                                        "padding": "5px",
                                                    },
                                                    page_size=30,
                                                    page_current=0,
                                                    sort_action="native",
                                                    sort_mode="multi",
                                                    filter_action="native",
                                                    tooltip_data=[],
                                                    tooltip_duration=None,
                                                    style_as_list_view=True,
                                                )
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
                # Modal para exibição
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            [dbc.ModalTitle(id="ssa-modal-title")],
                            close_button=True,
                        ),
                        dbc.ModalBody([html.Div(id="ssa-modal-body")]),
                        dbc.ModalFooter(
                            [
                                html.Small(
                                    "Clique nas SSAs para copiar",
                                    className="text-muted me-auto",
                                ),
                                dbc.Button(
                                    "Fechar",
                                    id="close-modal",
                                    className="ms-auto",
                                    color="secondary",
                                ),
                            ]
                        ),
                    ],
                    id="ssa-modal",
                    size="lg",
                    is_open=False,
                ),
                # Store para dados de estado
                dcc.Store(id="state-data"),
                # Intervalo para atualização automática
                dcc.Interval(
                    id="interval-component",
                    interval=5 * 60 * 1000,  # 5 minutos em milissegundos
                    n_intervals=0,
                ),
                # Footer
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Hr(),
                                html.Small(
                                    f"© {datetime.now().year} Dashboard SSAs - Versão 1.0",
                                    className="text-muted",
                                ),
                            ],
                            width=12,
                            className="text-center py-3",
                        )
                    ]
                ),
            ],
            fluid=True,
            className="p-4",
        )

    def _create_empty_chart(self, title: str) -> go.Figure:
        """
        Creates an empty chart with an error message.

        Args:
            title (str): Chart title

        Returns:
            go.Figure: Empty Plotly figure with error message
        """
        return go.Figure().update_layout(
            title=title,
            xaxis_title="",
            yaxis_title="",
            template="plotly_white",
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
