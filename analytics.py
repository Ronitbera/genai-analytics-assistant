from __future__ import annotations
import os
import re
import sqlite3
from pathlib import Path
from typing import TypedDict, Any
import pandas as pd

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "retail_sales.csv"
DB_PATH = ROOT / "data" / "retail_sales.db"
ALLOWED_TABLE = "retail_sales"
FORBIDDEN_SQL = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|load_extension)\b", re.I)


def initialize_database() -> None:
    """Create the local demo database from the included synthetic CSV."""
    df = pd.read_csv(CSV_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(ALLOWED_TABLE, conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON retail_sales(order_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_region ON retail_sales(region)")


def validate_sql(sql: str) -> str:
    """Allow a single read-only SELECT over the curated retail_sales table."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise ValueError("No SQL query was generated.")
    if ";" in cleaned:
        raise ValueError("Only one SQL statement is allowed.")
    if not re.match(r"^select\b", cleaned, re.I):
        raise ValueError("Only SELECT queries are allowed.")
    if FORBIDDEN_SQL.search(cleaned):
        raise ValueError("The query contains a restricted SQL operation.")
    # The demo exposes exactly one table; reject other table references.
    refs = re.findall(r"\b(?:from|join)\s+([\w.]+)", cleaned, re.I)
    if not refs or any(ref.lower().split(".")[-1] != ALLOWED_TABLE for ref in refs):
        raise ValueError("Queries may reference only the retail_sales table.")
    return cleaned


def execute_readonly_query(sql: str) -> pd.DataFrame:
    safe_sql = validate_sql(sql)
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as conn:
        conn.set_authorizer(_read_only_authorizer)
        return pd.read_sql_query(safe_sql, conn)


def _read_only_authorizer(action, arg1, arg2, db_name, trigger_name):
    # SQLite authorizer: deny writes and schema changes even if validation misses one.
    write_actions = {
        sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_CREATE_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_INDEX, sqlite3.SQLITE_CREATE_TEMP_TABLE,
        sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
    }
    return sqlite3.SQLITE_DENY if action in write_actions else sqlite3.SQLITE_OK


def fallback_query(question: str) -> tuple[str, str]:
    """Useful no-API-key demo path for common business questions."""
    q = question.lower()
    if any(x in q for x in ["monthly", "month by month", "trend", "over time"]):
        sql = "SELECT substr(order_date, 1, 7) AS month, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit FROM retail_sales GROUP BY month ORDER BY month"
        explanation = "Monthly revenue and profit trend."
    elif "region" in q or "regional" in q or "state" in q:
        sql = "SELECT region, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit, SUM(quantity) AS units_sold FROM retail_sales GROUP BY region ORDER BY revenue DESC"
        explanation = "Sales performance grouped by region."
    elif "channel" in q or "online" in q or "marketplace" in q or "store" in q:
        sql = "SELECT sales_channel, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit, COUNT(*) AS orders FROM retail_sales GROUP BY sales_channel ORDER BY revenue DESC"
        explanation = "Performance grouped by sales channel."
    elif "category" in q or "product" in q or "best seller" in q or "top selling" in q:
        sql = "SELECT category, product, SUM(quantity) AS units_sold, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit FROM retail_sales GROUP BY category, product ORDER BY revenue DESC LIMIT 10"
        explanation = "Top 10 products by revenue."
    elif "discount" in q:
        sql = "SELECT discount_pct, COUNT(*) AS orders, ROUND(AVG(revenue), 2) AS avg_order_revenue, ROUND(SUM(profit), 2) AS total_profit FROM retail_sales GROUP BY discount_pct ORDER BY discount_pct"
        explanation = "Revenue and profit by discount level."
    elif "profit" in q or "margin" in q:
        sql = "SELECT category, ROUND(SUM(profit), 2) AS profit, ROUND(100.0 * SUM(profit) / NULLIF(SUM(revenue), 0), 2) AS profit_margin_pct FROM retail_sales GROUP BY category ORDER BY profit DESC"
        explanation = "Profit and profit margin by category."
    else:
        sql = "SELECT COUNT(*) AS orders, ROUND(SUM(revenue), 2) AS total_revenue, ROUND(SUM(profit), 2) AS total_profit, ROUND(AVG(revenue), 2) AS avg_order_revenue FROM retail_sales"
        explanation = "Overall sales summary. Try asking about monthly trends, regions, channels, products, discounts, or profit."
    return sql, explanation


class AssistantState(TypedDict, total=False):
    question: str
    sql: str
    result: Any
    explanation: str
    error: str


def ask_assistant(question: str) -> dict:
    """Use LangGraph + an LLM when configured; otherwise use the deterministic demo path."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sql, explanation = fallback_query(question)
        try:
            return {"sql": sql, "result": execute_readonly_query(sql), "explanation": explanation, "mode": "Demo mode (no API key)"}
        except Exception as exc:
            return {"sql": sql, "result": pd.DataFrame(), "explanation": explanation, "error": str(exc), "mode": "Demo mode (no API key)"}

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from langgraph.graph import StateGraph, END

        def generate(state: AssistantState) -> AssistantState:
            llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
            prompt = f"""You are a careful data analyst. Generate exactly one SQLite SELECT query for the user's business question.
Only use table retail_sales and columns: order_id, order_date, region, sales_channel, category, product, quantity, unit_price, discount_pct, revenue, cost, profit.
Use SQLite syntax. Never modify data. Do not use markdown or explanations; output SQL only.
Question: {state['question']}"""
            response = llm.invoke([SystemMessage(content="Return one safe read-only SQL SELECT query."), HumanMessage(content=prompt)])
            sql = str(response.content).strip().replace("```sql", "").replace("```", "").strip()
            return {"sql": sql}

        def validate_and_execute(state: AssistantState) -> AssistantState:
            sql = validate_sql(state["sql"])
            result = execute_readonly_query(sql)
            return {"sql": sql, "result": result}

        def summarize(state: AssistantState) -> AssistantState:
            result = state["result"]
            if result.empty:
                explanation = "The query returned no rows for this question."
            else:
                explanation = f"The query returned {len(result)} row(s). Review the result table below; figures are calculated from the curated dataset."
            return {"explanation": explanation}

        graph = StateGraph(AssistantState)
        graph.add_node("generate_sql", generate)
        graph.add_node("validate_execute", validate_and_execute)
        graph.add_node("summarize", summarize)
        graph.set_entry_point("generate_sql")
        graph.add_edge("generate_sql", "validate_execute")
        graph.add_edge("validate_execute", "summarize")
        graph.add_edge("summarize", END)
        output = graph.compile().invoke({"question": question})
        return {**output, "mode": "LLM + LangGraph"}
    except Exception as exc:
        # Fail closed: do not silently execute a fallback query after an LLM/security error.
        return {"sql": "", "result": pd.DataFrame(), "explanation": "The assistant could not safely answer this question.", "error": str(exc), "mode": "LLM workflow error"}
