import requests
import pandas as pd
import numpy as np


ATIVOS_ENDPOINTS = {
    "IBOV": "http://localhost:5001/api/ticker/ibov",
    "PETR4": "http://localhost:5001/api/ticker/petr4_sa",
    "VALE3": "http://localhost:5001/api/ticker/vale3_sa",
    "ITUB4": "http://localhost:5001/api/ticker/itub4_sa",
    "ABEV3": "http://localhost:5001/api/ticker/abev3_sa",
    "BBAS3": "http://localhost:5001/api/ticker/bbas3_sa",
    "WEGE3": "http://localhost:5001/api/ticker/wege3_sa",
    "PRIO3": "http://localhost:5001/api/ticker/prio3_sa",
}

API_SELIC_URL = "http://localhost:5001/api/ticker/selic"


def fetch_api_data(url, timeout=5):

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame.from_records(data)
        return df
    except requests.exceptions.RequestException as e:
        print(f"   [ERRO] Falha na conexão com {url}: {e}")
        return pd.DataFrame()


def load_all_data():

    print("\n=== INICIANDO CARGA DE DADOS (data.py) ===")

    dfs_ativos = []
    for ticker, url in ATIVOS_ENDPOINTS.items():
        print(f" -> Carregando {ticker}...")
        df_temp = fetch_api_data(url)
        if not df_temp.empty:
            df_temp.columns = [c.lower() for c in df_temp.columns]
            if "close" in df_temp.columns:
                if "date" in df_temp.columns:
                    df_temp["date"] = pd.to_datetime(df_temp["date"], errors="coerce")
                    df_temp = df_temp.set_index("date")
                df_ativo = df_temp[["close"]].rename(columns={"close": ticker})
                dfs_ativos.append(df_ativo)

    if dfs_ativos:
        df_precos = pd.concat(dfs_ativos, axis=1).dropna()
    else:
        df_precos = pd.DataFrame()

    if not df_precos.empty:
        df_retornos = df_precos.pct_change().dropna()
        lista_ativos = df_precos.columns.tolist()
    else:
        df_retornos = pd.DataFrame()
        lista_ativos = []

    print(" -> Carregando Benchmark (SELIC)...")
    df_selic_raw = fetch_api_data(API_SELIC_URL)

    retornos_selic_global = pd.Series(dtype=float)
    taxa_selic_anual = 0.10

    if not df_selic_raw.empty:
        cols = [c.lower() for c in df_selic_raw.columns]
        df_selic_raw.columns = cols
        if "date" in df_selic_raw.columns:
            df_selic_raw["date"] = pd.to_datetime(
                df_selic_raw["date"], format="%d/%m/%Y", errors="coerce"
            )
            df_selic_raw = df_selic_raw.dropna(subset=["date"]).set_index("date")

        if "value" in df_selic_raw.columns:
            df_selic_raw["retorno_diario"] = (
                pd.to_numeric(df_selic_raw["value"], errors="coerce") / 100
            )
            retornos_selic_global = df_selic_raw["retorno_diario"].dropna()
        elif "close" in df_selic_raw.columns:
            df_selic_raw["retorno_diario"] = df_selic_raw["close"].pct_change()
            retornos_selic_global = df_selic_raw["retorno_diario"].dropna()

        if not retornos_selic_global.empty:
            taxa_selic_anual = retornos_selic_global.mean() * 252

    print("=== CARGA FINALIZADA ===\n")

    return {
        "df_precos": df_precos,
        "df_retornos": df_retornos,
        "selic_global": retornos_selic_global,
        "selic_anual": taxa_selic_anual,
        "lista_ativos": lista_ativos,
    }
