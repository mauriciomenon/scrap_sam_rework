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
try:
    from .ssa_visualizer import SSAVisualizer  # type: ignore[reportMissingImports]
    from .kpi_calculator import KPICalculator  # type: ignore[reportMissingImports]
    from ..data.ssa_columns import SSAColumns  # type: ignore[reportMissingImports]
    from ..utils.log_manager import LogManager  # type: ignore[reportMissingImports]
except Exception:
    import os, sys
    # Robust fallback: walk up to repo root (with pyproject.toml) then add main src path
    _this_dir = os.path.dirname(__file__)
    _repo_root = None
    _cursor = _this_dir
    for _ in range(8):  # walk up a few levels safely
        if os.path.isfile(os.path.join(_cursor, "pyproject.toml")):
            _repo_root = _cursor
            break
        _parent = os.path.dirname(_cursor)
        if _parent == _cursor:
            break
        _cursor = _parent
    if _repo_root is None:
        # heuristic: from bkp/.../dashboard directory to repo root
        _repo_root = os.path.abspath(os.path.join(_this_dir, "../../../../.."))
    # Add repo root so 'src' becomes a top-level package
    if _repo_root not in sys.path:
        sys.path.append(_repo_root)
    from src.dashboard.Class.src.dashboard.ssa_visualizer import SSAVisualizer  # type: ignore
    from src.dashboard.Class.src.dashboard.kpi_calculator import KPICalculator  # type: ignore
    from src.dashboard.Class.src.data.ssa_columns import SSAColumns  # type: ignore
    from src.dashboard.Class.src.utils.log_manager import LogManager  # type: ignore

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

        # Configurar servidor Flask subjacente
        server = self.app.server

        # Adicionar middleware para logging
        @server.before_request
        def log_request_info():
            self.logger.log_with_ip("INFO", f"Acesso à rota: {request.path}")

        self.visualizer = SSAVisualizer(df)
        self.kpi_calc = KPICalculator(df)
        self.week_analyzer = self.visualizer.week_analyzer
        self.setup_layout()
        self.setup_callbacks()

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
                "por_prioridade": pd.Series(),
                "por_setor": pd.Series(),
                "por_estado": pd.Series(),
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
        """Retorna configuração padrão para todos os gráficos."""
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
        }

    def run_server(self, debug: bool = True, port: int = 8080, host: str = "0.0.0.0"):
        """Inicia o servidor do dashboard com compatibilidade entre versões do Dash."""
        self.logger.log_with_ip("INFO", "Iniciando servidor do dashboard")
        try:
            run = getattr(self.app, "run", None)
            if callable(run):
                self.app.run(debug=debug, port=port, host=host)
            else:
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
        """Enhances bar chart with hover info and clickable data without in-place y mutations."""
        df_to_use = df_filtered if df_filtered is not None else self.df

        try:
            for trace in fig.data:
                if isinstance(trace, go.Bar):
                    hover_text = []
                    customdata = []
                    new_y = []

                    for cat in list(getattr(trace, "x", []) or []):
                        mask = None
                        if chart_type == "resp_prog":
                            mask = (
                                df_to_use.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == cat
                            )
                        elif chart_type == "resp_exec":
                            mask = df_to_use.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == cat
                        elif chart_type == "state":
                            mask = df_to_use.iloc[:, SSAColumns.SITUACAO] == cat
                        elif chart_type == "week_programmed":
                            mask = df_to_use.iloc[:, SSAColumns.SEMANA_PROGRAMADA] == str(
                                cat
                            )
                            if (
                                trace.name
                            ):  # Se tem nome, é um gráfico empilhado por prioridade
                                mask = mask & (
                                    df_to_use.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                                    == trace.name
                                )
                        elif chart_type == "week_registration":
                            mask = df_to_use.iloc[:, SSAColumns.SEMANA_CADASTRO] == str(cat)
                            if trace.name:
                                mask = mask & (
                                    df_to_use.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                                    == trace.name
                                )
                        else:
                            continue

                        ssas = df_to_use[mask].iloc[:, SSAColumns.NUMERO_SSA].tolist() if mask is not None else []

                        # Texto do hover
                        ssa_preview = "<br>".join(ssas[:5])
                        if len(ssas) > 5:
                            ssa_preview += f"<br>... (+{len(ssas)-5} SSAs)"

                        title_text = str(cat)
                        if trace.name:
                            title_text += f" - {trace.name}"

                        hover_text.append(
                            f"<b>{title_text}</b><br>"
                            f"Total SSAs: {len(ssas)}<br>"
                            f"SSAs:<br>{ssa_preview}"
                        )
                        customdata.append(ssas)
                        new_y.append(len(ssas))

                    trace.update(
                        text=new_y if new_y else trace.y,
                        hovertext=hover_text,
                        hoverinfo="text",
                        customdata=customdata,
                        textposition="auto",
                        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                        y=new_y if new_y else trace.y,
                    )

            fig.update_layout(
                dragmode="pan",
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                modebar=dict(remove=["scrollZoom", "autoScale2d"]),
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True),
            )

        except Exception as e:
            logging.error(f"Erro ao melhorar gráfico: {str(e)}")
            return fig

        return fig

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
            title="SSAs por Responsável na Programação",
            xaxis_title="Responsável",
            yaxis_title="Quantidade",
            template="plotly_white",
            showlegend=False,
            xaxis={"tickangle": -45},
            margin={"l": 50, "r": 20, "t": 50, "b": 100},
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
                textposition="auto",
            )
        ])

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

            df_filtered = self.df.copy()

            # Aplicar filtros
            if resp_prog:
                df_filtered = df_filtered[df_filtered.iloc[:, SSAColumns.RESPONSAVEL_PROGRAMACAO] == resp_prog]
            if resp_exec:
                df_filtered = df_filtered[df_filtered.iloc[:, SSAColumns.RESPONSAVEL_EXECUCAO] == resp_exec]
            if setor_emissor:
                df_filtered = df_filtered[df_filtered.iloc[:, SSAColumns.SETOR_EMISSOR] == setor_emissor]
            if setor_executor:
                df_filtered = df_filtered[df_filtered.iloc[:, SSAColumns.SETOR_EXECUTOR] == setor_executor]

            # Criar visualizador filtrado
            filtered_visualizer = SSAVisualizer(df_filtered)

            # Criar os cards de resumo
            resp_cards = self._create_resp_summary_cards(df_filtered)

            # Gerar gráficos com informações de hover e click
            fig_prog = self._enhance_bar_chart(
                self._create_resp_prog_chart(df_filtered),
                "resp_prog",
                "SSAs por Programador",
                df_filtered
            )

            fig_exec = self._enhance_bar_chart(
                self._create_resp_exec_chart(df_filtered),
                "resp_exec", 
                "SSAs por Executor",
                df_filtered
            )

            # Gráficos de semana com hover e click
            fig_programmed_week = self._enhance_bar_chart(
                filtered_visualizer.create_week_chart(use_programmed=True),
                "week_programmed",
                "SSAs Programadas",
                df_filtered
            )

            fig_registration_week = self._enhance_bar_chart(
                filtered_visualizer.create_week_chart(use_programmed=False),
                "week_registration",
                "SSAs Cadastradas",
                df_filtered
            )

            detail_style = {"display": "block"} if any([resp_prog, resp_exec, setor_emissor, setor_executor]) else {"display": "none"}

            fig_detail_state = self._enhance_bar_chart(
                self._create_detail_state_chart(df_filtered),
                "state",
                "SSAs por Estado",
                df_filtered
            )

            fig_detail_week = self._enhance_bar_chart(
                filtered_visualizer.create_week_chart(),
                "week_detail",
                "SSAs por Semana",
                df_filtered
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
                    "programmed-week-chart": (prog_week_click, "SSAs programadas na semana"),
                    "registration-week-chart": (reg_week_click, "SSAs cadastradas na semana"),
                    "detail-state-chart": (detail_state_click, "SSAs no estado"),
                    "detail-week-chart": (detail_week_click, "SSAs na semana (detalhe)")
                }

                if trigger_id in click_mapping:
                    click_data, title_prefix = click_mapping[trigger_id]
                    if not click_data or "points" not in click_data or not click_data["points"]:
                        return False, "", ""

                    point_data = click_data["points"][0]
                    label = point_data.get("x", "")
                    ssas = point_data.get("customdata", [])

                    if isinstance(ssas, (list, tuple)):
                        ssas = [str(ssa).strip() for ssa in ssas if ssa]
                    else:
                        ssas = []

                    if ssas:
                        self.logger.log_with_ip("INFO", f"Visualização de SSAs: {title_prefix} {label}")

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
                    if (navigator.clipboard && window.isSecureContext) {
                        return navigator.clipboard.writeText(text);
                    } else {
                        const ta = document.createElement('textarea');
                        ta.value = text;
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
                }

                const el = document.getElementById('all-ssas-data');
                if (!el) return null;
                const allSSAs = (el.textContent || '').trim();
                copy(allSSAs).then(function() {
                    const btn = document.getElementById('copy-all-ssas');
                    if (!btn) return;
                    btn.textContent = 'Copiado!';
                    btn.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                        const count = allSSAs ? allSSAs.split(',').length : 0;
                        btn.textContent = `Copiar todas (${count})`;
                        btn.style.backgroundColor = '#f8f9fa';
                    }, 1500);
                });
                return true;
            }
            """,
            Output("copy-all-ssas", "data-copied"),
            Input("copy-all-ssas", "n_clicks")
        )

        self.app.clientside_callback(
            """
            function(n_clicks, id) {
                if (!n_clicks) return null;

                function copy(text) {
                    if (navigator.clipboard && window.isSecureContext) {
                        return navigator.clipboard.writeText(text);
                    } else {
                        const ta = document.createElement('textarea');
                        ta.value = text;
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
                }

                const domId = (typeof id === 'string') ? id : JSON.stringify(id);
                const button = document.getElementById(domId);
                if (!button) return null;
                const ssa = button.title || button.getAttribute('title') || '';
                copy(ssa).then(function() {
                    const originalText = button.textContent;
                    button.textContent = '✓';
                    button.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.backgroundColor = 'transparent';
                    }, 1500);
                });
                
                return true;
            }
            """,
            Output({"type": "copy-button", "index": MATCH}, "data-copied"),
            Input({"type": "copy-button", "index": MATCH}, "n_clicks"),
            State({"type": "copy-button", "index": MATCH}, "id")
        )

        # Callback para atualização automática
        @self.app.callback(
            Output("state-data", "data"),
            Input("interval-component", "n_intervals")
        )
        def update_data(n):
            """Update data periodically."""
            if n:  # Só atualiza após o primeiro intervalo
                self.logger.log_with_ip("INFO", "Atualização automática dos dados")
            return {}

    def _create_resp_summary_cards(self, df_filtered):
        """Cria cards de resumo para o usuário filtrado."""
        # Obtém estatísticas do DataFrame filtrado
        state_counts = df_filtered.iloc[:, SSAColumns.SITUACAO].value_counts()
        total_count = len(df_filtered)

        # Obtém prioridades do DataFrame filtrado
        priority_counts = df_filtered.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].value_counts()

        # Cabeçalho fixo mostrando "Todos"
        cards = [
            dbc.Col(
                html.Div([
                    html.H6("Estado:", className="me-2 mb-0"),
                    html.H5(
                        "Todos",
                        className="text-primary mb-0",
                        style={"fontWeight": "bold"},
                    ),
                ], className="d-flex align-items-center"),
                width="auto",
            ),
            # Card de Total
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div(
                                "TOTAL",
                                className="text-muted mb-1",
                                style={"fontSize": "0.8rem", "fontWeight": "bold"},
                            ),
                            html.H3(
                                str(total_count),
                                className="text-danger mb-0",
                                style={"fontWeight": "bold"},
                            ),
                        ], className="text-center")
                    ], className="p-2")
                ], className="mb-0 border-danger",
                style={"width": "120px", "height": "65px", "borderLeft": "4px solid"}),
                width="auto",
            ),
        ]

        state_info = [
            ("APL", "#fd7e14", "APL - AGUARDANDO PLANEJAMENTO"),
            ("APG", "#fd7e14", "APG - AGUARDANDO PROGRAMAÇÃO"),
            ("AAD", "#007bff", "AAD - AGUARDANDO ATUALIZAÇÃO DE DESENHOS"),
            ("ADM", "#007bff", "ADM - AGUARDANDO DEPARTAMENTO DE MANUTENÇÃO"),
            ("AAT", "#007bff", "AAT - AGAURDANDO ATENDIMENTO DE TERCEIROS"),
            ("APV", "#007bff", "APV - AGUARDANDO PROVISIONAMENTO"),
            ("AIM", "#007bff", "AIM - AGUARDANDO ENGENHARIA DE MANUTENÇÃO"),
            ("SCD", "#6c757d", "SCD - SSA CANCELADA AGUARDANDO APROV. DIVISÃO"),
            ("ADI", "#dc3545", "ADI - AGUARDANDO APROVAÇÃO DA DIVISÃO NA EMISSÃO"),
            
        ]

        # Cola de cores: "#007bff", "#28a745", "#dc3545", "#ffc107", "#17a2b8", "#6610f2", "#fd7e14", "#20c997", "#e83e8c", "#6c757d",

        # Cards para cada estado
        for state, color, description in state_info:
            count = state_counts.get(state, 0)
            percentage = (count / total_count * 100) if total_count > 0 else 0

            cards.append(
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.Span(
                                        state,
                                        className="fw-bold",
                                        style={"fontSize": "0.9rem"},
                                    ),
                                    dbc.Tooltip(
                                        description,
                                        target=f"state-{state}",
                                        placement="top",
                                    ),
                                ], id=f"state-{state}"),
                                html.Div([
                                    html.H4(
                                        str(count),
                                        className="mb-0 fw-bold",
                                        style={"color": color},
                                    ),
                                    html.Small(
                                        f"({percentage:.1f}%)",
                                        className="text-muted",
                                    ),
                                ])
                            ], className="text-center")
                        ], className="p-2")
                    ], className="mb-0",
                    style={
                        "width": "120px",
                        "height": "65px",
                        "borderLeft": f"4px solid {color}",
                    }),
                    width="auto",
                )
            )

        # Adiciona card de prioridades críticas se houver
        if "S3.7" in priority_counts:
            critical_count = priority_counts["S3.7"]
            critical_percentage = (critical_count / total_count * 100) if total_count > 0 else 0

            cards.append(
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div(
                                    "CRÍTICAS",
                                    className="text-muted mb-1",
                                    style={"fontSize": "0.8rem", "fontWeight": "bold"},
                                ),
                                html.H4(
                                    str(critical_count),
                                    className="mb-0 fw-bold text-warning",
                                ),
                                html.Small(
                                    f"({critical_percentage:.1f}%)",
                                    className="text-muted",
                                ),
                            ], className="text-center")
                        ], className="p-2")
                    ], className="mb-0",
                    style={
                        "width": "120px",
                        "height": "65px",
                        "borderLeft": "4px solid #ffc107",
                    }),
                    width="auto",
                )
            )

        # Retorna row com todos os cards em um container com scroll horizontal
        return dbc.Row(
            cards,
            className="mb-3 g-2 flex-nowrap align-items-center",
            style={
                "overflowX": "auto",
                "overflowY": "hidden",
                "paddingBottom": "18px",  # aumenta o espaço abaixo dos cards
                "marginBottom": "30px",  # adiciona margem após a seção dos cards
                "position": "sticky",
                "top": "0",
                "backgroundColor": "white",
                "zIndex": "1000",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "minHeight": "90px",  # Adicionado altura mínima
                "paddingTop": "10px",  # Adicionado padding top
            },
        )

    def setup_layout(self):
        """Define o layout completo do dashboard."""
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
                            width=12,
                        ),
                    ],
                    className="mb-4 pt-3",
                ),
                # Linha com estatísticas gerais
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "Total de SSAs",
                                                    className="text-muted mb-2",
                                                ),
                                                html.H3(
                                                    f"{stats['total']:,}",
                                                    className="text-primary mb-0",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "SSAs Críticas (S3.7)",
                                                    className="text-muted mb-2",
                                                ),
                                                html.H3(
                                                    f"{stats['criticas']:,}",
                                                    className="text-warning mb-0",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "Setores Envolvidos",
                                                    className="text-muted mb-2",
                                                ),
                                                html.H3(
                                                    f"{len(stats['por_setor']):,}",
                                                    className="text-success mb-0",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "Estados Ativos",
                                                    className="text-muted mb-2",
                                                ),
                                                html.H3(
                                                    f"{len(stats['por_estado']):,}",
                                                    className="text-info mb-0",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width=3,
                        ),
                    ],
                    className="mb-4",
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
                # Cards de resumo do usuário
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
                                                        config=cast(Any, self._get_chart_config()),
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
                                                        config=cast(Any, self._get_chart_config()),
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
                                                        config=cast(Any, self._get_chart_config()),
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
                                                        config=cast(Any, self._get_chart_config()),
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
                                                        config=cast(Any, self._get_chart_config()),
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
                                                                config=cast(Any, self._get_chart_config()),
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
                                                                config=cast(Any, self._get_chart_config()),
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
                                                        "overflowX": "auto",  # Scroll horizontal
                                                        "minWidth": "100%",  # Largura mínima
                                                        "marginBottom": "20px",  # Margem inferior
                                                    },
                                                    style_cell={
                                                        "textAlign": "left",
                                                        "padding": "5px",
                                                        "whiteSpace": "normal",
                                                        "height": "auto",  # Altura automática
                                                        "fontSize": "11px",  # Tamanho geral da fonte para células
                                                        "fontFamily": "Arial",  # Tipo da fonte
                                                        "lineHeight": "12px",  # Espaçamento entre linhas
                                                        "minWidth": "0px",  # Importante para permitir compressão, Largura mínima
                                                        "maxWidth": "500px",  # Limite máximo geral
                                                    },
                                                    style_cell_conditional=cast(Any, [
                                                        {
                                                            "if": {
                                                                "column_id": "numero"
                                                            },
                                                            "width": "70px",
                                                            "verticalAlign": "middle",
                                                            "maxWidth": "70px",
                                                            "minWidth": "70px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "estado"
                                                            },
                                                            "width": "50px",
                                                            "maxWidth": "50px",
                                                            "minWidth": "50px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "setor_emissor"
                                                            },
                                                            "width": "50px",
                                                            "maxWidth": "50px",
                                                            "minWidth": "50px",
                                                        },
                                                        {  #
                                                            "if": {
                                                                "column_id": "setor_executor"
                                                            },
                                                            "width": "70px",
                                                            "maxWidth": "70px",
                                                            "minWidth": "70px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "resp_prog"
                                                            },
                                                            "width": "140px",
                                                            "maxWidth": "140px",
                                                            "minWidth": "140px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "resp_exec"
                                                            },
                                                            "width": "140px",
                                                            "maxWidth": "140px",
                                                            "minWidth": "140px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "semana_prog"
                                                            },
                                                            "width": "60px",
                                                            "maxWidth": "60px",
                                                            "minWidth": "60px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "prioridade"
                                                            },
                                                            "width": "100px",
                                                            "maxWidth": "100px",
                                                            "minWidth": "100px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "data_emissao"
                                                            },
                                                            "width": "120px",
                                                            "maxWidth": "120px",
                                                            "minWidth": "120px",
                                                        },
                                                        {
                                                            "if": {
                                                                "column_id": "descricao"
                                                            },
                                                            "minWidth": "300px",
                                                            "width": "auto",
                                                            "flex": "1",
                                                        },
                                                    ]),
                                                    style_header={  # cabecalho da tabela
                                                        "backgroundColor": "rgb(230, 230, 230)",
                                                        "fontWeight": "bold",
                                                        "textAlign": "left",
                                                        "padding": "2px",
                                                        "whiteSpace": "normal",  # Permite quebra de linha no cabeçalho
                                                        "height": "auto",  # Altura automática para cabeçalhos
                                                        "fontSize": "11px",  # Tamanho da fonte para cabeçalhos
                                                        "fontFamily": "Arial",
                                                    },
                                                    style_data={
                                                        "whiteSpace": "normal",  # Permite quebra de linha
                                                        "height": "auto",  # Altura automática
                                                        "lineHeight": "12px",  # Espaçamento entre linhas
                                                        "padding": "5px",  # Espaçamento interno
                                                    },
                                                    style_header_conditional=cast(Any, [  # Aplica os mesmos tamanhos aos cabeçalhos
                                                        {
                                                            "if": {
                                                                "column_id": col["id"]
                                                            },
                                                            "width": width["width"],
                                                        }
                                                        for col, width in zip(
                                                            [
                                                                {"id": "numero"},
                                                                {"id": "estado"},
                                                                {"id": "setor_emissor"},
                                                                {
                                                                    "id": "setor_executor"
                                                                },
                                                                {"id": "resp_prog"},
                                                                {"id": "resp_exec"},
                                                                {"id": "semana_prog"},
                                                                {"id": "prioridade"},
                                                                {"id": "data_emissao"},
                                                                {"id": "descricao"},
                                                            ],
                                                            [
                                                                {"width": "80px"},
                                                                {"width": "90px"},
                                                                {"width": "120px"},
                                                                {"width": "120px"},
                                                                {"width": "120px"},
                                                                {"width": "120px"},
                                                                {"width": "110px"},
                                                                {"width": "100px"},
                                                                {"width": "120px"},
                                                                {"width": "auto"},
                                                            ],
                                                        )
                                                    ]),
                                                    style_data_conditional=cast(Any, [
                                                        {
                                                            "if": {"row_index": "odd"},
                                                            "backgroundColor": "rgb(248, 248, 248)",
                                                        },
                                                        {  # Prioridades
                                                            "if": {
                                                                "filter_query": "{prioridade} eq 'S3.7'"
                                                            },
                                                            "backgroundColor": "#fff3cd",
                                                            "color": "#856404",
                                                        },
                                                    ]),
                                                    page_size=30,  # default 10
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
                # Resumo de estilos da tabela:
                # Para reduzir altura: diminua lineHeight e padding
                # Para fontes menores: reduza fontSize
                # Para colunas mais estreitas: diminua width, maxWidth e minWidth
                # Para mais espaço: aumente padding
                # Para cabeçalhos menores: reduza padding no style_header
                # Para uma tabela mais compacta:
                # style_cell={"fontSize": "10px", "padding": "4px", "lineHeight": "12px"}
                # Ou para uma mais espaçada:
                # style_cell={"fontSize": "13px", "padding": "10px", "lineHeight": "18px"}
                # Modal para exibição das SSAs
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            [dbc.ModalTitle(id="ssa-modal-title")], close_button=True
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
        """Creates an empty chart with a title when no data is available."""
        return go.Figure().update_layout(
            title=title,
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
