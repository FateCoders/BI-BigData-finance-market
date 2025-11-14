from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import logging

# Importa a *nova* função do nosso plugin
try:
    from b3_processing import selic_parquet_to_duckdb
except ImportError:
    logging.error("Erro fatal: Não foi possível encontrar 'selic_parquet_to_duckdb' na pasta de plugins.")
    def selic_parquet_to_duckdb(**kwargs):
        raise ImportError("Módulo 'b3_processing' não encontrado no PYTHONPATH.")

# Dataset que esta DAG consome
selic_parquet_dataset = Dataset("file:///opt/airflow/data/selic_dados_brutos.parquet")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id="pipeline_selic_parquet_to_duckdb",
    description="Limpa o Parquet bruto da SELIC e carrega no DuckDB.",
    start_date=datetime(2023, 1, 1),
    schedule=[selic_parquet_dataset],  # Acionado pelo Dataset da DAG anterior
    catchup=False,
    tags=['b3', 'duckdb', 'parquet', 'etl', 'selic'],
    default_args=default_args
)
def dag_processar_selic_para_duckdb():

    @task
    def transformar_e_carregar_selic_duckdb():
        logging.info("Iniciando tarefa de limpeza e carga da SELIC para DuckDB...")
        selic_parquet_to_duckdb()
        logging.info("Tarefa de carga da SELIC no DuckDB concluída.")

    transformar_e_carregar_selic_duckdb()

dag_processar_selic_para_duckdb()