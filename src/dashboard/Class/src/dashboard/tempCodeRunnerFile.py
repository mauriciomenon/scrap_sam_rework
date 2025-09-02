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
                                html.Label("Responsável Programação:", className="fw-bold"),
                                dcc.Dropdown(
                                    id="resp-prog-filter",
                                    options=[
                                        {"label": resp, "value": resp}
                                        for resp in self._get_responsaveis()["programacao"]
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
                                html.Label("Responsável Execução:", className="fw-bold"),
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
                                                        config=self._get_chart_config(),
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
                                                        config=self._get_chart_config(),
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
                                                        config=self._get_chart_config(),
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
                                           