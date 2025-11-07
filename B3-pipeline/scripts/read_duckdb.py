import duckdb

conn = duckdb.connect("../data/ibov_limpo.duckdb")

print(conn.execute("SHOW TABLES").fetchdf())

print(conn.execute("SELECT * FROM ibov_limpo LIMIT 10").fetchdf())

print(conn.execute("DESCRIBE ibov_limpo").fetchdf())

conn.close()
