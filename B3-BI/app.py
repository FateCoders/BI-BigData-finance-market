import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np

def create_mock_data():
    tickers = ['PETR4', 'VALE3', 'ITUB4', 'MGLU3']
    datas = pd.date_range(start='2022-01-01', end='2024-12-31', freq='B') 
    df = pd.DataFrame(index=datas)
    for ticker in tickers:
        precos_base = np.random.randint(20, 100)
        retornos_diarios = np.random.normal(loc=0.0005, scale=0.02, size=len(datas))
        precos = precos_base * (1 + retornos_diarios).cumprod()
        df[ticker] = precos
    return df

def create_mock_selic_data(datas_index):
    df_selic = pd.DataFrame(index=datas_index)
    taxa_diaria_simulada = np.random.normal(loc=0.0004, scale=0.0001, size=len(datas_index))
    df_selic['valor'] = (taxa_diaria_simulada * 100).round(4).astype(str)
    df_selic['data'] = df_selic.index.strftime('%d/%m/%Y')
    df_selic = df_selic.reset_index(drop=True)
    return df_selic

df_precos = create_mock_data()
df_retornos = df_precos.pct_change().dropna()

disponiveis_lista = df_precos.columns

df_selic_mock = create_mock_selic_data(df_precos.index)
df_selic = df_selic_mock.copy()
df_selic['data'] = pd.to_datetime(df_selic['data'], format='%d/%m/%Y')
df_selic = df_selic.set_index('data')
df_selic['retorno_diario'] = pd.to_numeric(df_selic['valor']) / 100
retornos_selic_global = df_selic['retorno_diario']
dias_uteis = 252
taxa_selic_anual_mock = retornos_selic_global.mean() * dias_uteis

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
server = app.server
acoes_disponiveis = [{'label': t, 'value': t} for t in disponiveis_lista]

app.layout = dbc.Container([
    
    dbc.Row(dbc.Col(html.H2([html.I(className="bi bi-graph-up me-2"), "Simulador de Portfólio Interativo (B3)"]), width=12, className="text-center my-4")),
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader([html.I(className="bi bi-archive-fill me-2"), "Ativos Disponíveis para Simulação"]),
                    dbc.CardBody(
                        [
                            html.Span([dbc.Badge(ticker, color="secondary", className="me-2 mb-2") for ticker in disponiveis_lista])
                        ]
                    )
                ],
                className="mb-4" 
            ),
            width=12
        )
    ),
    
    
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader([html.I(className="bi bi-gear-fill me-2"), "Configurações da Simulação"]),
                    dbc.CardBody(
                        [
                            dbc.Row(className="g-3", children=[
                                dbc.Col(
                                    [
                                        html.Label("Selecione as Ações:", className="form-label"),
                                        dcc.Dropdown(
                                            id='stock-selector',
                                            options=acoes_disponiveis,
                                            value=['PETR4', 'VALE3'],
                                            multi=True
                                        )
                                    ], md=5
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Defina os Pesos (ex: 0.5, 0.5):", className="form-label"),
                                        dcc.Input(
                                            id='weight-inputs',
                                            type='text',
                                            value='0.5, 0.5',
                                            className="form-control"
                                        )
                                    ], md=4
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Aporte Inicial (R$):", className="form-label"),
                                        dcc.Input(
                                            id='aporte-input',
                                            type='number',
                                            value=1000,
                                            min=1,
                                            className="form-control"
                                        )
                                    ], md=3
                                ),
                            ]),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            [html.I(className="bi bi-play-circle me-2"), "Simular Portfólio"],
                                            id='run-button', 
                                            n_clicks=0, 
                                            color="primary",
                                            className="w-100 mt-4" 
                                        ),
                                        html.Div(id='error-message', className="text-danger mt-3 text-center")
                                    ],
                                    width=12
                                )
                            )
                        ]
                    )
                ]
            ),
            width=12
        )
    ),
    
    
    dbc.Row(
        dbc.Col(
            
            html.Div(
                id='results-container',
                style={'display': 'none'}, 
                children=[
                    dbc.Card(
                        [
                            dbc.CardHeader([html.I(className="bi bi-bar-chart-line-fill me-2"), "Resultados da Simulação"]),
                            dbc.CardBody(
                                [
                                    
                                    dbc.Row(id='metrics-output', className="mb-4 g-3"), 
                                    
                                    
                                    dbc.Row(
                                        dbc.Col(
                                            dcc.Loading(
                                                id="loading-graph",
                                                type="dot",
                                                children=dcc.Graph(
                                                    id='portfolio-graph',
                                                    config={'responsive': True}
                                                )
                                            ),
                                            width=12
                                        )
                                    )
                                ]
                            )
                        ],
                        className="mt-4" 
                    )
                ]
            ),
            width=12
        )
    )
    
], fluid=True, className="p-4")



@app.callback(
    [Output('portfolio-graph', 'figure'),
     Output('metrics-output', 'children'),
     Output('error-message', 'children'),
     Output('results-container', 'style')], 
    [Input('run-button', 'n_clicks')],
    [State('stock-selector', 'value'),
     State('weight-inputs', 'value'),
     State('aporte-input', 'value')]
)
def update_portfolio(n_clicks, selected_tickers, weight_str, aporte_inicial):
    
    empty_fig = go.Figure().update_layout(
        template="plotly_white",
        title="Selecione as ações e clique em 'Simular'",
        yaxis_title="Valor (R$)",
        yaxis_tickprefix="R$ "
    )
    
    
    style_output = {'display': 'none'}
    
    
    if n_clicks == 0:
        return empty_fig, [], "", style_output 

    if not selected_tickers:
        return empty_fig, [], "Erro: Nenhuma ação selecionada.", style_output

    if aporte_inicial is None or aporte_inicial <= 0:
        return empty_fig, [], "Erro: Aporte inicial deve ser um número positivo.", style_output
        
    try:
        pesos_list = [float(w.strip()) for w in weight_str.split(',')]
        pesos = np.array(pesos_list)
    except Exception as e:
        return empty_fig, [], "Erro: Formato dos pesos inválido. Use números separados por vírgula (ex: 0.6, 0.4).", style_output

    if len(pesos) != len(selected_tickers):
        return empty_fig, [], f"Erro: Você selecionou {len(selected_tickers)} ações, mas forneceu {len(pesos)} pesos.", style_output
    
    if not np.isclose(np.sum(pesos), 1.0):
        return empty_fig, [], f"Erro: A soma dos pesos deve ser 1.0 (soma atual: {np.sum(pesos):.2f}).", style_output

    
    try:
        retornos_selecionados = df_retornos[selected_tickers]
        retorno_portfolio = retornos_selecionados.dot(pesos)
        
        volatilidade = retorno_portfolio.std() * np.sqrt(dias_uteis)
        retorno_medio_anual = retorno_portfolio.mean() * dias_uteis
        sharpe_ratio = (retorno_medio_anual - taxa_selic_anual_mock) / volatilidade 
        
        retornos_selic_alinhados = retornos_selic_global.reindex(retorno_portfolio.index).ffill()
        
        performance_cumulativa_port = (1 + retorno_portfolio).cumprod()
        performance_cumulativa_selic = (1 + retornos_selic_alinhados).cumprod()
        
        valor_portfolio = performance_cumulativa_port * aporte_inicial
        valor_selic = performance_cumulativa_selic * aporte_inicial
        
        valor_final_portfolio = valor_portfolio.iloc[-1]
        valor_final_selic = valor_selic.iloc[-1]

    except Exception as e:
        return empty_fig, [], f"Erro no cálculo: {e}", style_output

    
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=valor_portfolio.index,
        y=valor_portfolio,
        mode='lines',
        name='Meu Portfólio',
        line=dict(color="#0d6efd") 
    ))
    
    fig.add_trace(go.Scatter(
        x=valor_selic.index,
        y=valor_selic,
        mode='lines',
        name='Benchmark (SELIC)',
        line=dict(color="#6c757d", dash="dot") 
    ))
    
    fig.update_layout(
        title="Performance Histórica: Portfólio vs. Benchmark",
        xaxis_title="Data",
        yaxis_title="Valor (R$)",
        yaxis_tickprefix="R$ ",
        yaxis_separatethousands=True,
        hovermode="x unified",
        template="plotly_white",
        legend_title_text='Legenda'
    )
    
    
    def create_metric_card(title, value, color_class="text-dark"):
        return dbc.Card(
            dbc.CardBody([
                html.H6(title, className="card-subtitle text-muted"),
                html.P(value, className=f"card-text fs-4 {color_class}")
            ]),
            className="text-center",
            color="light" 
        )

    metrics_display = [
        
        dbc.Col(create_metric_card("Valor Final (Portfólio)", f"R$ {valor_final_portfolio:,.2f}", "text-success"), md=6),
        dbc.Col(create_metric_card("Valor Final (SELIC)", f"R$ {valor_final_selic:,.2f}", "text-primary"), md=6),
        
        dbc.Col(create_metric_card("Volatilidade (a.a.)", f"{volatilidade:.2%}", "text-warning"), md=6),
        
        dbc.Col(create_metric_card("Sharpe Ratio", f"{sharpe_ratio:.2f}", "text-info"), md=6),
    ]

    
    style_output = {'display': 'block'}
    
    return fig, metrics_display, "", style_output



if __name__ == '__main__':
    app.run(debug=True)