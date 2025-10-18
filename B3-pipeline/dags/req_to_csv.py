from airflow.decorators import dag, task
from datetime import datetime
import requests
import pandas as pd
import logging

@dag(
    dag_id="pipeline_sidra_ipca",
    description="Coleta IPCA (Tabela 1737) da API do SIDRA",
    start_date=datetime(2025, 10, 17),
    schedule=None,
    catchup=False
)
def pipeline_sidra_ipca_func():

    @task
    def extrair_salvar_dados_ipca():
        url = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/63/p/all"
        caminho_csv = "/opt/airflow/dags/ipca_1737.csv"

        try:
            logging.info(f"Acessando a API do SIDRA: {url}")
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            logging.info("Dados JSON recebidos com sucesso.")

            df = pd.DataFrame(data[1:])
            df.columns = data[0].values()
            
            df.to_csv(caminho_csv, index=False)
            
            logging.info(f"Gerou '{caminho_csv}' com sucesso!")
            return caminho_csv

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar a API: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro ao processar os dados: {e}")
            raise

    extrair_salvar_dados_ipca()

pipeline_sidra_ipca_func()
