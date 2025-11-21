from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging
import os
import re

# Dataset genérico para sinalizar que novos dados financeiros chegaram
yfinance_dataset = Dataset("file:///opt/airflow/data/yfinance_updates")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Lista de tickers para monitorar
TICKERS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "ABEV3.SA",
    "BBAS3.SA",
    "WEGE3.SA",
    "PRIO3.SA"
]

def limpar_nome(nome):
    """
    Remove caracteres especiais e pontuações, transformando em snake_case.
    Ex: 'PETR4.SA' -> 'petr4_sa'
    """
    # Remove tudo que não for letra ou número, substituindo por _
    nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', nome)
    # Remove underscores duplicados e converte para minúsculo
    nome_limpo = re.sub(r'_+', '_', nome_limpo).strip('_').lower()
    return nome_limpo

@dag(
    dag_id="pipeline_yfinance_to_parquet",
    description="Coleta dados de múltiplos tickers do Yahoo Finance",
    start_date=datetime(2023, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args
)
def pipeline_yfinance_func():

    @task(outlets=[yfinance_dataset])
    def processar_todos_tickers():
        pasta_dados = "/opt/airflow/data"
        os.makedirs(pasta_dados, exist_ok=True)
        
        arquivos_gerados = []

        for ticker in TICKERS:
            try:
                logging.info(f"Iniciando processamento para: {ticker}")
                
                # Define o nome do arquivo baseado no ticker limpo
                nome_ticker_limpo = limpar_nome(ticker)
                nome_arquivo = f"{nome_ticker_limpo}_dados_brutos.parquet"
                caminho_parquet = os.path.join(pasta_dados, nome_arquivo)

                # Baixa dados
                dados = yf.download(ticker, period="5y", progress=False)
                
                if dados.empty:
                    logging.warning(f"Nenhum dado retornado para {ticker}")
                    continue

                # 1. Flatten MultiIndex se necessário
                if isinstance(dados.columns, pd.MultiIndex):
                    dados.columns = dados.columns.get_level_values(0)
                
                # 2. Reset Index para transformar Date em coluna
                df = dados.reset_index()
                
                # 3. Limpeza dinâmica de nomes de colunas
                # Remove caracteres especiais dos nomes das colunas para evitar erro no Parquet/DuckDB
                df.columns = [limpar_nome(col) for col in df.columns]
                
                # Salva em Parquet
                df.to_parquet(caminho_parquet, index=False)
                logging.info(f"Salvo: {caminho_parquet}")
                arquivos_gerados.append(caminho_parquet)

            except Exception as e:
                logging.error(f"Erro ao processar {ticker}: {e}")
                # Não dá raise aqui para não parar os outros tickers
                continue
        
        return arquivos_gerados

    processar_todos_tickers()

pipeline_yfinance_func()