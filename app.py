from pathlib import Path
import pandas as pd
import streamlit as st
from analytics import DB_PATH, CSV_PATH, initialize_database, execute_readonly_query, ask_assistant

st.set_page_config(page_title="GenAI Analytics Assistant", page_icon="📊", layout="wide")
st.title("📊 GenAI-Powered Analytics Assistant")
st.caption("Explore a synthetic retail dataset with SQL-backed KPIs and an optional LangGraph-powered natural-language assistant.")

if not DB_PATH.exists() or DB_PATH.stat().st_mtime < CSV_PATH.stat().st_mtime:
    initialize_database()

summary = execute_readonly_query("SELECT COUNT(*) AS orders, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit, ROUND(AVG(revenue), 2) AS avg_order_value FROM retail_sales").iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Orders", f"{int(summary['orders']):,}")
c2.metric("Revenue", f"${summary['revenue']:,.2f}")
c3.metric("Profit", f"${summary['profit']:,.2f}")
c4.metric("Avg. order revenue", f"${summary['avg_order_value']:,.2f}")

left, right = st.columns([1, 1])
with left:
    st.subheader("Revenue by month")
    monthly = execute_readonly_query("SELECT substr(order_date, 1, 7) AS month, ROUND(SUM(revenue), 2) AS revenue FROM retail_sales GROUP BY month ORDER BY month")
    st.line_chart(monthly.set_index("month"))
with right:
    st.subheader("Revenue by category")
    categories = execute_readonly_query("SELECT category, ROUND(SUM(revenue), 2) AS revenue FROM retail_sales GROUP BY category ORDER BY revenue DESC")
    st.bar_chart(categories.set_index("category"))

st.divider()
st.subheader("Ask a business question")
st.write("Examples: *Show monthly sales trends*, *Compare revenue by region*, *Which products generate the most revenue?*, *How do discounts relate to profit?*")
with st.form("question_form"):
    question = st.text_input("Your question", placeholder="e.g. Compare sales performance by region")
    submitted = st.form_submit_button("Analyze", type="primary")
if submitted:
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Analyzing curated data..."):
            answer = ask_assistant(question.strip())
        st.caption(f"Execution mode: {answer.get('mode', 'Unknown')}")
        if answer.get("error"):
            st.error("The request could not be completed safely. Check the configuration or try a supported question.")
            with st.expander("Technical detail"):
                st.code(answer["error"])
        else:
            st.info(answer.get("explanation", "Results are ready."))
            st.dataframe(answer["result"], use_container_width=True, hide_index=True)
            with st.expander("View generated SQL"):
                st.code(answer["sql"], language="sql")
            if not answer["result"].empty:
                numeric = answer["result"].select_dtypes(include="number").columns.tolist()
                if len(answer["result"].columns) >= 2 and numeric:
                    st.subheader("Result visualization")
                    st.bar_chart(answer["result"].set_index(answer["result"].columns[0])[numeric[0]])

with st.expander("Dataset notes"):
    st.write("This project ships with synthetic retail transactions generated for demonstration. It does not represent a real company or real customer data.")
    st.write("Columns: order_id, order_date, region, sales_channel, category, product, quantity, unit_price, discount_pct, revenue, cost, profit.")
