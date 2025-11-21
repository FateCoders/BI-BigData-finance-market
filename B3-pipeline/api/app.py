import duckdb
import pandas as pd
from flask import Flask, Response, jsonify
import os
import glob
import re

app = Flask(__name__)

PASTA_DADOS = '/opt/airflow/data'

def get_db_connection(db_path):
    return duckdb.connect(database=db_path, read_only=True)

@app.route('/api/tickers', methods=['GET'])
def list_tickers():
    """
    Lista todos os tickers/tabelas disponíveis baseados nos arquivos .duckdb encontrados.
    """
    if not os.path.exists(PASTA_DADOS):
        return jsonify({"error": "Pasta de dados não encontrada."}), 404

    # Procura arquivos *_limpo.duckdb
    arquivos = glob.glob(os.path.join(PASTA_DADOS, '*_limpo.duckdb'))
    
    disponiveis = []
    for arq in arquivos:
        basename = os.path.basename(arq)
        # Remove '_limpo.duckdb' para pegar o nome limpo do ticker
        nome_ticker = basename.replace('_limpo.duckdb', '')
        disponiveis.append({
            "ticker_id": nome_ticker,
            "endpoint": f"/api/ticker/{nome_ticker}"
        })
    
    return jsonify({"tickers_disponiveis": disponiveis})

@app.route('/api/ticker/<ticker_id>', methods=['GET'])
def get_ticker_data(ticker_id):
    """
    Endpoint dinâmico. 
    Acessar /api/ticker/petr4_sa retorna os dados de PETR4.
    Acessar /api/ticker/vale3_sa retorna os dados de VALE3.
    """
    # Validação de segurança básica para o nome do arquivo
    if not re.match(r'^[a-z0-9_]+$', ticker_id):
        return jsonify({"error": "ID do ticker inválido."}), 400

    nome_banco = f"{ticker_id}_limpo.duckdb"
    caminho_banco = os.path.join(PASTA_DADOS, nome_banco)
    nome_tabela = f"{ticker_id}_limpo"

    if not os.path.exists(caminho_banco):
        return jsonify({"error": f"Dados para '{ticker_id}' não encontrados. Verifique se o pipeline rodou."}), 404

    try:
        conn = get_db_connection(caminho_banco)
        
        # Tenta selecionar todos os dados
        # Usamos exceção caso a tabela tenha um nome diferente do esperado, mas seguimos o padrão do pipeline
        query = f"SELECT * FROM {nome_tabela}"
        df = conn.query(query).df()
        conn.close()

        # Formatação de Datas (procura por colunas comuns de data)
        cols_data = [col for col in df.columns if 'date' in col.lower() or 'data' in col.lower()]
        for col in cols_data:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        result = df.to_json(orient="records")
        return Response(result, mimetype='application/json')

    except Exception as e:
        return jsonify({"error": f"Erro interno ao ler banco de dados: {str(e)}"}), 500

# Mantendo compatibilidade com endpoints antigos (Opcional)
@app.route('/api/selic', methods=['GET'])
def get_selic_legacy():
    return get_ticker_data('selic')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)