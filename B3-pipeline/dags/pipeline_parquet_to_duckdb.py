from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import logging # <-- Adicionado

# Airflow adiciona a pasta 'plugins' ao PYTHONPATH automaticamente.
# Esta é a forma correta e limpa de importar.
try:
    from b3_processing import parquet_to_duckdb
except ImportError:
    logging.error("Erro fatal: Não foi possível encontrar 'b3_processing' na pasta de plugins.")
    # Define uma função placeholder para que a DAG possa ser parseada sem falhar
    def parquet_to_duckdb(**kwargs):
        raise ImportError("Módulo 'b3_processing' não encontrado no PYTHONPATH.")

# Dataset que esta DAG consome
raw_parquet_dataset = Dataset("file:///opt/airflow/data/ibov_dados_brutos.parquet")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id="pipeline_parquet_to_duckdb",
    description="Limpa o Parquet bruto do IBOV e carrega em uma tabela DuckDB.",
    start_date=datetime(2023, 1, 1),
    schedule=[raw_parquet_dataset], # <-- CORRETO: Acionado pelo Dataset
    catchup=False,
    tags=['b3', 'duckdb', 'parquet', 'etl'],
    default_args=default_args
)
def dag_processar_b3_para_duckdb():

    @task
    def transformar_e_carregar_duckdb():
        logging.info("Iniciando tarefa de limpeza e carga para DuckDB...")
        parquet_to_duckdb()
        logging.info("Tarefa de carga no DuckDB concluída.")

    transformar_e_carregar_duckdb()

dag_processar_b3_para_duckdb()