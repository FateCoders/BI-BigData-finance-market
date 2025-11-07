import os
import duckdb
import pandas as pd
import pyarrow.parquet as pq
import unicodedata

parquet_path = "B3-pipeline/data/ibov_dados_brutos.parquet"
duckdb_path = "B3-pipeline/data/ibov_limpo.duckdb"
backup_parquet = "B3-pipeline/data/ibov_limpo_backup.parquet"


def normalizar_nome_coluna(nome):
    nome = nome.strip().lower()
    nome = "".join(
        c for c in unicodedata.normalize("NFD", nome)
        if unicodedata.category(c) != "Mn"
    )
    nome = nome.replace(" ", "_").replace("-", "_")
    return nome


def limpar_dataframe(df: pd.DataFrame):
    df.columns = [normalizar_nome_coluna(c) for c in df.columns]
    
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", ".", regex=False)
                    .str.replace(" ", "", regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors="ignore")
            except Exception:
                pass
    
    for col in df.columns.copy():
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            base = col
            df[f"{base}_ano"] = df[col].dt.year
            df[f"{base}_mes"] = df[col].dt.month
            df[f"{base}_dia"] = df[col].dt.day
            if not (df[col].dt.hour == 0).all():
                df[f"{base}_hora"] = df[col].dt.hour
            df = df.drop(columns=[col])
        else:
            try:
                temp = pd.to_datetime(df[col], errors="raise")
                if temp.notna().sum() > 0:
                    base = col
                    df[f"{base}_ano"] = temp.dt.year
                    df[f"{base}_mes"] = temp.dt.month
                    df[f"{base}_dia"] = temp.dt.day
                    if not (temp.dt.hour == 0).all():
                        df[f"{base}_hora"] = temp.dt.hour
                    df = df.drop(columns=[col])
            except Exception:
                pass
    df = df.dropna(axis=1, how="all")
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna("")
    
    return df


def salvar_duckdb(df, duckdb_path):
    if os.path.exists(duckdb_path):
        try:
            conn = duckdb.connect(duckdb_path)
            conn.close()
        except Exception:
            os.remove(duckdb_path)
            print("Banco corrompido removido e recriado.")
    conn = duckdb.connect(duckdb_path)
    conn.execute("CREATE OR REPLACE TABLE ibov_limpo AS SELECT * FROM df")
    conn.close()


table = pq.read_table(parquet_path)
df = table.to_pandas()
df = limpar_dataframe(df)

df.to_parquet(backup_parquet, index=False)
salvar_duckdb(df, duckdb_path)

print(f"Dados limpos e salvos em {duckdb_path}")
print(f"Backup salvo em {backup_parquet}")
