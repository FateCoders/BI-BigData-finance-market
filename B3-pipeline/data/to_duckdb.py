import os
import duckdb
import pandas as pd
import pyarrow.parquet as pq
import unicodedata

parquet_path = "B3-pipeline/data/ibov_dados_brutos.parquet"
duckdb_path = "ibov_limpo.duckdb"

import pandas as pd
import duckdb
import pyarrow.parquet as pq
import os

def parquet_to_duckdb(parquet_file_path, duckdb_file_path='data.db', table_name='my_table', decimal_places=2):
    """
    Carrega um arquivo .parquet, limpa os dados (remove linhas com NaN em colunas numéricas, 
    formata colunas float64 para arredondar doubles), e insere em uma tabela DuckDB.
    
    :param parquet_file_path: Caminho para o arquivo .parquet
    :param duckdb_file_path: Caminho para o arquivo DuckDB (criado se não existir)
    :param table_name: Nome da tabela no DuckDB
    :param decimal_places: Número de casas decimais para arredondar doubles (padrão: 2)
    """
    
    print(f"Lendo arquivo Parquet: {parquet_file_path}")
    parquet_table = pq.read_table(parquet_file_path)
    df = parquet_table.to_pandas()
    
    print(f"DataFrame carregado com {df.shape[0]} linhas e {df.shape[1]} colunas.")
    
    numeric_cols = df.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns
    df.dropna(subset=numeric_cols, inplace=True)
    
    float_cols = df.select_dtypes(include=['float64', 'float32']).columns
    if len(float_cols) > 0:
        print(f"Formatando {len(float_cols)} colunas float para {decimal_places} casas decimais.")
        df[float_cols] = df[float_cols].round(decimal_places)
    
    df.drop_duplicates(inplace=True)
    
    print(f"Após limpeza: {df.shape[0]} linhas restantes.")
    
    con = duckdb.connect(database=duckdb_file_path, read_only=False)
    
    con.register('df_view', df)
    
    con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df_view;")
    
    
    con.close()
    
    print(f"Dados inseridos com sucesso na tabela '{table_name}' do banco DuckDB: {duckdb_file_path}")
    
    con = duckdb.connect(database=duckdb_file_path, read_only=True)
    result = con.execute(f"SELECT * FROM {table_name} LIMIT 5;").fetchdf()
    con.close()
    
    print("Amostra dos dados no DuckDB:")
    print(result)


parquet_to_duckdb(parquet_path, duckdb_path, table_name="ibov_limpo")