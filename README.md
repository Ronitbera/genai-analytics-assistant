# GenAI-Powered Analytics Assistant

A portfolio project for Data Analyst / BI roles. It combines business KPIs, SQL analysis, data validation, and an optional natural-language-to-SQL workflow.

## Features
- Streamlit dashboard with order count, revenue, profit, and average order revenue.
- Monthly revenue trend and category revenue charts.
- SQLite-backed analysis over a curated synthetic retail dataset.
- Natural-language question interface with a deterministic no-key demo mode.
- Optional LangChain + LangGraph workflow to generate SQL, validate it, execute it read-only, and return results.
- SQL guardrails, SQLite read-only mode, query authorizer, and tests for unsafe SQL.
- SQL examples for monthly trends, regional performance, and profit margins.

## Dataset
`data/retail_sales.csv` contains 800 synthetic retail transactions generated with a fixed random seed. It is illustrative data only, not real customer or company data.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The dashboard and common question examples work without an API key. For open-ended natural-language SQL generation, create a `.env` file based on `.env.example`, set `OPENAI_API_KEY`, and export those environment variables before launching Streamlit. Keep API keys private; never commit `.env`.

## Test the SQL guardrails
```bash
pytest -q
```

## Example questions
- Show monthly sales trends.
- Compare revenue by region.
- Which products generate the most revenue?
- How do discounts relate to profit?
- Which category has the highest profit margin?

## Architecture
1. **Data layer:** CSV → SQLite `retail_sales` table.
2. **Analytics layer:** SQL aggregations over curated columns.
3. **Assistant layer:** deterministic demo routing without a key; optional LangGraph workflow with SQL generation, validation/execution, and result explanation when configured.
4. **Presentation layer:** Streamlit KPI cards, charts, result tables, and expandable SQL.

## Limitations and responsible use
- This is a learning/portfolio demo, not a production decision system.
- SQL validation is defense-in-depth, not a substitute for infrastructure isolation or security review.
- LLM-generated results should be checked against the SQL and underlying data.
- The current dataset is synthetic and the default no-key assistant recognizes common question categories rather than arbitrary language.

## Resume wording (use only after you have run and verified it)
**GenAI-Powered Analytics Assistant** | Python, SQL, SQLite, Pandas, Streamlit, LangChain, LangGraph
- Built a SQL-backed analytics dashboard to track revenue, profit, order volume, and monthly/category performance from a curated retail dataset.
- Developed a natural-language analytics workflow with SQL validation and read-only execution to answer business questions using retrieved data.
- Added query guardrails and automated tests for unsafe SQL, improving the reliability of data access in the prototype.
