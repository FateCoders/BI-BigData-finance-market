import duckdb
import pandas as pd
from flask import Flask, Response, jsonify
import os

app = Flask(__name__)

# Caminho para o banco de dados do IBOV
DB_PATH_IBOV = '/opt/airflow/data/ibov_limpo.duckdb'
TABLE_NAME_IBOV = 'ibov_limpo'

# Caminhos para SELIC
DB_PATH_SELIC = '/opt/airflow/data/selic_limpo.duckdb'
TABLE_NAME_SELIC = 'selic_limpa'


@app.route('/api/ibov', methods=['GET'])
def get_ibov_data():
    """
    Endpoint que retorna todos os dados da tabela ibov_limpo.
    """
    if not os.path.exists(DB_PATH_IBOV):
        return jsonify({"error": "Arquivo de dados [IBOV] não encontrado. O pipeline já rodou?"}), 404

    try:
        # Conecta no banco do IBOV
        conn = duckdb.connect(database=DB_PATH_IBOV, read_only=True)
        df = conn.query(f"SELECT * FROM {TABLE_NAME_IBOV}").df()
        conn.close()

        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        result = df.to_json(orient="records")
        return Response(result, mimetype='application/json')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/selic', methods=['GET'])
def get_selic_data():
    """
    Endpoint que retorna todos os dados da tabela selic_limpa.
    """
    if not os.path.exists(DB_PATH_SELIC):
        return jsonify({"error": "Arquivo de dados [SELIC] não encontrado. O pipeline já rodou?"}), 404

    try:
        # Conecta no banco da SELIC (Este era o erro)
        conn = duckdb.connect(database=DB_PATH_SELIC, read_only=True)
        
        df = conn.query(f"SELECT * FROM {TABLE_NAME_SELIC}").df()
        conn.close()
        
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        result = df.to_json(orient="records")
        return Response(result, mimetype='application/json')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)