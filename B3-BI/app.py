import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, ALL, ctx
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests

# --- 1. CONFIGURAÇÃO E CARREGAMENTO DE DADOS ---

# Dicionário de Endpoints (Ativos de Renda Variável)
ATIVOS_ENDPOINTS = {
    'IBOV': 'http://localhost:5001/api/ticker/ibov',
    'PETR4': 'http://localhost:5001/api/ticker/petr4_sa',
    'VALE3': 'http://localhost:5001/api/ticker/vale3_sa',
    'ITUB4': 'http://localhost:5001/api/ticker/itub4_sa',
    'ABEV3': 'http://localhost:5001/api/ticker/abev3_sa',
    'BBAS3': 'http://localhost:5001/api/ticker/bbas3_sa',
    'WEGE3': 'http://localhost:5001/api/ticker/wege3_sa',
    'PRIO3': 'http://localhost:5001/api/ticker/prio3_sa'
}

# Endpoint da SELIC (Renda Fixa / Benchmark)
API_SELIC_URL = "http://localhost:5001/api/ticker/selic"

def fetch_api_data(url, timeout=5):
    """Busca dados da API de forma resiliente."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame.from_records(data)
        return df
    except requests.exceptions.RequestException as e:
        print(f"   [ERRO] Falha na conexão com {url}: {e}")
        return pd.DataFrame()

# --- 1.1 Processamento dos Ativos (Renda Variável) ---
print("\n=== INICIANDO CARGA DE DADOS ===")

dfs_ativos = []

for ticker, url in ATIVOS_ENDPOINTS.items():
    print(f" -> Carregando {ticker}...")
    df_temp = fetch_api_data(url)
    
    if not df_temp.empty:
        df_temp.columns = [c.lower() for c in df_temp.columns]
        if 'close' in df_temp.columns:
            if 'date' in df_temp.columns:
                df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                df_temp = df_temp.set_index('date')
            df_ativo = df_temp[['close']].rename(columns={'close': ticker})
            dfs_ativos.append(df_ativo)
    else:
        print(f"    [AVISO] {ticker}: Sem dados disponíveis na API.")

# Consolida Ativos
if dfs_ativos:
    df_precos = pd.concat(dfs_ativos, axis=1).dropna() 
    print(f" -> Sucesso! {len(dfs_ativos)} ativos carregados e sincronizados.")
else:
    print(" -> [ERRO CRÍTICO] Nenhum ativo carregado. O dashboard ficará vazio.")
    df_precos = pd.DataFrame()

if not df_precos.empty:
    df_retornos = df_precos.pct_change().dropna()
    disponiveis_lista = df_precos.columns.tolist()
else:
    df_retornos = pd.DataFrame()
    disponiveis_lista = []


# --- 1.2 Processamento da SELIC (Benchmark) ---
print(" -> Carregando Benchmark (SELIC)...")
df_selic_raw = fetch_api_data(API_SELIC_URL)

taxa_selic_anual_mock = 0.10 # Fallback de segurança
retornos_selic_global = pd.Series(dtype=float)

if not df_selic_raw.empty:
    try:
        cols = [c.lower() for c in df_selic_raw.columns]
        df_selic_raw.columns = cols
        
        if 'date' in df_selic_raw.columns:
            # Formato específico para a SELIC (dd/mm/yyyy)
            df_selic_raw['date'] = pd.to_datetime(df_selic_raw['date'], format='%d/%m/%Y', errors='coerce')
            df_selic_raw = df_selic_raw.dropna(subset=['date']).set_index('date')

        # Lógica para Valor da Selic (Value ou Close)
        if 'value' in df_selic_raw.columns:
            df_selic_raw['retorno_diario'] = pd.to_numeric(df_selic_raw['value'], errors='coerce') / 100
            retornos_selic_global = df_selic_raw['retorno_diario'].dropna()
        elif 'close' in df_selic_raw.columns:
             df_selic_raw['retorno_diario'] = df_selic_raw['close'].pct_change()
             retornos_selic_global = df_selic_raw['retorno_diario'].dropna()

        if not retornos_selic_global.empty:
            dias_uteis = 252
            taxa_selic_anual_mock = retornos_selic_global.mean() * dias_uteis
            print(f" -> Sucesso! SELIC carregada (Taxa Média: {taxa_selic_anual_mock:.2%})")
    except Exception as e:
        print(f"    [ERRO] Falha ao processar SELIC: {e}")
else:
    print("    [AVISO] API da SELIC vazia. Usando taxa fixa de 10%.")

print("=== CARGA FINALIZADA ===\n")


# --- 2. APP DASH ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
server = app.server

# Lista de opções para o Dropdown
acoes_disponiveis = [{'label': t, 'value': t} for t in disponiveis_lista]

# --- Layout dos Badges Clicáveis ---
# Geramos os badges dinamicamente com Pattern Matching ID
badges_layout = []
if disponiveis_lista:
    for ticker in disponiveis_lista:
        badges_layout.append(
            dbc.Badge(
                ticker, 
                id={'type': 'asset-badge', 'index': ticker}, # ID Dinâmico
                n_clicks=0,
                color="success" if ticker != 'IBOV' else "primary", 
                className="me-2 mb-2 p-2",
                style={"cursor": "pointer", "userSelect": "none"} # Cursor de mãozinha
            )
        )
else:
    badges_layout = [html.P("Nenhum ativo carregado. Verifique a API.", className="text-danger")]


app.layout = dbc.Container([
    
    # Título
    dbc.Row(dbc.Col(html.H2([html.I(className="bi bi-graph-up me-2"), "Simulador de Portfólio Interativo (B3)"]), width=12, className="text-center my-4")),
    
    # Card 1: Ativos Disponíveis (Agora Clicáveis)
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader([html.I(className="bi bi-archive-fill me-2"), "Ativos Disponíveis (Clique para detalhes)"]),
                    dbc.CardBody(
                        [
                            html.P("Clique em um ativo para ver sua evolução individual:", className="text-muted small mb-2"),
                            html.Div(badges_layout)
                        ]
                    )
                ],
                className="mb-4" 
            ),
            width=12
        )
    ),
    
    # Card 2: Configurações
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
                                        html.Label("Selecione os Ativos:", className="form-label fw-bold"),
                                        dcc.Dropdown(
                                            id='stock-selector',
                                            options=acoes_disponiveis,
                                            value=['IBOV'] if 'IBOV' in disponiveis_lista else [],
                                            multi=True,
                                            placeholder="Escolha ações para compor a carteira..."
                                        )
                                    ], md=5
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Pesos (separados por vírgula):", className="form-label fw-bold"),
                                        dcc.Input(
                                            id='weight-inputs',
                                            type='text',
                                            value='1.0',
                                            placeholder="Ex: 0.5, 0.5",
                                            className="form-control"
                                        ),
                                        dbc.FormText("A soma deve ser 1.0 (100%)")
                                    ], md=4
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Aporte Inicial (R$):", className="form-label fw-bold"),
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
                                            [html.I(className="bi bi-play-circle me-2"), "Simular Carteira"],
                                            id='run-button', 
                                            n_clicks=0, 
                                            color="primary",
                                            className="w-100 mt-4 fw-bold" 
                                        ),
                                        html.Div(id='error-message', className="text-danger mt-3 text-center fw-bold")
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
    
    # Card 3: Resultados
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
                        className="mt-4 shadow-sm" 
                    )
                ]
            ),
            width=12
        )
    ),
    
    # --- MODAL DE DETALHES DO ATIVO ---
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
            dbc.ModalBody(
                dcc.Loading(
                    id="loading-modal",
                    type="dot",
                    children=dcc.Graph(id="modal-graph")
                )
            ),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="asset-modal",
        size="lg", # Grande
        is_open=False,
    ),
    
], fluid=True, className="p-4 bg-light")


# --- 3. CALLBACKS ---

# CALLBACK 1: Modal de Detalhes do Ativo
@app.callback(
    [Output("asset-modal", "is_open"),
     Output("modal-title", "children"),
     Output("modal-graph", "figure")],
    [Input({'type': 'asset-badge', 'index': ALL}, 'n_clicks'),
     Input("close-modal", "n_clicks")],
    [State("asset-modal", "is_open")]
)
def toggle_asset_modal(n_clicks_badges, n_click_close, is_open):
    # Descobre quem disparou o callback
    triggered_id = ctx.triggered_id
    
    # Se nada disparou (inicialização) ou se não há dados
    if not triggered_id or df_precos.empty:
        return False, "", go.Figure()

    # Se foi o botão de fechar
    if triggered_id == "close-modal":
        return False, "", go.Figure()
    
    # Se foi um badge (o ID é um dicionário {'type':..., 'index': 'PETR4'})
    if isinstance(triggered_id, dict) and triggered_id['type'] == 'asset-badge':
        ticker_selecionado = triggered_id['index']
        
        # Verifica se o clique foi real (n_clicks > 0)
        # O Dash dispara callbacks na inicialização com n_clicks=0 ou None
        # Precisamos verificar se algum dos badges tem n_clicks > 0
        if not any(c for c in n_clicks_badges if c):
             return is_open, "", go.Figure()

        # Gera o gráfico do ativo
        try:
            df_ativo = df_precos[ticker_selecionado]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_ativo.index, 
                y=df_ativo, 
                mode='lines', 
                name=ticker_selecionado,
                line=dict(color="#0d6efd")
            ))
            
            fig.update_layout(
                title=f"Evolução Histórica: {ticker_selecionado}",
                xaxis_title="Data",
                yaxis_title="Preço de Fechamento (R$)",
                yaxis_tickprefix="R$ ",
                template="plotly_white",
                hovermode="x unified",
                margin=dict(l=40, r=20, t=40, b=40)
            )
            
            return True, f"Detalhes: {ticker_selecionado}", fig
            
        except KeyError:
            return is_open, "Erro ao carregar dados", go.Figure()

    return is_open, "", go.Figure()


# CALLBACK 2: Simulação do Portfólio (Mantido)
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
    
    style_hidden = {'display': 'none'}
    style_visible = {'display': 'block'}
    
    if n_clicks == 0:
        return empty_fig, [], "", style_hidden

    # Validações básicas
    if not selected_tickers:
        return empty_fig, [], "Erro: Nenhuma ação selecionada.", style_hidden

    if aporte_inicial is None or aporte_inicial <= 0:
        return empty_fig, [], "Erro: Aporte inicial inválido.", style_hidden
        
    try:
        clean_weight_str = weight_str.replace(";", ",") 
        pesos_list = [float(w.strip()) for w in clean_weight_str.split(',')]
        pesos = np.array(pesos_list)
    except Exception:
        return empty_fig, [], "Erro: Formato dos pesos incorreto. Use números separados por vírgula.", style_hidden

    if len(pesos) != len(selected_tickers):
        return empty_fig, [], f"Erro: Você selecionou {len(selected_tickers)} ativos, mas informou {len(pesos)} pesos.", style_hidden
    
    if not np.isclose(np.sum(pesos), 1.0, atol=0.01): 
        return empty_fig, [], f"Erro: A soma dos pesos deve ser 1.0 (Soma atual: {np.sum(pesos):.2f}).", style_hidden

    try:
        # --- CÁLCULOS FINANCEIROS ---
        retornos_selecionados = df_retornos[selected_tickers]
        retorno_portfolio = retornos_selecionados.dot(pesos)
        
        volatilidade = retorno_portfolio.std() * np.sqrt(252)
        retorno_medio_anual = retorno_portfolio.mean() * 252
        sharpe_ratio = (retorno_medio_anual - taxa_selic_anual_mock) / volatilidade if volatilidade > 0 else 0
        
        # Benchmark Simulado
        val_media_diaria = 0
        if not retornos_selic_global.empty:
            val_media_diaria = retornos_selic_global.mean()
        elif taxa_selic_anual_mock > 0:
             val_media_diaria = taxa_selic_anual_mock / 252
             
        retornos_selic_simulados = pd.Series(val_media_diaria, index=retorno_portfolio.index)

        # Performance Acumulada
        perf_cum_port = (1 + retorno_portfolio).cumprod()
        perf_cum_selic = (1 + retornos_selic_simulados).cumprod()
        
        valor_portfolio = perf_cum_port * aporte_inicial
        valor_selic = perf_cum_selic * aporte_inicial
        
        valor_final_port = valor_portfolio.iloc[-1]
        valor_final_selic = valor_selic.iloc[-1]
        retorno_total_pct = (valor_final_port / aporte_inicial) - 1

    except Exception as e:
        return empty_fig, [], f"Erro no cálculo financeiro: {str(e)}", style_hidden

    # --- GRÁFICOS E VISUAL ---
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=valor_portfolio.index, y=valor_portfolio,
        mode='lines', name='Minha Carteira',
        line=dict(color="#0d6efd", width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=valor_selic.index, y=valor_selic,
        mode='lines', name='Benchmark (SELIC Média)',
        line=dict(color="#6c757d", dash="dot", width=2)
    ))
    
    fig.update_layout(
        title="Evolução Patrimonial Comparativa",
        xaxis_title="Data",
        yaxis_title="Valor Patrimonial (R$)",
        yaxis_tickprefix="R$ ",
        yaxis_separatethousands=True,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    def create_metric_card(title, value, color_text="text-dark", subtext=None):
        return dbc.Card(
            dbc.CardBody([
                html.H6(title, className="card-subtitle text-muted mb-2 small text-uppercase fw-bold"),
                html.P(value, className=f"card-text fs-4 fw-bold {color_text} mb-0"),
                html.Small(subtext, className="text-muted") if subtext else None
            ]),
            className="text-center shadow-sm h-100 border-0",
            color="light"
        )

    cor_resultado = "text-success" if valor_final_port >= valor_final_selic else "text-danger"

    metrics_display = [
        dbc.Col(create_metric_card("Saldo Final", f"R$ {valor_final_port:,.2f}", cor_resultado, f"Retorno: {retorno_total_pct:.1%}"), md=3, sm=6),
        dbc.Col(create_metric_card("Benchmark (SELIC)", f"R$ {valor_final_selic:,.2f}", "text-secondary"), md=3, sm=6),
        dbc.Col(create_metric_card("Volatilidade (a.a.)", f"{volatilidade:.1%}", "text-warning"), md=3, sm=6),
        dbc.Col(create_metric_card("Sharpe Ratio", f"{sharpe_ratio:.2f}", "text-info"), md=3, sm=6),
    ]
    
    return fig, metrics_display, "", style_visible

if __name__ == '__main__':
    app.run(debug=True)