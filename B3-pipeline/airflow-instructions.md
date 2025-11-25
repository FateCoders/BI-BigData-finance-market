# Projeto 3A: Pipeline de Dados da B3 com Airflow e DuckDB

## 1. Descrição do Projeto
Este projeto tem como objetivo construir um pipeline para captura, processamento e armazenamento de dados financeiros da B3

---

## 2. Tecnologias Utilizadas

| Camada               | Tecnologia                     | Finalidade                                      |
|----------------------|--------------------------------|-------------------------------------------------|
| Orquestração         | Apache Airflow                 | Agendamento e monitoramento de workflows       |
| Ambiente             | Docker + Docker Compose        | Containerização e reprodutibilidade             |
| Fonte de Dados       | yfinance (Yahoo Finance)       | Extração de cotações do ^BVSP                   |
| Processamento (ETL)  | Python + Pandas                | Transformação dos dados                         |
| Staging              | Arquivos Parquet               | Armazenamento intermediário eficiente           |
| Armazenamento OLAP   | DuckDB                         | Banco analítico local (arquivo .duckdb)         |

---

## 3. Arquitetura do Ambiente (Docker Compose)

| Serviço              | Função                                                                 |
|----------------------|------------------------------------------------------------------------|
| `airflow-scheduler`  | Monitora e dispara as DAGs conforme o schedule                         |
| `airflow-webserver`  | Interface web → [http://localhost:8080](http://localhost:8080)         |
| `airflow-worker`     | Executa as tarefas das DAGs                                            |
| `airflow-init`       | Inicializa o metadata DB e cria usuário admin                          |
| `postgres`           | Banco de metadados do Airflow                                          |
| `redis`              | Message broker (CeleryExecutor)                                        |

### Volumes mapeados (importante para persistência)
```text
./dags      → /opt/airflow/dags
./plugins   → /opt/airflow/plugins
./data      → /opt/airflow/data      ← arquivos Parquet + DuckDB
./logs      → /opt/airflow/logs
```

---

## 4. Workflow do Pipeline (DAGs com Datasets)

O pipeline possui duas DAGs encadeadas automaticamente via Airflow Datasets.

### 4.1 DAG 1 – `pipeline_yfinance_to_parquet`
- **Arquivo:** `dags/pipeline_yfinance_to_parquet.py`
- **Agendamento:** `@daily` (executa todo dia às 00:00)
- **Tarefa principal:** baixar dados históricos do ^BVSP via yfinance
- **Saída:** `data/ibov_dados_brutos.parquet`
- **Dataset produzido:**  
  `Dataset("file:///opt/airflow/data/ibov_dados_brutos.parquet")`
- **Resiliência:** 2 retentativas, delay de 5 minutos

### 4.2 DAG 2 – `pipeline_parquet_to_duckdb`
- **Arquivo:** `dags/pipeline_parquet_to_duckdb.py`
- **Agendamento:** `schedule=[raw_parquet_dataset]` → **acionada automaticamente** quando o Parquet é gerado
- **Transformações realizadas:**
  - Remoção de linhas com valores nulos nas colunas principais
  - Arredondamento dos preços para 2 casas decimais
  - Deduplicação por data
  - Ordenação cronológica
- **Saída final:** tabela `ibov_limpo` no arquivo `data/ibov_limpo.duckdb`
- **Resiliência:** 2 retentativas

---

## 5. Como Rodar o Ambiente

### 5.1 Passo 1 – Inicializar o banco de metadados do Airflow
```bash
docker compose up airflow-init
```

### 5.2 Passo 2 – Subir todos os serviços em background
```bash
docker compose up -d
```

### 5.3 Passo 3 – Acessar a UI do Airflow
URL: [http://localhost:8080](http://localhost:8080)  
Credenciais padrão:
- **Usuário:** `admin`
- **Senha:** `admin`

Caso precise recriar o usuário admin:
```bash
docker compose exec airflow-scheduler airflow users create \
    -r Admin -u admin -e admin@example.com -f Admin -l User -p admin
```

### 5.4 Passo 4 – Executar o pipeline
1. Na UI, ative (toggle ON) as duas DAGs:
   - `pipeline_yfinance_to_parquet`
   - `pipeline_parquet_to_duckdb`
2. Dispare manualmente a primeira DAG
3. A segunda DAG será acionada automaticamente assim que o Parquet for gerado

---

## 6. Verificação dos Dados Gerados

Arquivos criados na pasta `./data`:
- `ibov_dados_brutos.parquet` → staging bruto
- `ibov_limpo.duckdb`         → banco analítico final

Para visualizar o conteúdo do DuckDB rapidamente:
```bash
python scripts/read_duckdb.py
```

Exemplo de consulta direta via terminal:
```sql
duckdb data/ibov_limpo.duckdb "SELECT * FROM ibov_limpo ORDER BY date DESC LIMIT 10"
```

---

## 7. API REST (FastAPI) – Consulta dos Dados Tratados

| Endpoint                     | Descrição                                                                 | Exemplo de retorno |
|------------------------------|---------------------------------------------------------------------------|--------------------|
| `GET /api/tickers`           | Lista todos os arquivos `*limpo.duckdb` disponíveis                       | `{"tickers": ["ibov", "selic", ...]}` |
| `GET /api/ticker/<ticker_id>`| Retorna todo o conteúdo da tabela `<ticker_id>_limpo` em JSON             | Dados históricos completos |
| `GET /api/selic`             | Endpoint legado → redireciona internamente para `/api/ticker/selic`      | Mantém compatibilidade com sistemas antigos |
