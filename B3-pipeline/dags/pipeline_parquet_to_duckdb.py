from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta

import sys
import os

DAG_DIR = os.path.dirname(__file__)
PLUGIN_DIR = os.path.join(DAG_DIR, '..', 'plugins')

if PLUGIN_DIR not in sys.path:
    sys.path.append(PLUGIN_DIR)


try:
    from b3_processing import parquet_to_duckdb
except ImportError:
    print(f"Erro ao importar 'b3_processing'. Verifique se 'plugins/b3_processing.py' existe e o sys.path está correto. Sys.path: {sys.path}")
    
    def parquet_to_duckdb(**kwargs):
        raise ImportError("Módulo 'b3_processing' não encontrado no PYTHONPATH.")

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
    schedule=[raw_parquet_dataset],
    catchup=False,
    tags=['b3', 'duckdb', 'parquet', 'etl'],
    default_args=default_args
)
def dag_processar_b3_para_duckdb():

    @task
    def transformar_e_carregar_duckdb():
        print("Iniciando tarefa de limpeza e carga para DuckDB...")
        parquet_to_duckdb()
        print("Tarefa de carga no DuckDB concluída.")

    transformar_e_carregar_duckdb()

dag_processar_b3_para_duckdb()