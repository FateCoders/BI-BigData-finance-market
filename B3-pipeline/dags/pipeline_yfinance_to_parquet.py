from airflow.decorators import dag, task
from datetime import datetime
import yfinance as yf
import pandas as pd
import logging
import os

@dag(
    dag_id="pipeline_yfinance_to_parquet",
    description="Coleta dados do Yahoo Finance (ex: IBOV)",
    start_date=datetime(2025, 10, 27),
    schedule="@daily",
    catchup=False
)
def pipeline_b3_yfinance_func():

    @task
    def extrair_salvar_dados_yfinance():
        pasta_dados = "/opt/airflow/data"
        nome_arquivo = "ibov_dados_brutos.parquet"
        caminho_parquet = os.path.join(pasta_dados, nome_arquivo)

        os.makedirs(pasta_dados, exist_ok=True)

        try:
            ticker = "^BVSP"
            logging.info(f"Buscando dados para o ticker: {ticker}")
            
            dados = yf.download(ticker, period="1y")
            
            if dados.empty:
                logging.warning(f"Nenhum dado retornado para {ticker}")
                return None

            df = dados.reset_index()
            
            df.to_parquet(caminho_parquet, index=False)
            
            logging.info(f"Gerou '{caminho_parquet}' com sucesso!")
            return caminho_parquet

        except Exception as e:
            logging.error(f"Erro ao processar os dados: {e}")
            raise

    extrair_salvar_dados_yfinance()

pipeline_b3_yfinance_func()