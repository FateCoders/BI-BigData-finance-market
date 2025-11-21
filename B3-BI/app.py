import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests # <--- ADICIONADO

# --- INÍCIO DA MODIFICAÇÃO: Carregando dados da API ---

# URLs da API (garanta que o docker-compose do B3-pipeline está rodando)
API_IBOV_URL = "http://localhost:5001/api/ibov"
API_SELIC_URL = "http://localhost:5001/api/selic"

def fetch_api_data(url):
    """Busca dados da API e retorna um DataFrame."""
    try:
        response = requests.get(url)
        # Gera um erro para status ruins (ex: 404, 500)
        response.raise_for_status() 
        data = response.json()
        df = pd.DataFrame.from_records(data)
        return df
    except requests.exceptions.RequestException as e:
        print(f"ERRO AO ACESSAR API {url}: {e}")
        print("Certifique-se que o 'docker-compose up' do B3-pipeline está em execução.")
        return pd.DataFrame() # Retorna DF vazio em caso de erro

# 1. Carregar Dados do IBOV
print("Carregando dados do IBOV via API...")
df_ibov = fetch_api_data(API_IBOV_URL)
if not df_ibov.empty:
    df_ibov['Date'] = pd.to_datetime(df_ibov['Date'])
    df_ibov = df_ibov.set_index('Date')
    # A app espera um DataFrame com tickers como colunas. Usaremos 'Close' do IBOV.
    # Renomeamos 'Close' para 'IBOV' para ficar claro no dashboard.
    df_precos = df_ibov[['Close']].rename(columns={'Close': 'IBOV'})
else:
    print("ERRO: Não foi possível carregar dados do IBOV. Dashboard pode não funcionar.")
    df_precos = pd.DataFrame()

# 2. Carregar Dados da SELIC
print("Carregando dados da SELIC via API...")
df_selic_raw = fetch_api_data(API_SELIC_URL)
if not df_selic_raw.empty:
    # Renomear colunas da API ('Date', 'Value') para bater com a lógica original do script ('data', 'valor')
    df_selic_raw = df_selic_raw.rename(columns={'Date': 'data', 'Value': 'valor'})
    
    # Processamento da SELIC (lógica mantida do script original)
    df_selic = df_selic_raw.copy()
    df_selic['data'] = pd.to_datetime(df_selic['data']) # API já retorna ISO
    df_selic = df_selic.set_index('data')
    # A API retorna o valor percentual (ex: 0.0419), dividimos por 100 para ter o retorno diário
    df_selic['retorno_diario'] = pd.to_numeric(df_selic['valor']) / 100
    retornos_selic_global = df_selic['retorno_diario']
    dias_uteis = 252
    taxa_selic_anual_mock = retornos_selic_global.mean() * dias_uteis # Renomeado para 'taxa_selic_anual'
else:
    print("ERRO: Não foi possível carregar dados da SELIC. Benchmark pode não funcionar.")
    retornos_selic_global = pd.Series(dtype=float)
    taxa_selic_anual_mock = 0.0 # Renomeado para 'taxa_selic_anual'

# 3. Calcular Retornos (lógica mantida)
df_retornos = df_precos.pct_change().dropna()
disponiveis_lista = df_precos.columns # Agora será apenas ['IBOV']

# --- FIM DA MODIFICAÇÃO ---


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
server = app.server

# Atualiza a lista de ações disponíveis (agora só tem IBOV)
acoes_disponiveis = [{'label': t, 'value': t} for t in disponiveis_lista]

app.layout = dbc.Container([
    
    dbc.Row(dbc.Col(html.H2([html.I(className="bi bi-graph-up me-2"), "Simulador de Portfólio Interativo (B3)"]), width=12, className="text-center my-4")),
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader([html.I(className="bi bi-archive-fill me-2"), "Ativos Disponíveis (Via API)"]),
                    dbc.CardBody(
                        [
                            # Atualizado para mostrar o ativo da API
                            html.Span([dbc.Badge(ticker, color="primary", className="me-2 mb-2") for ticker in disponiveis_lista])
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
                                            value=['IBOV'], # <--- MODIFICADO (Default é IBOV)
                                            multi=True
                                        )
                                    ], md=5
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Defina os Pesos (ex: 1.0):", className="form-label"),
                                        dcc.Input(
                                            id='weight-inputs',
                                            type='text',
                                            value='1.0', # <--- MODIFICADO (Default é 1.0)
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
    
    # Esta função (callback) não precisou de quase nenhuma mudança,
    # pois a lógica de cálculo (dot product) funciona igual
    # para 1 ou N ativos.
    
    empty_fig = go.Figure().update_layout(
        template="plotly_white",
        title="Selecione as ações e clique em 'Simular'",
        yaxis_title="Valor (R$)",
        yaxis_tickprefix="R$ "
    )
    
    style_output = {'display': 'none'}
    
    if n_clicks == 0:
        return empty_fig, [], "", style_output 

    # Validação dos inputs (sem mudança)
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
        # Lógica de cálculo (sem mudança)
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

    
    # Plotagem do Gráfico (sem mudança)
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=valor_portfolio.index,
        y=valor_portfolio,
        mode='lines',
        name='Meu Portfólio (IBOV)', # Nome atualizado
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
    
    
    # Cards de Métricas (sem mudança)
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