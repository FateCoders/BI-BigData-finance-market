from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import duckdb
import os
import logging
import re

# Acionado quando o pipeline do yfinance termina
yfinance_dataset = Dataset("file:///opt/airflow/data/yfinance_updates")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id="pipeline_parquet_to_duckdb",
    description="Converte dinamicamente Parquets brutos para DuckDB",
    start_date=datetime(2023, 1, 1),
    schedule=[yfinance_dataset], 
    catchup=False,
    default_args=default_args
)
def dag_processar_duckdb_dinamico():

    @task
    def converter_parquets_para_duckdb():
        pasta_dados = "/opt/airflow/data"
        
        # Lista todos os arquivos na pasta que seguem o padrão *_dados_brutos.parquet
        arquivos = [f for f in os.listdir(pasta_dados) if f.endswith('_dados_brutos.parquet')]
        
        if not arquivos:
            logging.warning("Nenhum arquivo parquet bruto encontrado.")
            return

        for arquivo in arquivos:
            try:
                caminho_origem = os.path.join(pasta_dados, arquivo)
                
                # Define nome de saída
                # Ex: petr4_sa_dados_brutos.parquet -> petr4_sa
                prefixo_nome = arquivo.replace('_dados_brutos.parquet', '')
                
                # Nome do arquivo DuckDB e da tabela
                nome_banco = f"{prefixo_nome}_limpo.duckdb"
                caminho_banco = os.path.join(pasta_dados, nome_banco)
                nome_tabela = f"{prefixo_nome}_limpo"

                logging.info(f"Processando {arquivo} -> Tabela {nome_tabela} em {nome_banco}")

                # Conexão com DuckDB
                conn = duckdb.connect(caminho_banco)
                
                # Cria tabela substituindo a anterior se existir
                # Usa CREATE OR REPLACE TABLE ... AS SELECT * FROM read_parquet(...)
                query = f"""
                    CREATE OR REPLACE TABLE {nome_tabela} AS 
                    SELECT * FROM read_parquet('{caminho_origem}')
                """
                conn.execute(query)
                
                # Opcional: Validação simples
                contagem = conn.execute(f"SELECT COUNT(*) FROM {nome_tabela}").fetchone()[0]
                logging.info(f"Sucesso! Tabela {nome_tabela} criada com {contagem} linhas.")
                
                conn.close()

            except Exception as e:
                logging.error(f"Erro ao processar arquivo {arquivo}: {e}")
                # Continua para o próximo arquivo

    converter_parquets_para_duckdb()

dag_processar_duckdb_dinamico()