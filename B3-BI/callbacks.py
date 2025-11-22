from dash import Input, Output, State, ALL, ctx
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from dash import html


def register_callbacks(app, data_cache):
    """Registra todos os callbacks da aplicação."""

    df_precos = data_cache["df_precos"]
    df_retornos = data_cache["df_retornos"]
    retornos_selic_global = data_cache["selic_global"]
    taxa_selic_anual_mock = data_cache["selic_anual"]

    @app.callback(
        [
            Output("asset-modal", "is_open"),
            Output("modal-title", "children"),
            Output("modal-graph", "figure"),
        ],
        [
            Input({"type": "asset-badge", "index": ALL}, "n_clicks"),
            Input("close-modal", "n_clicks"),
        ],
        [State("asset-modal", "is_open")],
    )
    def toggle_asset_modal(n_clicks_badges, n_click_close, is_open):
        triggered_id = ctx.triggered_id

        if not triggered_id or df_precos.empty:
            return False, "", go.Figure()

        if triggered_id == "close-modal":
            return False, "", go.Figure()

        if isinstance(triggered_id, dict) and triggered_id["type"] == "asset-badge":

            if not any(c for c in n_clicks_badges if c):
                return is_open, "", go.Figure()

            ticker_selecionado = triggered_id["index"]
            try:
                df_ativo = df_precos[ticker_selecionado]
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df_ativo.index,
                        y=df_ativo,
                        mode="lines",
                        name=ticker_selecionado,
                        line=dict(color="#0d6efd"),
                    )
                )
                fig.update_layout(
                    title=f"Evolução Histórica: {ticker_selecionado}",
                    xaxis_title="Data",
                    yaxis_title="Preço (R$)",
                    yaxis_tickprefix="R$ ",
                    template="plotly_white",
                    hovermode="x unified",
                    margin=dict(l=40, r=20, t=40, b=40),
                )
                return True, f"Detalhes: {ticker_selecionado}", fig
            except KeyError:
                return is_open, "Erro ao carregar dados", go.Figure()

        return is_open, "", go.Figure()

    @app.callback(
        [
            Output("portfolio-graph", "figure"),
            Output("metrics-output", "children"),
            Output("error-message", "children"),
            Output("results-container", "style"),
        ],
        [Input("run-button", "n_clicks")],
        [
            State("stock-selector", "value"),
            State("weight-inputs", "value"),
            State("aporte-input", "value"),
        ],
    )
    def update_portfolio(n_clicks, selected_tickers, weight_str, aporte_inicial):
        empty_fig = go.Figure().update_layout(template="plotly_white")
        style_hidden = {"display": "none"}
        style_visible = {"display": "block"}

        if n_clicks == 0:
            return empty_fig, [], "", style_hidden

        if not selected_tickers:
            return empty_fig, [], "Erro: Nenhuma ação selecionada.", style_hidden

        if aporte_inicial is None or aporte_inicial <= 0:
            return empty_fig, [], "Erro: Aporte inicial inválido.", style_hidden

        try:
            clean_weight_str = weight_str.replace(";", ",")
            pesos_list = [float(w.strip()) for w in clean_weight_str.split(",")]
            pesos = np.array(pesos_list)
        except Exception:
            return empty_fig, [], "Erro: Formato dos pesos incorreto.", style_hidden

        if len(pesos) != len(selected_tickers):
            return (
                empty_fig,
                [],
                f"Erro: Ativos ({len(selected_tickers)}) vs Pesos ({len(pesos)}) incompatível.",
                style_hidden,
            )

        if not np.isclose(np.sum(pesos), 1.0, atol=0.01):
            return empty_fig, [], f"Erro: Soma dos pesos deve ser 1.0.", style_hidden

        try:

            retornos_selecionados = df_retornos[selected_tickers]
            retorno_portfolio = retornos_selecionados.dot(pesos)

            volatilidade = retorno_portfolio.std() * np.sqrt(252)
            retorno_medio_anual = retorno_portfolio.mean() * 252
            sharpe_ratio = (
                (retorno_medio_anual - taxa_selic_anual_mock) / volatilidade
                if volatilidade > 0
                else 0
            )

            val_media_diaria = 0
            if not retornos_selic_global.empty:
                val_media_diaria = retornos_selic_global.mean()
            elif taxa_selic_anual_mock > 0:
                val_media_diaria = taxa_selic_anual_mock / 252

            retornos_selic_simulados = pd.Series(
                val_media_diaria, index=retorno_portfolio.index
            )

            perf_cum_port = (1 + retorno_portfolio).cumprod()
            perf_cum_selic = (1 + retornos_selic_simulados).cumprod()

            valor_portfolio = perf_cum_port * aporte_inicial
            valor_selic = perf_cum_selic * aporte_inicial

            valor_final_port = valor_portfolio.iloc[-1]
            valor_final_selic = valor_selic.iloc[-1]
            retorno_total_pct = (valor_final_port / aporte_inicial) - 1

        except Exception as e:
            return empty_fig, [], f"Erro cálculo: {str(e)}", style_hidden

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=valor_portfolio.index,
                y=valor_portfolio,
                mode="lines",
                name="Minha Carteira",
                line=dict(color="#0d6efd", width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=valor_selic.index,
                y=valor_selic,
                mode="lines",
                name="Benchmark (SELIC Média)",
                line=dict(color="#6c757d", dash="dot", width=2),
            )
        )

        fig.update_layout(
            title="Evolução Patrimonial Comparativa",
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            yaxis_tickprefix="R$ ",
            yaxis_separatethousands=True,
            hovermode="x unified",
            template="plotly_white",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=40, r=40, t=60, b=40),
        )

        def create_metric_card(title, value, color_text="text-dark", subtext=None):
            return dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            title,
                            className="card-subtitle text-muted mb-2 small text-uppercase fw-bold",
                        ),
                        html.P(
                            value, className=f"card-text fs-4 fw-bold {color_text} mb-0"
                        ),
                        (
                            html.Small(subtext, className="text-muted")
                            if subtext
                            else None
                        ),
                    ]
                ),
                className="text-center shadow-sm h-100 border-0",
                color="light",
            )

        cor_res = (
            "text-success" if valor_final_port >= valor_final_selic else "text-danger"
        )
        metrics = [
            dbc.Col(
                create_metric_card(
                    "Saldo Final",
                    f"R$ {valor_final_port:,.2f}",
                    cor_res,
                    f"Retorno: {retorno_total_pct:.1%}",
                ),
                md=3,
                sm=6,
            ),
            dbc.Col(
                create_metric_card(
                    "Benchmark (SELIC)",
                    f"R$ {valor_final_selic:,.2f}",
                    "text-secondary",
                ),
                md=3,
                sm=6,
            ),
            dbc.Col(
                create_metric_card(
                    "Volatilidade", f"{volatilidade:.1%}", "text-warning"
                ),
                md=3,
                sm=6,
            ),
            dbc.Col(
                create_metric_card("Sharpe", f"{sharpe_ratio:.2f}", "text-info"),
                md=3,
                sm=6,
            ),
        ]

        return fig, metrics, "", style_visible
