from app import app, server
from data import load_all_data
from layout import create_layout
from callbacks import register_callbacks


def main():

    data_cache = load_all_data()

    app.layout = create_layout(data_cache["lista_ativos"])

    register_callbacks(app, data_cache)

    print("\nServidor rodando em http://127.0.0.1:8050/")
    app.run(debug=True)


if __name__ == "__main__":
    main()
