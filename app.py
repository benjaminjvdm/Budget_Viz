import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Initialize session state
if 'income_entries' not in st.session_state:
    st.session_state.income_entries = []

if 'expense_entries' not in st.session_state:
    st.session_state.expense_entries = []

# Calculate budget totals
def calculate_budget():
    total_income = sum(entry['amount'] for entry in st.session_state.income_entries)
    total_expenses = sum(entry['amount'] for entry in st.session_state.expense_entries)
    net_income = total_income - total_expenses
    return total_income, total_expenses, net_income

# Visualization functions
def display_income_pie():
    income_df = pd.DataFrame(st.session_state.income_entries)
    fig = px.pie(income_df, values='amount', names='type', 
                title='Income Breakdown', hole=0.3,
                color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig, use_container_width=True)

def display_expenses_pie():
    expense_df = pd.DataFrame(st.session_state.expense_entries)
    fig = px.pie(expense_df, values='amount', names='type', 
                title='Expenses Breakdown', hole=0.3,
                color_discrete_sequence=px.colors.sequential.Reds_r)
    st.plotly_chart(fig, use_container_width=True)

def display_budget_chart(total_income, total_expenses, net_income, multiplier):
    expected_income = total_expenses * multiplier
    budget_df = pd.DataFrame({
        "Category": ["Income", "Expenses", "Expected Income", "Net Income"],
        "Amount": [total_income, total_expenses, expected_income, net_income]
    })
    
    color_map = {
        "Income": "#2ecc71",
        "Expenses": "#e74c3c",
        "Expected Income": "#3498db",
        "Net Income": "#9b59b6" if net_income >= 0 else "#c0392b"
    }
    
    fig = px.bar(budget_df, x='Category', y='Amount', 
                text='Amount', color='Category',
                color_discrete_map=color_map,
                title="Budget Overview")
    
    fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
    fig.update_layout(showlegend=False, uniformtext_minsize=8)
    st.plotly_chart(fig, use_container_width=True)

# Main app layout
st.set_page_config(page_title="Budget Manager", page_icon="💸", layout="wide")
st.title("💰 Personal Budget Manager")

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    multiplier = st.selectbox(
        "Income Multiplier for Projections",
        [1.0, 1.25, 1.5, 1.75, 2.0],
        index=2,
        help="Multiplier for calculating expected income based on expenses"
    )
    
st.sidebar.subheader("About the Author")

image_url = "https://github.com/benjaminjvdm/streamlit-author/blob/main/Untitled%20design(1)(1).png?raw=true"
try:
    response = requests.get(image_url)
    print(f"Image URL: {image_url}")
    response.raise_for_status()
    image = response.content
    st.sidebar.image(image, caption="Moon Benjee (문벤지)")
except requests.exceptions.RequestException as e:
    st.sidebar.error(f"Error loading image: {e}")

st.sidebar.markdown(
    """
    This app was Built with ❤️ by **Benjee(문벤지)**.
    You can connect with me on: [LinkedIn](https://www.linkedin.com/in/benjaminjvdm/)
    """
)

# Input sections
col1, col2 = st.columns(2)

with col1:
    with st.expander("➕ Add Income Source", expanded=True):
        income_form = st.form(key="income_form")
        income_form.subheader("New Income Source")
        income_type = income_form.text_input("Source Name", key="income_type")
        income_amount = income_form.number_input("Amount ($)", min_value=0.0, step=50.0, key="income_amount")
        if income_form.form_submit_button("Add Income"):
            if income_type.strip() and income_amount > 0:
                st.session_state.income_entries.append({
                    "type": income_type.strip(),
                    "amount": float(income_amount)
                })
                st.success("Income source added!")
            else:
                st.error("Please fill all fields correctly")

with col2:
    with st.expander("➖ Add Expense Category", expanded=True):
        expense_form = st.form(key="expense_form")
        expense_form.subheader("New Expense Category")
        expense_type = expense_form.text_input("Category Name", key="expense_type")
        expense_amount = expense_form.number_input("Amount ($)", min_value=0.0, step=50.0, key="expense_amount")
        if expense_form.form_submit_button("Add Expense"):
            if expense_type.strip() and expense_amount > 0:
                st.session_state.expense_entries.append({
                    "type": expense_type.strip(),
                    "amount": float(expense_amount)
                })
                st.success("Expense category added!")
            else:
                st.error("Please fill all fields correctly")

# Display data tables
if st.session_state.income_entries or st.session_state.expense_entries:
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        if st.session_state.income_entries:
            st.subheader("Income Sources")
            income_df = pd.DataFrame(st.session_state.income_entries)
            st.dataframe(
                income_df.style.format({'amount': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )
    
    with col4:
        if st.session_state.expense_entries:
            st.subheader("Expense Categories")
            expense_df = pd.DataFrame(st.session_state.expense_entries)
            st.dataframe(
                expense_df.style.format({'amount': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )

# Calculations
total_income, total_expenses, net_income = calculate_budget()

# Key metrics
st.markdown("---")
st.subheader("Financial Summary")
metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Total Income", f"${total_income:,.2f}")
metric_col2.metric("Total Expenses", f"${total_expenses:,.2f}")
metric_col3.metric(
    "Net Balance", 
    f"${net_income:,.2f}", 
    delta_color="inverse",
    delta=f"{'Surplus' if net_income >= 0 else 'Deficit'}"
)

# Visualizations
if st.session_state.income_entries or st.session_state.expense_entries:
    st.markdown("---")
    st.subheader("Financial Analysis")
    
    # Pie charts
    if st.session_state.income_entries and st.session_state.expense_entries:
        cols = st.columns(2)
        with cols[0]:
            display_income_pie()
        with cols[1]:
            display_expenses_pie()
    
    # Budget chart
    display_budget_chart(total_income, total_expenses, net_income, multiplier)

# Empty state handling
if not st.session_state.income_entries and not st.session_state.expense_entries:
    st.markdown("---")
    st.info("👋 Welcome! Start by adding income sources and expense categories using the forms above.")
