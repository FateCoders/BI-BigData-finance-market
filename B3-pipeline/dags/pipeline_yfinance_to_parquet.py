from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging
import os

raw_parquet_dataset = Dataset("file:///opt/airflow/data/ibov_dados_brutos.parquet")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id="pipeline_yfinance_to_parquet",
    description="Coleta dados do Yahoo Finance (ex: IBOV)",
    start_date=datetime(2023, 1, 1),  # Data no passado para rodar ao iniciar
    schedule="@daily",
    catchup=False,
    default_args=default_args
)
def pipeline_b3_yfinance_func():

    @task(outlets=[raw_parquet_dataset])
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

            # --- INÍCIO DA CORREÇÃO ---
            
            # 1. ACHATAR (FLATTEN) COLUNAS MULTI-INDEX
            # O yfinance retorna colunas como ('Close', '^BVSP').
            # Queremos apenas o primeiro nível (ex: 'Close')
            if isinstance(dados.columns, pd.MultiIndex):
                logging.info("DataFrame possui MultiIndex. Aplicando flatten...")
                # Pega apenas o primeiro nível do MultiIndex
                dados.columns = dados.columns.get_level_values(0)
            
            # 2. RESETAR O ÍNDICE (para 'Date' virar uma coluna)
            df = dados.reset_index()
            
            # 3. GARANTIR O SCHEMA CORRETO
            # Mantém apenas as colunas que o pipeline espera, na ordem correta.
            colunas_para_manter = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            # Filtra o DataFrame para conter apenas essas colunas
            df = df[colunas_para_manter]

            # --- FIM DA CORREÇÃO ---
            
            df.to_parquet(caminho_parquet, index=False)
            
            logging.info(f"Gerou '{caminho_parquet}' com sucesso! Colunas: {df.columns.to_list()}")
            return caminho_parquet

        except Exception as e:
            logging.error(f"Erro ao processar os dados: {e}")
            raise

    extrair_salvar_dados_yfinance()

pipeline_b3_yfinance_func()