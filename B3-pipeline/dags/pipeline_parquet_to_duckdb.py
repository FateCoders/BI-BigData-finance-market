from airflow.decorators import dag, task
from datetime import datetime

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

@dag(
    dag_id="pipeline_parquet_to_duckdb",
    description="Limpa o Parquet bruto do IBOV e carrega em uma tabela DuckDB.",
    start_date=datetime(2023, 1, 1),
    schedule=None,
    catchup=False,
    tags=['b3', 'duckdb', 'parquet', 'etl']
)
def dag_processar_b3_para_duckdb():
    """
    ### Pipeline de Processamento B3

    Esta DAG é responsável por:
    1.  Ler o arquivo Parquet `ibov_dados_brutos.parquet` da pasta `data/`.
    2.  Limpar os dados (remover NaNs, arredondar floats, remover duplicatas).
    3.  Salvar o resultado na tabela `ibov_limpo` dentro do banco DuckDB `ibov_limpo.duckdb`,
        também na pasta `data/`.
    """

    @task
    def transformar_e_carregar_duckdb():
        """
        Executa a função de limpeza e carga do Parquet para o DuckDB.
        Os caminhos dos arquivos já estão configurados dentro da função importada
        para usar o volume /opt/airflow/data.
        """
        print("Iniciando tarefa de limpeza e carga para DuckDB...")
        parquet_to_duckdb()
        print("Tarefa de carga no DuckDB concluída.")

    transformar_e_carregar_duckdb()

dag_processar_b3_para_duckdb()