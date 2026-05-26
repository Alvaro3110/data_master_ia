import duckdb
conn = duckdb.connect()
conn.execute("CREATE TABLE fact AS SELECT * FROM read_json_auto('../../data/seeds/pricing_snapshot.json')")
print(conn.execute("SELECT count(*) FROM fact").fetchall())
