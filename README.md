# Cart2Insights: Decoding E-Commerce Performance

Data analysis of the Olist Brazilian e-commerce dataset (about 99,000 orders, 2016–2018) using Python, Pandas, MySQL and Streamlit.

## Objective
Analyse sales, customers, sellers, payments, delivery and reviews to find useful business insights.

## Approach
1. Understood the business problem and the 9 tables (data dictionary, ER diagram)
2. Checked data quality and cleaned the data with Pandas
3. Loaded the cleaned data into MySQL with primary and foreign keys
4. Created features: order value, delivery days, delivery delay, customer spending, repeat customer flag, seller revenue
5. Did EDA in Python (univariate, bivariate, multivariate, trend, correlation)
6. Answered business questions with SQL and built a Streamlit dashboard
7. Wrote insights and recommendations (`docs/insights.pdf`)

## Methodology
- **Cleaning:** fixed data types, dates and zip codes; filled missing categories; removed invalid payments
- **SQL:** joins, GROUP BY, HAVING, subqueries, CTEs, window functions, CASE WHEN
- **Dashboard:** 6 sections connected live to MySQL, credentials kept in `.env`

## Key Findings
1. Orders grew through 2017, with the highest month in November 2017 (Black Friday).
2. About 8% of orders are late. Late orders get about 2.5 stars vs 4.3 for on-time.
3. Only about 3% of customers order more than once.
4. SP has about 41% of orders and the fastest delivery.
5. Credit card is used in about 75% of orders.

## How to Run
1. `pip install -r requirements.txt`
2. Add a `.env` file with `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
3. Run notebooks 01 to 06 in order
4. `streamlit run streamlit/app.py`
