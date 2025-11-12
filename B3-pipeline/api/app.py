import duckdb
import pandas as pd
from flask import Flask, Response, jsonify
import os

app = Flask(__name__)

DB_PATH = '/opt/airflow/data/ibov_limpo.duckdb'

@app.route('/api/ibov', methods=['GET'])
def get_ibov_data():
    """
    Endpoint principal que retorna todos os dados da tabela ibov_limpo.
    """
    if not os.path.exists(DB_PATH):
        return jsonify({"error": "Arquivo de dados não encontrado. O pipeline já rodou?"}), 404

    try:
        conn = duckdb.connect(database=DB_PATH, read_only=True)

        df = conn.query("SELECT * FROM ibov_limpo").df()
        conn.close()

        result = df.to_json(orient="records", date_format='iso')
        
        return Response(result, mimetype='application/json')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)