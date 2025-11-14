import duckdb

conn = duckdb.connect("../data/selic_limpo.duckdb")

print(conn.execute("SHOW TABLES").fetchdf())

print(conn.execute("SELECT * FROM selic_limpa LIMIT 10").fetchdf())

print(conn.execute("DESCRIBE selic_limpa").fetchdf())

conn.close()
