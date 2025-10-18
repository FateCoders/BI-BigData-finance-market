# 1. Importar as bibliotecas
from airflow.decorators import dag, task  # Ferramentas do Airflow
from datetime import datetime
import requests                          # Para acessar a API
import pandas as pd                      # Mais fácil para salvar CSV
import logging                           # Para registrar o que acontece

# 2. Definir a DAG (O "Pipeline" ou "Maestro")
@dag(
    dag_id="pipeline_sidra_ipca",             # Nome que vai aparecer na interface
    description="Coleta IPCA (Tabela 1737) da API do SIDRA",
    start_date=datetime(2025, 10, 17),        # Data de hoje
    schedule=None,                            # 'None' = Só vamos rodar manualmente
    catchup=False                             # Não rodar execuções passadas
)
def pipeline_sidra_ipca_func():
    """
    Função principal que define o pipeline.
    """

    # 3. Definir a Tarefa (O "Músico" ou "Script")
    @task
    def extrair_salvar_dados_ipca():
        """
        Esta é a tarefa que contém o SEU código.
        """
        url = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/63/p/all"
        caminho_csv = "/opt/airflow/dags/ipca_1737.csv"  # Caminho DENTRO do contêiner

        try:
            logging.info(f"Acessando a API do SIDRA: {url}")
            response = requests.get(url)
            response.raise_for_status()  # Gera um erro se a requisição falhar
            
            data = response.json()
            logging.info("Dados JSON recebidos com sucesso.")

            # 4. Usar Pandas para facilitar a conversão
            df = pd.DataFrame(data[1:])        # Carrega os dados
            df.columns = data[0].values()      # Define os nomes das colunas
            
            # 5. Salvar o CSV
            df.to_csv(caminho_csv, index=False)
            
            logging.info(f"Gerou '{caminho_csv}' com sucesso!")
            return caminho_csv

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar a API: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro ao processar os dados: {e}")
            raise

    # 6. Chamar a função da tarefa para ela existir no pipeline
    extrair_salvar_dados_ipca()

# 7. "Instanciar" a DAG (comando final para o Airflow ler)
pipeline_sidra_ipca_func()
