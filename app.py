import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit_local_storage import LocalStorage
import json

# --- Local Storage ---
localS = LocalStorage()

# --- Configuration ---
CURRENCIES = {
    "USD": {"symbol": "$", "name": "US Dollar"},
    "EUR": {"symbol": "€", "name": "Euro"},
    "ZAR": {"symbol": "R", "name": "South African Rand"}
}

# --- Utility Functions ---
def format_currency(amount, currency_symbol):
    """Formats a number as a currency string."""
    return f"{currency_symbol}{amount:,.2f}"

# --- Initialize Session State ---
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

def display_budget_chart(total_income, total_expenses, net_income, multiplier, currency_symbol):
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
    
    fig.update_traces(texttemplate=f'{currency_symbol}%{{y:,.2f}}', textposition='outside')
    fig.update_layout(showlegend=False, uniformtext_minsize=8)
    st.plotly_chart(fig, use_container_width=True)

def display_edit_form(entry, index, entry_type, currency_symbol):
    """Displays a form to edit an existing entry."""
    with st.form(key=f"form_{entry_type}_{index}"):
        st.subheader(f"Edit {entry_type.replace('_', ' ').capitalize()}")
        new_type = st.text_input("Source Name", value=entry['type'], key=f"type_{entry_type}_{index}")
        new_amount = st.number_input(f"Amount ({currency_symbol})", value=entry['amount'], min_value=0.0, step=50.0, key=f"amount_{entry_type}_{index}")

        c1, c2 = st.columns(2)
        if c1.form_submit_button("Save Changes"):
            entry_list_key = f"{entry_type}_entries"
            st.session_state[entry_list_key][index] = {"type": new_type, "amount": new_amount}
            st.session_state[f'editing_{entry_type}'] = None
            st.rerun()
        if c2.form_submit_button("Cancel"):
            st.session_state[f'editing_{entry_type}'] = None
            st.rerun()

# Main app layout
st.set_page_config(page_title="Budget Manager", page_icon="💸", layout="wide")

# --- Load and Initialize State ---
if 'app_bootstrapped' not in st.session_state:
    # Attempt to load from local storage
    stored_state_str = localS.getItem('budget_app_state')
    if stored_state_str:
        try:
            stored_state = json.loads(stored_state_str)
            st.session_state.update(stored_state)
        except (json.JSONDecodeError, TypeError):
            # If stored data is corrupted or not valid JSON, start fresh
            pass

    # Set defaults for any state that wasn't loaded
    if 'income_entries' not in st.session_state:
        st.session_state.income_entries = []
    if 'expense_entries' not in st.session_state:
        st.session_state.expense_entries = []
    if 'currency' not in st.session_state:
        st.session_state.currency = "USD"

    # Initialize non-persisted state
    st.session_state.editing_income = None
    st.session_state.editing_expense = None

    # Mark as bootstrapped
    st.session_state.app_bootstrapped = True

currency_symbol = CURRENCIES[st.session_state.currency]["symbol"]

st.title("💰 Personal Budget Manager")

# Sidebar controls
with st.sidebar:
    st.header("Settings")

    # Currency Selector
    selected_currency = st.selectbox(
        "Select Currency",
        options=list(CURRENCIES.keys()),
        format_func=lambda x: f"{CURRENCIES[x]['name']} ({CURRENCIES[x]['symbol']})",
        key='currency'
    )

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
        income_amount = income_form.number_input(f"Amount ({currency_symbol})", min_value=0.0, step=50.0, key="income_amount")
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
        expense_amount = expense_form.number_input(f"Amount ({currency_symbol})", min_value=0.0, step=50.0, key="expense_amount")
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
        st.subheader("Income Sources")
        if not st.session_state.income_entries:
            st.caption("No income sources added yet.")
        else:
            for i, entry in enumerate(st.session_state.income_entries):
                if st.session_state.editing_income == i:
                    display_edit_form(entry, i, 'income', currency_symbol)
                else:
                    col1, col2, col3, col4 = st.columns([0.4, 0.3, 0.15, 0.15])
                    col1.write(entry['type'])
                    col2.write(format_currency(entry['amount'], currency_symbol))
                    if col3.button("Edit", key=f"edit_income_{i}", use_container_width=True):
                        st.session_state.editing_income = i
                        st.rerun()
                    if col4.button("Del", key=f"delete_income_{i}", use_container_width=True):
                        st.session_state.income_entries.pop(i)
                        st.session_state.editing_income = None  # Reset editing state on delete
                        st.rerun()

    with col4:
        st.subheader("Expense Categories")
        if not st.session_state.expense_entries:
            st.caption("No expense categories added yet.")
        else:
            for i, entry in enumerate(st.session_state.expense_entries):
                if st.session_state.editing_expense == i:
                    display_edit_form(entry, i, 'expense', currency_symbol)
                else:
                    col1, col2, col3, col4 = st.columns([0.4, 0.3, 0.15, 0.15])
                    col1.write(entry['type'])
                    col2.write(format_currency(entry['amount'], currency_symbol))
                    if col3.button("Edit", key=f"edit_expense_{i}", use_container_width=True):
                        st.session_state.editing_expense = i
                        st.rerun()
                    if col4.button("Del", key=f"delete_expense_{i}", use_container_width=True):
                        st.session_state.expense_entries.pop(i)
                        st.session_state.editing_expense = None  # Reset editing state on delete
                        st.rerun()

# Calculations
total_income, total_expenses, net_income = calculate_budget()

# Key metrics
st.markdown("---")
st.subheader("Financial Summary")
metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Total Income", format_currency(total_income, currency_symbol))
metric_col2.metric("Total Expenses", format_currency(total_expenses, currency_symbol))
metric_col3.metric(
    "Net Balance",
    format_currency(net_income, currency_symbol),
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
    display_budget_chart(total_income, total_expenses, net_income, multiplier, currency_symbol)

# --- Persist State to Local Storage ---
state_to_persist = {
    "income_entries": st.session_state.income_entries,
    "expense_entries": st.session_state.expense_entries,
    "currency": st.session_state.currency
}
localS.setItem('budget_app_state', json.dumps(state_to_persist))


# Empty state handling
if not st.session_state.income_entries and not st.session_state.expense_entries:
    st.markdown("---")
    st.info("👋 Welcome! Start by adding income sources and expense categories using the forms above.")
