import dash_bootstrap_components as dbc
from dash import dcc, html


def create_layout(lista_ativos):
    """Cria o layout da aplicação com base na lista de ativos disponíveis."""

    acoes_disponiveis = [{"label": t, "value": t} for t in lista_ativos]

    badges_layout = []
    if lista_ativos:
        for ticker in lista_ativos:
            badges_layout.append(
                dbc.Badge(
                    ticker,
                    id={"type": "asset-badge", "index": ticker},
                    n_clicks=0,
                    color="success" if ticker != "IBOV" else "primary",
                    className="me-2 mb-2 p-2",
                    style={"cursor": "pointer", "userSelect": "none"},
                )
            )
    else:
        badges_layout = [
            html.P("Nenhum ativo carregado. Verifique a API.", className="text-danger")
        ]

    layout = dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.H2(
                        [
                            html.I(className="bi bi-graph-up me-2"),
                            "Simulador de Portfólio Interativo (B3)",
                        ]
                    ),
                    width=12,
                    className="text-center my-4",
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.I(className="bi bi-archive-fill me-2"),
                                    "Ativos Disponíveis (Clique para detalhes)",
                                ]
                            ),
                            dbc.CardBody(
                                [
                                    html.P(
                                        "Clique em um ativo para ver sua evolução individual:",
                                        className="text-muted small mb-2",
                                    ),
                                    html.Div(badges_layout),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    width=12,
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.I(className="bi bi-gear-fill me-2"),
                                    "Configurações da Simulação",
                                ]
                            ),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        className="g-3",
                                        children=[
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Selecione os Ativos:",
                                                        className="form-label fw-bold",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="stock-selector",
                                                        options=acoes_disponiveis,
                                                        value=(
                                                            ["IBOV"]
                                                            if "IBOV" in lista_ativos
                                                            else []
                                                        ),
                                                        multi=True,
                                                        placeholder="Escolha ações para compor a carteira...",
                                                    ),
                                                ],
                                                md=5,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Pesos (separados por vírgula):",
                                                        className="form-label fw-bold",
                                                    ),
                                                    dcc.Input(
                                                        id="weight-inputs",
                                                        type="text",
                                                        value="1.0",
                                                        placeholder="Ex: 0.5, 0.5",
                                                        className="form-control",
                                                    ),
                                                    dbc.FormText(
                                                        "A soma deve ser 1.0 (100%)"
                                                    ),
                                                ],
                                                md=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Aporte Inicial (R$):",
                                                        className="form-label fw-bold",
                                                    ),
                                                    dcc.Input(
                                                        id="aporte-input",
                                                        type="number",
                                                        value=1000,
                                                        min=1,
                                                        className="form-control",
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                        ],
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                dbc.Button(
                                                    [
                                                        html.I(
                                                            className="bi bi-play-circle me-2"
                                                        ),
                                                        "Simular Carteira",
                                                    ],
                                                    id="run-button",
                                                    n_clicks=0,
                                                    color="primary",
                                                    className="w-100 mt-4 fw-bold",
                                                ),
                                                html.Div(
                                                    id="error-message",
                                                    className="text-danger mt-3 text-center fw-bold",
                                                ),
                                            ],
                                            width=12,
                                        )
                                    ),
                                ]
                            ),
                        ]
                    ),
                    width=12,
                )
            ),
            dbc.Row(
                dbc.Col(
                    html.Div(
                        id="results-container",
                        style={"display": "none"},
                        children=[
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(
                                                className="bi bi-bar-chart-line-fill me-2"
                                            ),
                                            "Resultados da Simulação",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                id="metrics-output",
                                                className="mb-4 g-3",
                                            ),
                                            dbc.Row(
                                                dbc.Col(
                                                    dcc.Loading(
                                                        id="loading-graph",
                                                        type="dot",
                                                        children=dcc.Graph(
                                                            id="portfolio-graph",
                                                            config={"responsive": True},
                                                        ),
                                                    ),
                                                    width=12,
                                                )
                                            ),
                                        ]
                                    ),
                                ],
                                className="mt-4 shadow-sm",
                            )
                        ],
                    ),
                    width=12,
                )
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                    dbc.ModalBody(
                        dcc.Loading(
                            id="loading-modal",
                            type="dot",
                            children=dcc.Graph(id="modal-graph"),
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Fechar", id="close-modal", className="ms-auto", n_clicks=0
                        )
                    ),
                ],
                id="asset-modal",
                size="lg",
                is_open=False,
            ),
        ],
        fluid=True,
        className="p-4 bg-light",
    )

    return layout
