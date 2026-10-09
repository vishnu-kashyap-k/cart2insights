# importing all required import statements
import pandas as pd
import os
import streamlit as st
import sqlalchemy as sqla
import plotly.express as px
from dotenv import load_dotenv
from urllib.parse import quote_plus

# to load the .env file load_dotenv is used here
load_dotenv('.env')

# all the credentials loaded from the .env file
username=os.getenv('DB_USER')
pwd=os.getenv('DB_PASSWORD')
host=os.getenv('DB_HOST')
port=os.getenv('DB_PORT')
db= os.getenv('DB_NAME')

# quote_plus encodes the password so that any special characters in password can't break url
safe_pwd=quote_plus(pwd)

# connection url
url='mysql+pymysql://'+username+':'+safe_pwd+'@'+host+':'+port

db_con=sqla.create_engine(url+'/'+db)

# Sidebar navigation
st.sidebar.title('cart2insights')
option=st.sidebar.selectbox('select a section:',
                            ['Home','Business Overview','Sales Analysis','Customer Analysis','Seller & Product Analysis',
                             'Delivery Analysis','Customer Experience'])
# Sections
if option == "Home":
    st.title("Cart2Insights: Decoding E-Commerce Performance")
    st.markdown("""
    A dashboard analysing the **Olist Brazilian e-commerce dataset**
    (~99,000 orders, 2016- 2018), connected live to a MySQL database.

    Objective is to uncover business insights on sales, customers, sellers, delivery performance and customer satisfaction.""")

elif option=='Business Overview':
    st.title('Business Overview')
    # Q1. All KPIs
    q1="""select 
    (select sum(price) from order_items) as Total_revenue,
    (select count(*) from orders) as Total_orders,
    (select count(distinct customer_unique_id) from customers) as Total_customers,
    (select count(*) from sellers) as Total_sellers,
    (select sum(price)/count(distinct order_id) from order_items) as Avg_order_value,
    (select avg(review_score) from order_reviews) as Avg_order_reviews
    """
    kpi=pd.read_sql(q1,db_con)

    # First row of KPI cards
    col1,col2,col3=st.columns(3)
    col1.metric('Total Revenue', f"R$ {kpi['Total_revenue'][0]:,.0f}")
    col2.metric('Total Orders', f"{kpi['Total_orders'][0]:,}")
    col3.metric('Total Customers',f"{kpi['Total_customers'][0]:,}")

    # Second row of LPI cards
    col4,col5,col6=st.columns(3)
    col4.metric('Total Sellers',f"{kpi['Total_sellers'][0]:,}")
    col5.metric('Average order value',f"{kpi['Avg_order_value'][0]:,.2f}")
    col6.metric('Average order reviews',f"{kpi['Avg_order_reviews'][0]:,.2f}/5")


elif option=='Sales Analysis':
    st.title('Sales Analysis')
    tab1,tab2,tab3,tab4,tab5= st.tabs(
        ["Monthly Trend", "Top Categories", "Top Products", "By Location", "Payments"])
    with tab1:
        # Q2: Monthly revenue trend
        st.subheader("Monthly Revenue Trend")
        q2 = """
        select concat(extract(year from o.order_purchase_timestamp), '-',
                    lpad(extract(month from o.order_purchase_timestamp), 2, '0')) as month,
            sum(oi.price) as revenue
        from orders o
        join order_items oi on o.order_id = oi.order_id
        where o.order_purchase_timestamp >= '2017-01-01'
        and o.order_purchase_timestamp <  '2018-09-01'
        group by 1
        order by 1
        """
        monthly = pd.read_sql(q2, db_con)
        plot = px.line(monthly, x='month', y='revenue', markers=True,
                    title='Monthly Revenue')
        st.plotly_chart(plot)

    with tab2:
        # Q3. Which product categories generates the most revenue?
        st.subheader("Top 10 Categories by Revenue")
        q3 = """
        select coalesce(e.product_category_name_english, p.product_category_name) as category,
            sum(oi.price) as revenue
        from order_items oi
        join products p on oi.product_id = p.product_id
        left join category_translation e on p.product_category_name = e.product_category_name
        group by category
        order by revenue desc
        limit 10
        """
        cat_rev = pd.read_sql(q3, db_con)

        cat_rev_plot = px.bar(cat_rev, x='revenue', y='category', orientation='h',
                            title='Top 10 Categories by Revenue')
        cat_rev_plot.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(cat_rev_plot)

    with tab3:
        # Q4. Top 10 products by units sold
        st.subheader("Top 10 Products by Units Sold")
        q4 = """
        select oi.product_id,
            coalesce(e.product_category_name_english, p.product_category_name) as category,
            count(*) as units_sold,
            sum(oi.price) as revenue
        from order_items oi
        join products p on oi.product_id = p.product_id
        left join category_translation e on p.product_category_name = e.product_category_name
        group by 1,2
        order by 3 desc
        limit 10
        """
        top_products = pd.read_sql(q4, db_con)
        st.dataframe(top_products)

    with tab4:
        # Q5. Revenue by state
        st.subheader("Revenue by Customer State")
        q5a = """
        select c.customer_state as state,
            sum(oi.price) as revenue
        from order_items oi
        join orders o on oi.order_id = o.order_id
        join customers c on o.customer_id = c.customer_id
        group by c.customer_state
        order by revenue desc
        """
        state_rev = pd.read_sql(q5a, db_con)
        state_rev_plot = px.bar(state_rev, x='state', y='revenue', title='Revenue by Customer State')
        st.plotly_chart(state_rev_plot)

        # Q5. Top 10 cities by revenue
        st.subheader("Top 10 Cities by Revenue")
        q5b = """
        select c.customer_city as city,
            c.customer_state as state,
            sum(oi.price) as revenue
        from order_items oi
        join orders o on oi.order_id = o.order_id
        join customers c on o.customer_id = c.customer_id
        group by c.customer_city, c.customer_state
        order by revenue desc
        limit 10
        """
        city_rev = pd.read_sql(q5b, db_con)
        city_rev_plot = px.bar(city_rev, x='city', y='revenue', title='Top 10 Cities by Revenue')
        st.plotly_chart(city_rev_plot)

    with tab5:
        # Q6. Payment methods
        st.subheader("Payment Methods")
        q6 = """
        select payment_type,
            count(distinct order_id) as orders,
            avg(payment_value) as avg_payment_value
        from order_payments
        group by 1
        order by 2 desc
        """
        payments = pd.read_sql(q6, db_con)

        payments_plot_1 = px.pie(payments, names='payment_type', values='orders',
                    title='Share of Orders by Payment Type')
        st.plotly_chart(payments_plot_1)

        payment_plot_2 = px.bar(payments, x='payment_type', y='avg_payment_value',
                    title='Average Payment Value by Type')
        st.plotly_chart(payment_plot_2)

elif option=='Customer Analysis':
    st.title('Customer Analysis')
    tab1,tab2,tab3,tab4,tab5 = st.tabs(
        ["By State", "Repeat vs One-time", "Top Customers", "Delay vs Repeat", "Multi-year"])
    with tab1:
        # Q7. How are customers distributed across states?
        st.subheader("Customers by State")
        q7 = """
        select customer_state as state,
               count(distinct customer_unique_id) as customers
        from customers
        group by 1
        order by 2 desc
        """
        cust_state = pd.read_sql(q7, db_con)
        cust_state_plot = px.bar(cust_state, x='state', y='customers',
                                 title='Number of Unique Customers by State')
        st.plotly_chart(cust_state_plot)
    with tab2:
        # Q8. How many customers are repeat buyers vs one-time buyers?
        st.subheader("Repeat vs One-time Customers")
        q8 = """
        with customer_orders as (
            select c.customer_unique_id, count(o.order_id) as order_count
            from orders o
            join customers c on o.customer_id = c.customer_id
            group by 1
        )
        select case when order_count > 1 then 'Repeat' else 'One-time' end as customer_type, count(*) as customers
        from customer_orders
        group by 1
        """
        repeat = pd.read_sql(q8, db_con)
        repeat_plot = px.pie(repeat, names='customer_type', values='customers',
                     title='Repeat vs One-time Customers')
        st.plotly_chart(repeat_plot)

    with tab3:
        # Q9. Who are the top customers by total spending and by number of items purchased?
        st.subheader("Top 10 Customers by Spending")
        q9 = """
        with customer_spend as (
            select c.customer_unique_id,
                   sum(oi.price) as total_spent,
                   count(*) as items_bought
            from order_items oi
            join orders o on oi.order_id = o.order_id
            join customers c on o.customer_id = c.customer_id
            group by 1
        )
        select customer_unique_id,
               total_spent,
               rank() over (order by total_spent desc) as spend_rank,
               items_bought,
               rank() over (order by items_bought desc) as items_rank
        from customer_spend
        order by 3
        limit 10
        """
        top_customers = pd.read_sql(q9, db_con)
        st.dataframe(top_customers)

    with tab4:
        # Q10.Do customers who experienced a delivery delay place fewer repeat orders than those who did not?
        st.subheader("Late Delivery vs Repeat Purchases")
        q10 = """
        with customer_late as (
            select c.customer_unique_id,
                   max(case when f.delivery_delay > 0 then 1 else 0 end) as had_late
            from order_features f
            join customers c on f.customer_id = c.customer_id
            where f.delivery_delay is not null
            group by 1
        )
        select case when cl.had_late = 1 then 'Had a late order' else 'Never late' end as delivery_experience,
               count(*) as customers,
               round(avg(s.is_repeat) * 100, 2) as repeat_rate_pct
        from customer_late cl
        join customer_summary s on cl.customer_unique_id = s.customer_unique_id
        group by 1
        """

        delay_repeat = pd.read_sql(q10, db_con)
        st.dataframe(delay_repeat)

        delay_repeat_plot = px.bar(delay_repeat, x='delivery_experience', y='repeat_rate_pct',
                     title='Repeat Purchase Rate: Had a Late Order vs Never Late')
        st.plotly_chart(delay_repeat_plot)
        st.caption("Customers with more orders have more chances of a late delivery, "
                   "so this comparison can't show a clear effect of delays on repeat buying. ")
        
    with tab5:
        # Q.11 How many customers purchased in more than one year?
        st.subheader("Customers Who Purchased in More Than One Year")
        q11 = """
        select count(*) as multi_year_customers
        from (
            select c.customer_unique_id
            from orders o
            join customers c on o.customer_id = c.customer_id
            group by 1
            having count(distinct year(o.order_purchase_timestamp)) > 1
        ) as t
        """
        multi_year = pd.read_sql(q11, db_con)
        st.metric("Customers with orders in 2+ years", int(multi_year['multi_year_customers'][0]))

elif option=="Seller & Product Analysis":
    st.title("Seller & Product Analysis")
    tab1,tab2,tab3 = st.tabs(["Top Sellers", "Seller Ratings", "Category Ratings"])

    with tab1:
        # Q12. Top sellers by revenue 
        st.subheader("Top 10 Sellers by Revenue")
        q12 = """
        select seller_id, seller_revenue, seller_order_count
        from seller_summary
        order by 2 desc
        limit 10
        """
        top_sellers = pd.read_sql(q12, db_con)
        st.dataframe(top_sellers)

    with tab2:
        # Q13. Average rating per seller (sellers with at least 50 reviews)
        st.subheader("Seller Ratings (min 50 reviews)")
        q13 = """
        select oi.seller_id,
               count(*) as reviews,
               round(avg(r.review_score), 2) as avg_rating
        from order_items oi
        join order_reviews r on oi.order_id = r.order_id
        group by 1
        having count(*) >= 50
        order by 3
        """
        seller_ratings = pd.read_sql(q13, db_con)
        st.dataframe(seller_ratings)

    with tab3:
        # Q15. Best and worst categories by rating (min 100 reviews)
        st.subheader("Lowest Rated Categories (min 100 reviews)")
        q15 = """
        select coalesce(e.product_category_name_english, p.product_category_name) as category,
               count(*) as reviews,
               round(avg(r.review_score), 2) as avg_rating
        from order_items oi
        join products p on oi.product_id = p.product_id
        left join category_translation e on p.product_category_name = e.product_category_name
        join order_reviews r on oi.order_id = r.order_id
        group by 1
        having count(*) >= 100
        order by 3
        limit 10
        """
        cat_ratings = pd.read_sql(q15, db_con)
        cat_ratings_plot = px.bar(cat_ratings, x='avg_rating', y='category', orientation='h',
                                  title='10 Lowest Rated Categories')
        st.plotly_chart(cat_ratings_plot)

elif option=="Delivery Analysis":
    st.title("Delivery Analysis")
    tab1,tab2,tab3,tab4 = st.tabs(["Delivery Time", "On-time vs Late", "By State", "Delay vs Review"])

    with tab1:
        # Q16. Average delivery time
        q16 = "select avg(delivery_days) as avg_days from order_features"
        avg_days = pd.read_sql(q16, db_con)['avg_days'][0]
        st.metric("Average Delivery Time in days", round(float(avg_days), 1))

    with tab2:
        # Q17. On-time vs late
        q17 = """
        select case when delivery_delay> 0 then 'Late' else 'On-time' end as status,
               count(*) as orders
        from order_features
        where delivery_delay is not null
        group by 1
        """
        on_time_vs_late= pd.read_sql(q17, db_con)
        on_time_vs_late_plot = px.pie(on_time_vs_late, names='status', values='orders',
                     title='On-time vs Late Orders')
        st.plotly_chart(on_time_vs_late_plot)

    with tab3:
        # Q18. Delivery days by state
        q18 = """
        select c.customer_state as state, avg(f.delivery_days) as avg_days
        from order_features f
        join customers c on f.customer_id = c.customer_id
        group by 1
        order by 2
        """
        deliv_state= pd.read_sql(q18, db_con)
        deliv_state_plot = px.bar(deliv_state, x='state', y='avg_days',
                     title='Average Delivery Days by State')
        st.plotly_chart(deliv_state_plot)

    with tab4:
        # Q19. Delay vs review score
        q19 = """
        select case when f.delivery_delay> 0 then 'Late' else 'On-time' end as status,
               avg(r.review_score) as avg_review
        from order_features f
        join order_reviews r on f.order_id = r.order_id
        where f.delivery_delay is not null
        group by status
        """
        deliv_review=pd.read_sql(q19, db_con)
        deliv_review_plot = px.bar(deliv_review, x='status', y='avg_review',
                     title='Average Review: On-time vs Late')
        st.plotly_chart(deliv_review_plot)

elif option== "Customer Experience":
    st.title("Customer Experience")
    # Q20. Review score distribution
    q20 = """
    select review_score, count(*) as reviews
    from order_reviews
    group by 1
    order by 1
    """
    rev_score=pd.read_sql(q20, db_con)
    rev_score_plot = px.bar(rev_score, x='review_score', y='reviews',
                 title='Review Score Distribution')
    st.plotly_chart(rev_score_plot)