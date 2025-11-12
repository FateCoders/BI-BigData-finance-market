# Projeto 3A: Pipeline de Dados da B3 com Airflow e DuckDB

## 1. Descrição do Projeto

Este projeto faz parte da iniciativa **Engenharia de Big Data: Projeto 3A**.  
O objetivo é construir um pipeline de dados gratuito para captura, processamento e armazenamento de informações financeiras da **B3**.

O pipeline utiliza **Apache Airflow** para orquestração, **Docker** para execução containerizada e **DuckDB** como sistema de armazenamento analítico local.

---

## 2. Tecnologias Utilizadas

- **Orquestração:** Apache Airflow
- **Ambiente de Execução:** Docker e Docker Compose
- **Fonte de Dados:** API yfinance (Yahoo Finance), obtendo dados do índice IBOVESPA (^BVSP)
- **Processamento (ETL):** Python com Pandas e yfinance
- **Armazenamento de Staging:** Parquet
- **Armazenamento Analítico:** DuckDB

---

## 3. Arquitetura e Funcionamento do Ambiente

O ambiente é containerizado com **Docker Compose**, permitindo isolamento e reprodutibilidade.  
Os componentes principais do Airflow são definidos no arquivo `docker-compose.yaml`.

### 3.1. Serviços do Docker

- **airflow-scheduler:** Monitora e executa DAGs conforme o agendamento.
- **airflow-webserver:** Fornece a interface de usuário (UI) em [http://localhost:8080](http://localhost:8080).
- **airflow-worker:** Executa as tarefas definidas nas DAGs.
- **airflow-init:** Serviço de inicialização para preparar o banco de dados e as configurações iniciais.
- **postgres:** Armazena os metadados do Airflow (DAGs, execuções e conexões).
- **redis:** Atua como message broker entre os serviços.

### 3.2. Mapeamento de Volumes

Os volumes mapeiam diretórios locais para os containers do Airflow:

- `./dags`: Contém os arquivos Python das DAGs.
- `./plugins`: Contém módulos auxiliares, como `b3_processing.py`.
- `./data`: Armazena os arquivos Parquet e o banco DuckDB.
- `./logs`: Armazena os registros de execução das tarefas.

---

## 4. Workflow do Pipeline (DAGs)

O pipeline é composto por duas DAGs integradas por **Datasets**.  
A segunda DAG é acionada automaticamente após a primeira concluir sua execução com sucesso.

### 4.1. DAG 1 — `pipeline_yfinance_to_parquet`

- **Função:** Extrai dados históricos do IBOVESPA (^BVSP) por meio da API do Yahoo Finance.
- **Arquivo:** `dags/pipeline_yfinance_to_parquet.py`
- **Agendamento:** `@daily`
- **Saída:** `Dataset("file:///opt/airflow/data/ibov_dados_brutos.parquet")`
- **Configuração de Resiliência:** `retries=2`, `retry_delay=timedelta(minutes=5)`

### 4.2. DAG 2 — `pipeline_parquet_to_duckdb`

- **Função:** Lê o arquivo Parquet bruto, realiza limpeza (remoção de valores nulos, arredondamento e deduplicação) e insere os dados tratados no DuckDB.
- **Arquivo:** `dags/pipeline_parquet_to_duckdb.py`
- **Agendamento:** `schedule=[raw_parquet_dataset]` (acionamento automático)
- **Saída:** Tabela `ibov_limpo` dentro de `data/ibov_limpo.duckdb`
- **Configuração de Resiliência:** `retries=2`

---

## 5. Execução do Ambiente e do Pipeline

### 5.1. Inicialização do Banco de Dados do Airflow

O comando abaixo realiza o download das imagens necessárias e inicializa o banco de dados do Airflow em um container:

```bash
docker-compose up airflow-init
```

### 5.2. Inicialização dos Serviços do Airflow

Para iniciar todos os serviços (webserver, scheduler, banco de dados):

```bash
docker-compose up -d
```

Os containers ativos podem ser verificados no **Docker Desktop** ou via terminal.

### 5.3. Acesso à Interface Web do Airflow

Acesse [http://localhost:8080](http://localhost:8080) para abrir a interface web.  
As credenciais padrão são:

- **Login:** `admin`
- **Senha:** `admin`

Caso as credenciais estejam incorretas, utilize o comando abaixo para criar o usuário administrador:

```bash
docker-compose exec airflow-scheduler airflow users create -r Admin -u admin -e admin@example.com -f admin -l user -p admin
```

### 5.4. Execução das DAGs

1. Localize as DAGs `pipeline_yfinance_to_parquet` e `pipeline_parquet_to_duckdb` na interface.
2. Ative ambas utilizando o botão **Toggle**.
3. Para execução manual, clique em **Play → Trigger DAG**.
4. Acompanhe a execução pela aba **Grid**.

Após a conclusão da DAG 1, a DAG 2 é acionada automaticamente via dependência de Dataset.

---

## 6. Verificação dos Dados

Os dados processados são gravados no banco **DuckDB**.  
Para leitura, utilize o script:

```bash
# A partir da raiz do projeto B3-pipeline
python scripts/read_duckdb.py
```

Arquivos gerados na pasta `data/`:

- `ibov_dados_brutos.parquet`
- `ibov_limpo.duckdb`
