import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime, date, timedelta
import io
import os

# Try to import google-generativeai safely
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ==========================================
# 1. PAGE CONFIGURATION & THEME STYLING
# ==========================================
st.set_page_config(
    page_title="AI Personal Finance Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for fintech dark/light balanced theme
custom_css = """
<style>
/* Font and general styles */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stSidebar"] {
    font-family: 'Outfit', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
}

/* Custom dashboard cards */
.metric-card {
    background-color: #1e293b;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #334155;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    margin-bottom: 15px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: #4f46e5;
}
.metric-title {
    color: #94a3b8;
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}
.metric-value {
    color: #f8fafc;
    font-size: 32px;
    font-weight: 700;
    margin: 0;
}
.metric-subtitle {
    color: #64748b;
    font-size: 12px;
    margin-top: 6px;
    margin-bottom: 0;
}

/* Alert styles */
.warning-box {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid #ef4444;
    color: #fca5a5;
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 15px;
}
.success-box {
    background-color: rgba(34, 197, 94, 0.1);
    border: 1px solid #22c55e;
    color: #86efac;
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 15px;
}
.info-box {
    background-color: rgba(99, 102, 241, 0.1);
    border: 1px solid #6366f1;
    color: #c7d2fe;
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 15px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Helper function to generate clean custom cards
def render_kpi_card(title, value, subtitle, border_color="#334155"):
    card_html = f"""
    <div class="metric-card" style="border-left: 5px solid {border_color};">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ==========================================
# 2. DUMMY DATA & STATE INITIALIZATION
# ==========================================
def get_initial_dummy_data():
    today = date.today()
    # Create spanning data for last 3 months
    d1 = today - timedelta(days=75)
    d2 = today - timedelta(days=45)
    d3 = today - timedelta(days=15)
    
    data = [
        # April (2 months ago)
        {"Date": d1.replace(day=1), "Amount": 5500.0, "Type": "Income", "Category": "Salary", "Description": "Monthly Corporate Salary"},
        {"Date": d1.replace(day=12), "Amount": 750.0, "Type": "Income", "Category": "Freelance/Side Hustle", "Description": "Web Consulting Project"},
        {"Date": d1.replace(day=2), "Amount": 1250.0, "Type": "Expense", "Category": "Housing", "Description": "Rent Payment"},
        {"Date": d1.replace(day=5), "Amount": 180.0, "Type": "Expense", "Category": "Food & Dining", "Description": "Weekly Groceries"},
        {"Date": d1.replace(day=8), "Amount": 120.0, "Type": "Expense", "Category": "Utilities", "Description": "Power & Water"},
        {"Date": d1.replace(day=15), "Amount": 200.0, "Type": "Expense", "Category": "Transportation", "Description": "Monthly Transit Pass"},
        {"Date": d1.replace(day=20), "Amount": 85.0, "Type": "Expense", "Category": "Entertainment", "Description": "Cinema & Dining"},
        {"Date": d1.replace(day=25), "Amount": 150.0, "Type": "Expense", "Category": "Shopping", "Description": "Winter Apparel"},

        # May (1 month ago)
        {"Date": d2.replace(day=1), "Amount": 5500.0, "Type": "Income", "Category": "Salary", "Description": "Monthly Corporate Salary"},
        {"Date": d2.replace(day=15), "Amount": 920.0, "Type": "Income", "Category": "Freelance/Side Hustle", "Description": "App UX Design Contract"},
        {"Date": d2.replace(day=20), "Amount": 100.0, "Type": "Income", "Category": "Investments", "Description": "Quarterly Dividends"},
        {"Date": d2.replace(day=2), "Amount": 1250.0, "Type": "Expense", "Category": "Housing", "Description": "Rent Payment"},
        {"Date": d2.replace(day=6), "Amount": 210.0, "Type": "Expense", "Category": "Food & Dining", "Description": "Supermarket Purchase"},
        {"Date": d2.replace(day=9), "Amount": 135.0, "Type": "Expense", "Category": "Utilities", "Description": "Gas & Internet Bill"},
        {"Date": d2.replace(day=14), "Amount": 75.0, "Type": "Expense", "Category": "Health & Fitness", "Description": "Gym Membership"},
        {"Date": d2.replace(day=22), "Amount": 190.0, "Type": "Expense", "Category": "Entertainment", "Description": "Live Concert Tickets"},
        {"Date": d2.replace(day=26), "Amount": 300.0, "Type": "Expense", "Category": "Education", "Description": "Fintech Certification Course"},

        # June (Current Month)
        {"Date": d3.replace(day=1), "Amount": 5500.0, "Type": "Income", "Category": "Salary", "Description": "Monthly Corporate Salary"},
        {"Date": d3.replace(day=15), "Amount": 500.0, "Type": "Income", "Category": "Freelance/Side Hustle", "Description": "Consulting Advisory"},
        {"Date": d3.replace(day=2), "Amount": 1250.0, "Type": "Expense", "Category": "Housing", "Description": "Rent Payment"},
        {"Date": d3.replace(day=4), "Amount": 195.0, "Type": "Expense", "Category": "Food & Dining", "Description": "Supermarket Supplies"},
        {"Date": d3.replace(day=9), "Amount": 130.0, "Type": "Expense", "Category": "Utilities", "Description": "Electricity & Gas"},
        {"Date": d3.replace(day=14), "Amount": 240.0, "Type": "Expense", "Category": "Food & Dining", "Description": "Anniversary Dinner"},
        {"Date": d3.replace(day=18), "Amount": 80.0, "Type": "Expense", "Category": "Transportation", "Description": "Uber & Cab rides"},
        {"Date": d3.replace(day=21), "Amount": 30.0, "Type": "Expense", "Category": "Entertainment", "Description": "Streaming Subscriptions"}
    ]
    return pd.DataFrame(data)

# Initialize Session States
if "transactions" not in st.session_state:
    st.session_state.transactions = get_initial_dummy_data()

if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 3000.0

if "goal_name" not in st.session_state:
    st.session_state.goal_name = "Emergency Fund Reserve"

if "goal_amount" not in st.session_state:
    st.session_state.goal_amount = 15000.0

if "goal_contrib" not in st.session_state:
    st.session_state.goal_contrib = 600.0

if "goal_return" not in st.session_state:
    st.session_state.goal_return = 6.5

if "goal_start" not in st.session_state:
    st.session_state.goal_start = 2000.0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ==========================================
# 3. HELPER MATHEMATICAL & ANALYTICAL ENGINES
# ==========================================

# Financial Health Score Calculator
def calculate_financial_health_score(df):
    if df.empty:
        return 0, 0.0, 0.0, 0.0
    
    total_income = df[df["Type"] == "Income"]["Amount"].sum()
    total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
    
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0
    savings_rate = max(0.0, savings_rate)
    
    expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 100.0
    
    # Calculate average monthly expenses
    df_exp = df[df["Type"] == "Expense"].copy()
    if not df_exp.empty:
        df_exp["YearMonth"] = pd.to_datetime(df_exp["Date"]).dt.to_period("M")
        monthly_exp = df_exp.groupby("YearMonth")["Amount"].sum()
        avg_monthly_expense = monthly_exp.mean()
    else:
        avg_monthly_expense = 0.0
        
    # Emergency fund coverage ratio (months of average expenses covered by current net savings)
    if avg_monthly_expense > 0:
        emergency_months = max(0.0, net_savings / avg_monthly_expense)
    else:
        emergency_months = 6.0 if net_savings > 0 else 0.0

    # 1. Savings Rate Score (target: 30%+ is 100 pts)
    savings_score = min(100.0, savings_rate * (100.0 / 30.0))
    
    # 2. Expense Ratio Score (target: 50% or less is 100 pts, 100%+ is 0 pts)
    expense_score = max(0.0, min(100.0, (100.0 - expense_ratio) * 2.0))
    
    # 3. Emergency Fund Score (target: 6 months of expenses is 100 pts)
    ef_score = min(100.0, (emergency_months / 6.0) * 100.0)
    
    # Weighted Average Score
    health_score = int(0.4 * savings_score + 0.3 * expense_score + 0.3 * ef_score)
    health_score = max(0, min(100, health_score))
    
    return health_score, savings_rate, expense_ratio, emergency_months

# Investment Allocation Model
def get_investment_recommendation(age, risk_tolerance, income):
    # Base equity allocation determined using the standard industry "110 - age" rule
    base_equity = max(10, min(95, 110 - age))
    
    # Modify base allocation based on risk profile
    if risk_tolerance == "Conservative":
        equity_ratio = max(10, base_equity - 25)
    elif risk_tolerance == "Moderate":
        equity_ratio = base_equity
    else:  # Aggressive
        equity_ratio = min(95, base_equity + 15)
        
    debt_ratio = 100 - equity_ratio
    
    # Proportional assets inside Equity and Fixed Income classes
    if risk_tolerance == "Conservative":
        fd_pct = round(debt_ratio * 0.7)
        mf_pct = round(debt_ratio * 0.3)
        idx_pct = round(equity_ratio * 0.5)
        etf_pct = round(equity_ratio * 0.4)
        stock_pct = round(equity_ratio * 0.1)
    elif risk_tolerance == "Moderate":
        fd_pct = round(debt_ratio * 0.5)
        mf_pct = round(debt_ratio * 0.5)
        idx_pct = round(equity_ratio * 0.4)
        etf_pct = round(equity_ratio * 0.4)
        stock_pct = round(equity_ratio * 0.2)
    else:  # Aggressive
        fd_pct = round(debt_ratio * 0.3)
        mf_pct = round(debt_ratio * 0.7)
        idx_pct = round(equity_ratio * 0.3)
        etf_pct = round(equity_ratio * 0.4)
        stock_pct = round(equity_ratio * 0.3)
        
    # Realign summation matching exactly 100%
    allocations = {
        "Fixed Deposit": max(0, fd_pct),
        "Mutual Funds": max(0, mf_pct),
        "Index Funds": max(0, idx_pct),
        "ETFs": max(0, etf_pct),
        "Stocks": max(0, stock_pct)
    }
    
    alloc_sum = sum(allocations.values())
    if alloc_sum != 100:
        diff = 100 - alloc_sum
        allocations["Index Funds"] += diff

    # Industry benchmark historical annualized returns:
    # FD: 6%, MF: 9%, Index Funds: 11%, ETFs: 11.5%, Stocks: 14%
    weighted_return = (
        allocations["Fixed Deposit"] * 0.06 +
        allocations["Mutual Funds"] * 0.09 +
        allocations["Index Funds"] * 0.11 +
        allocations["ETFs"] * 0.115 +
        allocations["Stocks"] * 0.14
    )
    
    # Explanatory description
    if risk_tolerance == "Conservative":
        desc = "Preservation-focused: Tailored to steady income generation and minimizing drawdowns."
    elif risk_tolerance == "Moderate":
        desc = "Balanced-focused: Capital growth aligned with overall broad market performance."
    else:
        desc = "Growth-focused: Designed for maximized long-term compounding with high risk tolerance."
        
    return allocations, weighted_return, desc

# Savings Growth Projection calculator
def calculate_savings_timeline(goal_amount, monthly_contrib, expected_return_annual, starting_balance):
    if goal_amount <= starting_balance:
        return 0, [{"Month": 0, "Balance": starting_balance}]
    
    if monthly_contrib <= 0:
        return -1, []
        
    r = expected_return_annual / 100.0 / 12.0
    
    if r == 0:
        months = (goal_amount - starting_balance) / monthly_contrib
    else:
        val_num = goal_amount + (monthly_contrib / r)
        val_den = starting_balance + (monthly_contrib / r)
        if val_num <= 0 or val_den <= 0:
            return -1, []
        months = np.log(val_num / val_den) / np.log(1 + r)
        
    months = int(np.ceil(months))
    
    # Cap projections to 240 months (20 years) to avoid performance issues
    projected_months = min(months + 12, 240)
    
    projection = []
    current = starting_balance
    for m in range(projected_months + 1):
        if m > 0:
            current = current * (1 + r) + monthly_contrib
        projection.append({"Month": m, "Balance": round(current, 2)})
        if current >= goal_amount and m >= months:
            break
            
    return months, projection


# ==========================================
# 4. SIDEBAR INPUTS & NAVIGATION CONTROL
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #6366f1;'>💰 SmartWealth AI</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Navigation selectbox
menu = st.sidebar.radio(
    "Navigation View",
    ["Dashboard & Analytics", "Transactions Management", "Budget & Savings Goals", "Investment Recommendations", "AI Advisory Panel"]
)

st.sidebar.markdown("### Profile Parameters")
user_age = st.sidebar.number_input("User Age", min_value=18, max_value=100, value=30, step=1)
user_risk = st.sidebar.selectbox("Risk Profile Type", ["Conservative", "Moderate", "Aggressive"], index=1)
user_income = st.sidebar.number_input("Monthly Net Income ($)", min_value=0.0, value=6000.0, step=500.0)

st.sidebar.markdown("### Advisor Connectivity")
gemini_api_key = st.sidebar.text_input("Gemini API Key (Optional)", type="password", help="Input your Google Gemini API Key for customized GenAI consultations.")

# Store API key in session state or system variables
if gemini_api_key:
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    if HAS_GENAI:
        genai.configure(api_key=gemini_api_key)


# ==========================================
# 5. DATA PREPARATION FOR DASHBOARD VISUALS
# ==========================================
df_tx = st.session_state.transactions

# Ensure type conversions
if not df_tx.empty:
    df_tx["Date"] = pd.to_datetime(df_tx["Date"])
    df_tx["Amount"] = df_tx["Amount"].astype(float)

# Health score details
h_score, sav_rate, exp_ratio, emerg_m = calculate_financial_health_score(df_tx)

# Overall numbers
tot_inc = df_tx[df_tx["Type"] == "Income"]["Amount"].sum() if not df_tx.empty else 0.0
tot_exp = df_tx[df_tx["Type"] == "Expense"]["Amount"].sum() if not df_tx.empty else 0.0
tot_sav = tot_inc - tot_exp

# Current Month Expenses
today_date = date.today()
curr_month_tx = df_tx[
    (df_tx["Date"].dt.month == today_date.month) & 
    (df_tx["Date"].dt.year == today_date.year) & 
    (df_tx["Type"] == "Expense")
] if not df_tx.empty else pd.DataFrame()
current_month_exp_sum = curr_month_tx["Amount"].sum() if not curr_month_tx.empty else 0.0


# ==========================================
# TAB VIEW 1: DASHBOARD & ANALYTICS
# ==========================================
if menu == "Dashboard & Analytics":
    st.markdown("<h1>📊 Financial Dashboard</h1>", unsafe_allow_html=True)
    st.write("Track and monitor your overall financial status, analytics, and health scoring indexes in real-time.")
    
    # 5 KPI metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_kpi_card(
            "Total Income",
            f"${tot_inc:,.2f}",
            "Cumulative inflows",
            "#22c55e" # Green
        )
    with col2:
        render_kpi_card(
            "Total Expenses",
            f"${tot_exp:,.2f}",
            "Cumulative outflows",
            "#ef4444" # Red
        )
    with col3:
        render_kpi_card(
            "Net Savings",
            f"${tot_sav:,.2f}",
            "Total accumulated capital",
            "#06b6d4" # Teal
        )
    with col4:
        render_kpi_card(
            "Savings Rate",
            f"{sav_rate:.1f}%",
            "Target: > 20.0%",
            "#eab308" if sav_rate < 20 else "#22c55e"
        )
    with col5:
        render_kpi_card(
            "Health Score",
            f"{h_score}/100",
            "Multi-factor index",
            "#ef4444" if h_score < 40 else ("#eab308" if h_score < 70 else "#22c55e")
        )
        
    st.markdown("---")
    
    # Visual grid
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("### Financial Health Index Gauge")
        # Gauge chart using Plotly graph objects
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=h_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#6366f1"},
                'bgcolor': "#1e293b",
                'borderwidth': 1,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.2)'},
                    {'range': [40, 70], 'color': 'rgba(234, 179, 8, 0.2)'},
                    {'range': [70, 100], 'color': 'rgba(34, 197, 94, 0.2)'}
                ]
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f8fafc", 'family': "Outfit"},
            height=250,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Display short descriptive rating box
        if h_score < 40:
            st.markdown(
                "<div class='warning-box'><strong>Rating: Poor Health Score</strong><br>"
                "Your score is impacted by high expenses relative to income and low emergency fund levels. "
                "Review the AI Advisor panel for immediate actions to take.</div>",
                unsafe_allow_html=True
            )
        elif h_score < 70:
            st.markdown(
                "<div class='info-box'><strong>Rating: Fair Health Score</strong><br>"
                "Your financial situation is stable, but there is room for optimization. "
                "Consider increasing your savings rate or setting up automatic transfers to your emergency fund.</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='success-box'><strong>Rating: Excellent Health Score</strong><br>"
                "Fantastic! You have a high savings rate, an solid emergency cushion, and well-managed outflows. "
                "You are ready to optimize your investments.</div>",
                unsafe_allow_html=True
            )
            
    with col_right:
        st.markdown("### Expense Distribution by Category")
        df_expenses = df_tx[df_tx["Type"] == "Expense"]
        if not df_expenses.empty:
            category_totals = df_expenses.groupby("Category")["Amount"].sum().reset_index()
            fig_pie = px.pie(
                category_totals, 
                values="Amount", 
                names="Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#f8fafc", 'family': "Outfit"},
                height=250,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense data found. Add transactions in the next tab to view breakdown charts.")

    st.markdown("---")
    st.markdown("### Monthly Cash Inflow vs Outflow Trend")
    
    if not df_tx.empty:
        # Group by Year-Month and Type
        df_trend = df_tx.copy()
        df_trend["Month-Year"] = df_trend["Date"].dt.strftime("%Y-%m")
        trend_grouped = df_trend.groupby(["Month-Year", "Type"])["Amount"].sum().reset_index()
        
        # Pivot table for simple plotting
        trend_pivot = trend_grouped.pivot(index="Month-Year", columns="Type", values="Amount").fillna(0.0).reset_index()
        
        # Add columns if missing
        if "Income" not in trend_pivot:
            trend_pivot["Income"] = 0.0
        if "Expense" not in trend_pivot:
            trend_pivot["Expense"] = 0.0
            
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend_pivot["Month-Year"], 
            y=trend_pivot["Income"], 
            name="Income", 
            marker_color="#22c55e"
        ))
        fig_trend.add_trace(go.Bar(
            x=trend_pivot["Month-Year"], 
            y=trend_pivot["Expense"], 
            name="Expense", 
            marker_color="#ef4444"
        ))
        
        fig_trend.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f8fafc", 'family': "Outfit"},
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#334155")
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No transaction data available to plot timeline trends.")


# ==========================================
# TAB VIEW 2: TRANSACTIONS MANAGEMENT
# ==========================================
elif menu == "Transactions Management":
    st.markdown("<h1>✍️ Transaction Ledger</h1>", unsafe_allow_html=True)
    st.write("Add, view, download, or edit your financial entries. All transactions are securely held in session memory.")
    
    col_form, col_table = st.columns([2, 3])
    
    with col_form:
        st.markdown("### Record Transaction")
        with st.form("transaction_form", clear_on_submit=True):
            tx_date = st.date_input("Transaction Date", value=date.today())
            tx_type = st.selectbox("Transaction Type", ["Income", "Expense"])
            
            # Select category list based on type selection
            if tx_type == "Income":
                tx_category = st.selectbox("Category", ["Salary", "Freelance/Side Hustle", "Investments", "Other Income"])
            else:
                tx_category = st.selectbox("Category", ["Housing", "Food & Dining", "Utilities", "Transportation", "Entertainment", "Health & Fitness", "Education", "Shopping", "Other Expense"])
                
            tx_amount = st.number_input("Amount ($)", min_value=0.01, step=10.0, format="%.2f")
            tx_desc = st.text_input("Description", placeholder="E.g. Walmart, Client design work")
            
            submitted = st.form_submit_button("Record Transaction")
            
            if submitted:
                # Add row to state DataFrame
                new_tx = pd.DataFrame([{
                    "Date": pd.to_datetime(tx_date),
                    "Amount": float(tx_amount),
                    "Type": tx_type,
                    "Category": tx_category,
                    "Description": tx_desc
                }])
                st.session_state.transactions = pd.concat([st.session_state.transactions, new_tx], ignore_index=True)
                st.success("Transaction logged successfully!")
                st.rerun()
                
        # Deletion Panel
        st.markdown("---")
        st.markdown("### Remove Transaction Entry")
        if not df_tx.empty:
            tx_to_delete = st.selectbox(
                "Select Transaction to Delete",
                options=df_tx.index,
                format_func=lambda idx: f"[{df_tx.loc[idx, 'Date'].strftime('%Y-%m-%d')}] {df_tx.loc[idx, 'Type']} | {df_tx.loc[idx, 'Category']} | ${df_tx.loc[idx, 'Amount']:.2f} | {df_tx.loc[idx, 'Description']}"
            )
            if st.button("Delete Selected Transaction", type="secondary"):
                st.session_state.transactions = df_tx.drop(tx_to_delete).reset_index(drop=True)
                st.success("Transaction deleted successfully!")
                st.rerun()
        else:
            st.info("No transaction records available for deletion.")
            
    with col_table:
        st.markdown("### Ledger Records")
        
        # Display full ledger dataframe
        if not df_tx.empty:
            # Sort by date descending for view
            view_df = df_tx.copy()
            view_df["Date"] = view_df["Date"].dt.strftime("%Y-%m-%d")
            view_df = view_df.sort_values(by="Date", ascending=False)
            
            st.dataframe(
                view_df,
                use_container_width=True,
                column_config={
                    "Amount": st.column_config.NumberColumn(format="$%.2f")
                }
            )
            
            # Export data downloads
            st.markdown("### Export Ledger Data")
            csv_data = df_tx.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Ledger (CSV)",
                data=csv_data,
                file_name=f"transactions_export_{date.today().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("The transaction ledger is currently empty. Add items using the form to populate.")


# ==========================================
# TAB VIEW 3: BUDGET & SAVINGS GOALS
# ==========================================
elif menu == "Budget & Savings Goals":
    st.markdown("<h1>🎯 Budgets & Goal Planners</h1>", unsafe_allow_html=True)
    st.write("Construct guidelines to limit expenses and project savings growth timelines with compounding returns.")
    
    col_bud, col_sav = st.columns([1, 1])
    
    with col_bud:
        st.markdown("### Monthly Spending Budget")
        monthly_budget = st.number_input("Monthly Budget Cap ($)", min_value=1.0, value=st.session_state.monthly_budget, step=100.0)
        st.session_state.monthly_budget = monthly_budget
        
        st.write(f"This Month's Spending Goal Cap: **${monthly_budget:,.2f}**")
        st.write(f"Actual Outflows Recorded (June): **${current_month_exp_sum:,.2f}**")
        
        # Budget utilization calculation
        utilization_rate = (current_month_exp_sum / monthly_budget * 100) if monthly_budget > 0 else 0.0
        
        # Progress Bar visual
        progress_color = "#22c55e" # Green
        if utilization_rate > 100:
            progress_color = "#ef4444" # Red
        elif utilization_rate > 80:
            progress_color = "#eab308" # Yellow
            
        progress_bar_html = f"""
        <div style="background-color: #334155; border-radius: 10px; width: 100%; height: 24px; overflow: hidden; margin-top: 10px; margin-bottom: 10px;">
            <div style="background-color: {progress_color}; width: {min(100, utilization_rate)}%; height: 100%; transition: width 0.5s ease; text-align: center; color: white; font-weight: bold; font-size: 14px; line-height: 24px;">
                {utilization_rate:.1f}%
            </div>
        </div>
        """
        st.markdown(progress_bar_html, unsafe_allow_html=True)
        
        # Display warn or success messages
        if utilization_rate > 100:
            st.markdown(
                f"<div class='warning-box'>🚨 **Over Budget warning!** You have exceeded your designated limit by "
                f"**${(current_month_exp_sum - monthly_budget):,.2f}**. Consider delaying non-essential purchases.</div>", 
                unsafe_allow_html=True
            )
        elif utilization_rate > 80:
            st.markdown(
                f"<div class='warning-box' style='background-color: rgba(234, 179, 8, 0.1); border-color: #eab308; color: #fef08a;'>"
                f"⚠️ **Attention:** Budget utilization is high ({utilization_rate:.1f}%). Limit extra expenditures.</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='success-box'>✅ **Healthy budget:** You are well within your budget limits this month. Keep it up!</div>",
                unsafe_allow_html=True
            )
            
    with col_sav:
        st.markdown("### Savings Goal Planner")
        goal_name = st.text_input("Target Savings Goal Name", value=st.session_state.goal_name)
        st.session_state.goal_name = goal_name
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            goal_amount = st.number_input("Target Goal Amount ($)", min_value=1.0, value=st.session_state.goal_amount, step=500.0)
            st.session_state.goal_amount = goal_amount
            starting_bal = st.number_input("Starting Capital Balance ($)", min_value=0.0, value=st.session_state.goal_start, step=250.0)
            st.session_state.goal_start = starting_bal
            
        with col_g2:
            monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=1.0, value=st.session_state.goal_contrib, step=50.0)
            st.session_state.goal_contrib = monthly_contrib
            expected_return = st.number_input("Expected Annual Return (%)", min_value=0.0, max_value=40.0, value=st.session_state.goal_return, step=0.5)
            st.session_state.goal_return = expected_return
            
        # Calculation results
        months_required, projection = calculate_savings_timeline(goal_amount, monthly_contrib, expected_return, starting_bal)
        
        if months_required == 0:
            st.markdown(f"<div class='success-box'>🎉 You have already achieved the savings target!</div>", unsafe_allow_html=True)
        elif months_required == -1:
            st.markdown("<div class='warning-box'>❌ Invalid target or contributions configured. Double check your settings.</div>", unsafe_allow_html=True)
        else:
            years = months_required // 12
            rem_months = months_required % 12
            timeline_str = f"{years} Years, {rem_months} Months" if years > 0 else f"{rem_months} Months"
            
            st.info(f"⌛ Estimated Timeline to Reach Goal: **{timeline_str}** ({months_required} months total)")
            
            # Progress meter toward goal using current savings relative to target
            target_pct = min(100.0, max(0.0, (starting_bal / goal_amount) * 100))
            st.write(f"Savings Goal Starting Milestone progress: **{target_pct:.1f}%** reached")
            st.progress(target_pct / 100.0)
            
    # Projections Chart rendering
    if months_required > 0 and len(projection) > 0:
        st.markdown("---")
        st.markdown("### Cumulative Portfolio Growth Projections")
        df_proj = pd.DataFrame(projection)
        
        fig_proj = px.line(
            df_proj, 
            x="Month", 
            y="Balance", 
            labels={"Month": "Months Elapsed", "Balance": "Portfolio Value ($)"}
        )
        
        # Add target line
        fig_proj.add_hline(y=goal_amount, line_dash="dash", line_color="#ef4444", annotation_text="Goal Target Value")
        
        fig_proj.update_traces(line_color='#6366f1', line_width=3)
        fig_proj.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f8fafc", 'family': "Outfit"},
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis=dict(showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=True, gridcolor="#334155")
        )
        st.plotly_chart(fig_proj, use_container_width=True)


# ==========================================
# TAB VIEW 4: INVESTMENT RECOMMENDATIONS
# ==========================================
elif menu == "Investment Recommendations":
    st.markdown("<h1>📈 Asset Allocation Model</h1>", unsafe_allow_html=True)
    st.write("Generate investment recommendations based on your current age, risk profile, and monthly income parameters.")
    
    # Calculate recommendations
    allocations, est_return, risk_desc = get_investment_recommendation(user_age, user_risk, user_income)
    
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.markdown("### Target Asset Distribution")
        
        # Plotly pie chart of asset allocations
        fig_pie_alloc = px.pie(
            names=list(allocations.keys()),
            values=list(allocations.values()),
            hole=0.4,
            color_discrete_sequence=['#64748b', '#3b82f6', '#0d9488', '#6366f1', '#10b981']
        )
        fig_pie_alloc.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f8fafc", 'family': "Outfit"},
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_pie_alloc, use_container_width=True)
        
    with col_r:
        st.markdown("### Recommended Asset Breakdown")
        
        # Display KPI card for Expected Portfolio Return
        render_kpi_card(
            "Expected Annual Portfolio Return",
            f"{est_return*100:.2f}%",
            f"Based on: {user_risk} Allocation Profile",
            "#6366f1"
        )
        
        # Display profile narrative card
        st.markdown(
            f"<div class='info-box'><strong>Risk Profile Description:</strong><br>{risk_desc}</div>",
            unsafe_allow_html=True
        )
        
        # Detailed descriptions of suggested allocations
        for asset, pct in allocations.items():
            if pct > 0:
                st.write(f"🔹 **{asset}: {pct}%** of total investment capital")


# ==========================================
# TAB VIEW 5: AI ADVISORY PANEL & REPORT
# ==========================================
elif menu == "AI Advisory Panel":
    st.markdown("<h1>🤖 AI Personal Financial Advisor</h1>", unsafe_allow_html=True)
    st.write("Consult our advisor module on budgeting, saving strategies, or portfolio structures.")
    
    # Financial parameters data package for GenAI
    metrics_summary = {
        "health_score": h_score,
        "total_income": tot_inc,
        "total_expense": tot_exp,
        "net_savings": tot_sav,
        "savings_rate": sav_rate,
        "emergency_months": emerg_m,
        "monthly_budget": st.session_state.monthly_budget,
        "current_month_expenses": current_month_exp_sum,
        "budget_utilization": (current_month_exp_sum / st.session_state.monthly_budget * 100) if st.session_state.monthly_budget > 0 else 0.0,
        "goal_name": st.session_state.goal_name,
        "goal_amount": st.session_state.goal_amount,
        "goal_timeline": f"{(calculate_savings_timeline(st.session_state.goal_amount, st.session_state.goal_contrib, st.session_state.goal_return, st.session_state.goal_start)[0])} months"
    }
    
    # Investment allocations
    allocations, est_return, risk_desc = get_investment_recommendation(user_age, user_risk, user_income)
    recs_summary = {
        "risk_tolerance": user_risk,
        "expected_return": est_return,
        "allocations": allocations
    }
    
    # Prepare text overview of actual data
    df_recent = df_tx.sort_values(by="Date", ascending=False).head(10)
    tx_string_list = []
    for _, r in df_recent.iterrows():
        tx_string_list.append(f"{r['Date'].strftime('%Y-%m-%d')} | {r['Type']} | {r['Category']} | ${r['Amount']:.2f} | {r['Description']}")
    transactions_str = "\n".join(tx_string_list)
    
    # AI Query processing function
    def run_financial_consultant(query):
        # 1. Check if Gemini connectivity key exists and library imports passed
        if HAS_GENAI and "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"]:
            try:
                system_instruction = (
                    "You are a Senior Fintech Advisory Specialist. Generate personalized, highly professional, "
                    "and actionable wealth advice based on the user's provided ledger details and preferences. "
                    "Always present formatted structure and bullet points."
                )
                
                context_prompt = f"""
                Financial Health Score: {metrics_summary['health_score']}/100
                Total Income: ${metrics_summary['total_income']:.2f}
                Total Expenses: ${metrics_summary['total_expense']:.2f}
                Savings Rate: {metrics_summary['savings_rate']:.1f}%
                Months of Emergency Fund Saved: {metrics_summary['emergency_months']:.1f}
                Current Month Budget Utilized: {metrics_summary['budget_utilization']:.1f}% (Actual: ${metrics_summary['current_month_expenses']:.2f} / Budget Cap: ${metrics_summary['monthly_budget']:.2f})
                Savings Goal: {metrics_summary['goal_name']} Target of ${metrics_summary['goal_amount']:.2f} (Est Timeline: {metrics_summary['goal_timeline']})
                
                Investment Preferences:
                Age: {user_age}
                Risk Tolerance: {user_risk}
                Target Returns Expected: {recs_summary['expected_return']*100:.2f}% per annum
                Proposed Asset Allocations: {recs_summary['allocations']}
                
                Recent Transactions Log:
                {transactions_str}
                
                User Inquiry: {query}
                """
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_instruction}\n\n{context_prompt}")
                return response.text
                
            except Exception as e:
                # If API call breaks, return error alert and fallback output
                st.toast(f"GenAI Connection Failure: {str(e)}", icon="⚠️")
                return get_rule_based_advisory_text(query)
        else:
            return get_rule_based_advisory_text(query)

    # Backup rule-based advisor logic
    def get_rule_based_advisory_text(query):
        query_cleaned = query.lower()
        
        # Group by category for top list
        df_exp_only = df_tx[df_tx["Type"] == "Expense"]
        if not df_exp_only.empty:
            max_cat_name = df_exp_only.groupby("Category")["Amount"].sum().idxmax()
            max_cat_sum = df_exp_only.groupby("Category")["Amount"].sum().max()
        else:
            max_cat_name = "N/A"
            max_cat_sum = 0.0

        if "save" in query_cleaned or "saving" in query_cleaned:
            advice = (
                f"### AI Saving Recommendations\n"
                f"Your current **Savings Rate** is **{sav_rate:.1f}%**.\n\n"
                f"**Strategic Breakdown:**\n"
                f"1. **Analyze Highest Expenditure:** Your top spending category is **{max_cat_name}** with a cumulative "
                f"outflow of **${max_cat_sum:,.2f}**. Cutting back here by 15% will significantly improve your baseline savings rate.\n"
                f"2. **Implement Pay-Yourself-First Strategy:** Automate a fixed deposit of at least 15% of your income into a separate high-yield account immediately on payday.\n"
                f"3. **Target Savings Cushion:** With an emergency buffer of **{emerg_m:.1f} months**, continue accumulating deposits "
                f"until you comfortably cover at least 6 months of living expenses."
            )
        elif "invest" in query_cleaned or "investment" in query_cleaned:
            advice = (
                f"### AI Investment Guidance\n"
                f"Based on your profile (Age: **{user_age}**, Risk Profile: **{user_risk}**), we recommend a target "
                f"portfolio allocation to reach an expected return of **{est_return*100:.2f}%** per year.\n\n"
                f"**Portfolio Allocations:**\n"
                f"- **Growth Assets (Index Funds/ETFs/Stocks):** {allocations['Index Funds'] + allocations['ETFs'] + allocations['Stocks']}% of total capital.\n"
                f"- **Safety/Income Assets (Fixed Deposits/Mutual Funds):** {allocations['Fixed Deposit'] + allocations['Mutual Funds']}% of total capital.\n\n"
                f"**Investment Advisory:**\n"
                f"Given your risk profile, leverage broad market index funds for consistent wealth compounding while maintaining "
                f"a minor cash buffer for short-term liquidity needs."
            )
        elif "budget" in query_cleaned or "spend" in query_cleaned or "overspending" in query_cleaned:
            advice = (
                f"### AI Spending & Budget Assessment\n"
                f"Your monthly budget cap is set to **${metrics_summary['monthly_budget']:,.2f}**.\n\n"
                f"**Status Analysis:**\n"
                f"Your actual outflows for the current month stand at **${current_month_exp_sum:,.2f}** (utilization: **{metrics_summary['budget_utilization']:.1f}%**).\n\n"
                f"**Optimization Checklist:**\n"
                f"- **Warning Indicators:** "
                f"{'🔴 High Risk! You have exceeded your monthly budget ceiling. Pause all non-essential outflows.' if metrics_summary['budget_utilization'] > 100 else '🟢 Good Management. Your current month spending is currently within limits.'}\n"
                f"- **Primary Category Check:** Control impulsive shopping or food deliveries, particularly inside your highest spending category (**{max_cat_name}**)."
            )
        elif "health" in query_cleaned or "score" in query_cleaned:
            advice = (
                f"### AI Financial Health Analysis\n"
                f"Your Financial Health Score is **{h_score}/100**.\n\n"
                f"**Performance Rating:**\n"
                f"- **Savings Metric (40% Weight):** "
                f"{'Strong.' if sav_rate >= 20 else 'Needs improvement. Target at least 20% savings rate.'}\n"
                f"- **Expense Margin (30% Weight):** "
                f"{'Well within limits.' if exp_ratio < 70 else 'High outflows. Reduce fixed monthly burdens.'}\n"
                f"- **Emergency Cushion (30% Weight):** "
                f"{'Solid reserve!' if emerg_m >= 6.0 else 'Inadequate. Build cash reserves to cover at least 6 months of expenses.'}"
            )
        else:
            advice = (
                f"### AI Advisory Overview\n"
                f"Hello! I am your rule-based AI financial advisor. Ask me specific questions about your portfolio, "
                f"savings strategies, or budgets. For full personalized advisories, input your Gemini API Key in the sidebar.\n\n"
                f"**Current Summary:**\n"
                f"- **Financial Health score:** {h_score}/100\n"
                f"- **Cash Savings:** ${tot_sav:,.2f}\n"
                f"- **Risk tolerance:** {user_risk}"
            )
        return advice

    # Advisory UI Layout
    col_input, col_chat = st.columns([2, 3])
    
    with col_input:
        st.markdown("### Ask your Advisor")
        user_query = st.text_input("Ask a question about your financial situation:", placeholder="Can I save more money?")
        ask_btn = st.button("Consult AI Advisor", type="primary")
        
        # Display helpful suggested questions
        st.write("💡 *Suggested Inquiries:*")
        st.caption("- How can I save more money?")
        st.caption("- Am I overspending?")
        st.caption("- What is my investment recommendation?")
        st.caption("- How do I improve my health score?")
        
        if ask_btn and user_query:
            with st.spinner("Analyzing ledger and calculating advisory plans..."):
                response_text = run_financial_consultant(user_query)
                # Save to history
                st.session_state.chat_history.append((user_query, response_text))
                st.rerun()
                
    with col_chat:
        st.markdown("### Consultation Logs")
        if len(st.session_state.chat_history) > 0:
            # Render chat history in reverse chronological order
            for q, a in reversed(st.session_state.chat_history):
                st.markdown(f"**👤 Question:** {q}")
                st.markdown(f"**🤖 Advisor Response:**\n{a}")
                st.markdown("---")
        else:
            st.info("No query logs recorded. Enter your query on the left pane to begin.")

    # ==========================================
    # PDF REPORT GENERATOR MODULE
    # ==========================================
    st.markdown("---")
    st.markdown("### 📄 Generate Comprehensive Financial Report")
    st.write("Download a beautifully formatted, publication-quality PDF report containing all your metrics, projections, and AI recommendations.")
    
    if st.button("Build PDF Report", type="secondary"):
        with st.spinner("Generating document layers..."):
            try:
                # Use recent AI advisory output if available, or generate standard summary
                base_advisory_text = (
                    st.session_state.chat_history[-1][1] if len(st.session_state.chat_history) > 0 
                    else get_rule_based_advisory_text("health")
                )
                # Clean markdown characters from advisor text for standard Helvetica font limits
                clean_adv_text = base_advisory_text.replace("**", "").replace("###", "").replace("🔹", "-").replace("🚨", "!").replace("⚠️", "!").replace("✨", "*")
                
                # FPDF Generation
                pdf = FPDF()
                pdf.alias_nb_pages()
                pdf.add_page()
                pdf.set_font('Helvetica', '', 12)
                
                # Colors
                pdf.set_text_color(51, 65, 85) # slate-700
                
                # Main Title Header
                pdf.set_font('Helvetica', 'B', 20)
                pdf.set_text_color(30, 41, 59) # slate-800
                pdf.cell(0, 10, 'Financial Health & Wealth Report', 0, 1, 'L')
                
                # Subtitle details
                pdf.set_font('Helvetica', 'I', 10)
                pdf.set_text_color(100, 116, 139) # slate-500
                pdf.cell(0, 8, f'Generated on {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'L')
                pdf.ln(5)
                
                # Horizontal rule line
                pdf.set_draw_color(226, 232, 240) # slate-200
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(8)
                
                # Section 1: Executive Summary
                pdf.set_font('Helvetica', 'B', 14)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 10, '1. Executive Summary Metrics', 0, 1, 'L')
                pdf.ln(2)
                
                pdf.set_font('Helvetica', '', 11)
                pdf.set_text_color(51, 65, 85)
                
                kpi_data = [
                    ("Financial Health Score:", f"{metrics_summary['health_score']}/100"),
                    ("Total Cumulative Income:", f"${metrics_summary['total_income']:,.2f}"),
                    ("Total Cumulative Expenses:", f"${metrics_summary['total_expense']:,.2f}"),
                    ("Overall Savings Rate:", f"{metrics_summary['savings_rate']:.1f}%"),
                    ("Emergency Cushion Months:", f"{metrics_summary['emergency_months']:.1f} months of expenses")
                ]
                
                for label, val in kpi_data:
                    pdf.set_font('Helvetica', '', 11)
                    pdf.cell(60, 8, label, 0, 0)
                    pdf.set_font('Helvetica', 'B', 11)
                    pdf.cell(60, 8, val, 0, 1)
                pdf.ln(6)
                
                # Section 2: Budgeting Analysis
                pdf.set_font('Helvetica', 'B', 14)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 10, '2. Budget & Goals Assessment', 0, 1, 'L')
                pdf.ln(2)
                
                budget_data = [
                    ("Monthly Spending Cap:", f"${metrics_summary['monthly_budget']:,.2f}"),
                    ("Current Month Spending (June):", f"${metrics_summary['current_month_expenses']:,.2f}"),
                    ("Budget Utilization Percentage:", f"{metrics_summary['budget_utilization']:.1f}%"),
                    ("Designated Savings Goal Name:", f"{metrics_summary['goal_name']}"),
                    ("Savings Target Value:", f"${metrics_summary['goal_amount']:,.2f}"),
                    ("Est Target Completion Timeline:", f"{metrics_summary['goal_timeline']}")
                ]
                
                for label, val in budget_data:
                    pdf.set_font('Helvetica', '', 11)
                    pdf.cell(65, 8, label, 0, 0)
                    pdf.set_font('Helvetica', 'B', 11)
                    pdf.cell(60, 8, val, 0, 1)
                pdf.ln(6)
                
                # Section 3: Recommended Investments
                pdf.set_font('Helvetica', 'B', 14)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 10, '3. Investment recommendations', 0, 1, 'L')
                pdf.ln(2)
                
                pdf.set_font('Helvetica', '', 11)
                pdf.cell(60, 8, "Target Risk Profile:", 0, 0)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(60, 8, f"{recs_summary['risk_tolerance']}", 0, 1)
                
                pdf.set_font('Helvetica', '', 11)
                pdf.cell(60, 8, "Expected Annual Return:", 0, 0)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(60, 8, f"{recs_summary['expected_return']*100:.2f}%", 0, 1)
                pdf.ln(4)
                
                # Allocations table
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_fill_color(241, 245, 249) # slate-100
                pdf.cell(70, 8, "Asset Allocation Class", 1, 0, 'L', True)
                pdf.cell(40, 8, "Target Allocation %", 1, 1, 'C', True)
                
                pdf.set_font('Helvetica', '', 10)
                for asset, pct in recs_summary['allocations'].items():
                    pdf.cell(70, 8, asset, 1, 0, 'L')
                    pdf.cell(40, 8, f"{pct}%", 1, 1, 'C')
                pdf.ln(8)
                
                # Section 4: Advisor Comments
                pdf.set_font('Helvetica', 'B', 14)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 10, '4. AI Financial Consultation Notes', 0, 1, 'L')
                pdf.ln(2)
                
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 6, clean_adv_text)
                
                # Save PDF to bytes
                pdf_output = pdf.output()
                
                # Adapt bytes retrieval for multiple fpdf/fpdf2 versions
                if isinstance(pdf_output, str):
                    pdf_bytes = pdf_output.encode('latin1')
                else:
                    pdf_bytes = bytes(pdf_output)
                
                st.download_button(
                    label="📥 Download Financial Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"SmartWealth_Report_{date.today().strftime('%Y-%m-%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("Financial Report built successfully!")
            except Exception as pdf_ex:
                st.error(f"Error compiling PDF layout: {str(pdf_ex)}")
