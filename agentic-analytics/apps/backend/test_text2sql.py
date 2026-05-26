import sys
sys.path.append(".")
from app.agent.text2sql_agent import _run_with_duckdb
try:
    sql, result, masked = _run_with_duckdb("Qual foi a margem da última safra no segmento Varejo?", "")
    print(f"SQL: {sql}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
