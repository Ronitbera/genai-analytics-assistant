import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from analytics import validate_sql


def test_allows_select_from_curated_table():
    assert validate_sql("SELECT region FROM retail_sales;") == "SELECT region FROM retail_sales"


@pytest.mark.parametrize("sql", [
    "DELETE FROM retail_sales",
    "DROP TABLE retail_sales",
    "SELECT * FROM users",
    "SELECT * FROM retail_sales; SELECT * FROM retail_sales",
    "UPDATE retail_sales SET profit = 0",
])
def test_rejects_unsafe_sql(sql):
    with pytest.raises(ValueError):
        validate_sql(sql)
