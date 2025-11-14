from airflow.decorators import dag, task
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
import requests

selic_parquet_dataset = Dataset("file:///opt/airflow/data/selic_dados_brutos.parquet")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# --- INÍCIO DA CORREÇÃO ---

def construir_url_selic():
    """
    Cria a URL da API do BCB para buscar a SELIC
    do último ano até a data atual.
    """
    # Pega a data de hoje
    data_hoje = datetime.now()
    # Pega a data de 365 dias atrás
    data_um_ano_atras = data_hoje - timedelta(days=1825)
    
    # Formata as datas no padrão DD/MM/AAAA que a API do BCB exige
    data_final_str = data_hoje.strftime('%d/%m/%Y')
    data_inicial_str = data_um_ano_atras.strftime('%d/%m/%Y')

    # Retorna a URL formatada com o intervalo de datas
    return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={data_inicial_str}&dataFinal={data_final_str}"

# --- FIM DA CORREÇÃO ---


@dag(
    dag_id="pipeline_selic_to_parquet",
    description="Coleta dados da SELIC (BCB) e salva em Parquet.",
    start_date=datetime(2023, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args
)
def pipeline_bcb_selic_func():

    @task(outlets=[selic_parquet_dataset])
    def extrair_dados_selic_e_salvar_parquet():
        pasta_dados = "/opt/airflow/data"
        nome_arquivo = "selic_dados_brutos.parquet"
        caminho_parquet = os.path.join(pasta_dados, nome_arquivo)

        os.makedirs(pasta_dados, exist_ok=True)

        try:
            # Chama a função para construir a URL correta <<<<< CORREÇÃO
            BCB_API_URL = construir_url_selic()
            
            logging.info(f"Buscando dados da SELIC em: {BCB_API_URL}")
            response = requests.get(BCB_API_URL)
            response.raise_for_status()
            
            dados = response.json()
            
            if not dados:
                logging.warning("API do BCB não retornou dados.")
                return None

            df = pd.DataFrame(dados)
            df = df.rename(columns={'data': 'Date', 'valor': 'Value'})
            df = df[['Date', 'Value']]
            
            df.to_parquet(caminho_parquet, index=False)
            
            logging.info(f"Gerou '{caminho_parquet}' com sucesso! {len(df)} linhas salvas.")
            return caminho_parquet

        except Exception as e:
            logging.error(f"Erro ao processar dados da SELIC: {e}")
            raise

    extrair_dados_selic_e_salvar_parquet()

pipeline_bcb_selic_func()