-- 1. Monthly revenue and profit trend
SELECT substr(order_date, 1, 7) AS month,
       ROUND(SUM(revenue), 2) AS revenue,
       ROUND(SUM(profit), 2) AS profit
FROM retail_sales
GROUP BY month
ORDER BY month;

-- 2. Regional performance
SELECT region,
       ROUND(SUM(revenue), 2) AS revenue,
       ROUND(SUM(profit), 2) AS profit,
       SUM(quantity) AS units_sold
FROM retail_sales
GROUP BY region
ORDER BY revenue DESC;

-- 3. Profit margin by category
SELECT category,
       ROUND(SUM(profit), 2) AS profit,
       ROUND(100.0 * SUM(profit) / NULLIF(SUM(revenue), 0), 2) AS profit_margin_pct
FROM retail_sales
GROUP BY category
ORDER BY profit DESC;
