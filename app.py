
import calendar
import hmac
import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import select, func, or_

from database import (
    SessionLocal,
    init_db,
    User,
    Transaction,
    Budget,
)
from security import hash_password, verify_password


st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
)

init_db()

CATEGORIES = [
    "Food", "Rent", "Transport", "Shopping",
    "Health", "Education", "Entertainment",
    "Bills", "Salary", "Freelance", "Investment", "Other",
]

EXPENSE_CATEGORIES = [c for c in CATEGORIES if c not in (
    "Salary", "Freelance", "Investment"
)]


def money(value):
    return f"₹{value:,.2f}"


def month_bounds(month):
    year, month_number = map(int, month.split("-"))
    start = date(year, month_number, 1)
    last_day = calendar.monthrange(year, month_number)[1]
    end = date(year, month_number, last_day)
    return start, end


def user_transactions(db, user_id, month=None):
    query = select(Transaction).where(
        Transaction.user_id == user_id
    )

    if month:
        start, end = month_bounds(month)
        query = query.where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )

    return list(
        db.scalars(
            query.order_by(Transaction.transaction_date.desc(),
                           Transaction.id.desc())
        ).all()
    )


def show_auth():
    st.title("💰 Smart Expense Tracker")
    st.caption("Understand your spending. Plan your future.")

    login_tab, register_tab = st.tabs(["Login", "Create account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Login", use_container_width=True
            )

        if submitted:
            with SessionLocal() as db:
                user = db.scalar(
                    select(User).where(User.username == username)
                )

                if user and verify_password(password, user.password_hash):
                    st.session_state["user_id"] = user.id
                    st.session_state["username"] = user.username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input(
                "Choose a username", key="register_username"
            ).strip().lower()
            new_password = st.text_input(
                "Choose a password (10+ characters)",
                type="password",
                key="register_password",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="confirm_password",
            )
            register = st.form_submit_button(
                "Create account", use_container_width=True
            )

        if register:
            if not new_username or len(new_username) < 3:
                st.error("Username must contain at least 3 characters.")
            elif len(new_username) > 40 or not all(
                ch.isalnum() or ch in "_-" for ch in new_username
            ):
                st.error("Use only letters, numbers, underscores or hyphens.")
            elif len(new_password) < 10:
                st.error("Password must contain at least 10 characters.")
            elif not hmac.compare_digest(new_password, confirm_password):
                st.error("Passwords do not match.")
            else:
                try:
                    with SessionLocal() as db:
                        if db.scalar(
                            select(User).where(
                                User.username == new_username
                            )
                        ):
                            st.error("That username is already registered.")
                        else:
                            user = User(
                                username=new_username,
                                password_hash=hash_password(new_password),
                            )
                            db.add(user)
                            db.commit()
                            st.success(
                                "Account created. You can now log in."
                            )
                except Exception:
                    st.error("Could not create the account. Try again.")

    st.info(
        "Use a unique password. This project is a portfolio starter, "
        "not a security-audited financial service."
    )


def dashboard(db, user_id, month):
    st.subheader("Financial overview")

    start, end = month_bounds(month)
    income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.kind == "Income",
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
    ) or 0

    expenses = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.kind == "Expense",
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
    ) or 0

    budgets = list(db.scalars(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.month == month,
        )
    ).all())

    a, b, c, d = st.columns(4)
    a.metric("Monthly income", money(income))
    b.metric("Monthly expenses", money(expenses))
    c.metric("Monthly net", money(income - expenses))
    d.metric("Budget categories", len(budgets))

    rows = user_transactions(db, user_id, month)
    expense_rows = [r for r in rows if r.kind == "Expense"]

    left, right = st.columns(2)

    with left:
        st.markdown("#### Spending by category")
        if expense_rows:
            frame = pd.DataFrame([
                {"Category": r.category, "Amount": r.amount}
                for r in expense_rows
            ])
            grouped = frame.groupby("Category", as_index=False)["Amount"].sum()
            fig = px.pie(
                grouped, names="Category", values="Amount",
                hole=0.45,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add expenses to see your spending breakdown.")

    with right:
        st.markdown("#### Budget status")
        if not budgets:
            st.info("Create a budget to monitor your spending.")
        else:
            for budget in budgets:
                spent = sum(
                    r.amount for r in expense_rows
                    if r.category == budget.category
                )
                ratio = spent / budget.limit_amount
                st.write(
                    f"**{budget.category}** — "
                    f"{money(spent)} / {money(budget.limit_amount)}"
                )
                st.progress(min(ratio, 1.0))
                if ratio > 1:
                    st.warning(f"{budget.category} budget exceeded.")
                elif ratio >= 0.8:
                    st.info(f"{budget.category}: 80% or more of budget used.")


def add_transaction(db, user_id):
    st.subheader("Add a transaction")

    with st.form("add_transaction", clear_on_submit=True):
        kind = st.selectbox("Transaction type", ["Expense", "Income"])
        category_options = (
            CATEGORIES if kind == "Income" else EXPENSE_CATEGORIES
        )
        category = st.selectbox("Category", category_options)
        amount = st.number_input(
            "Amount (₹)", min_value=0.01, max_value=1_000_000_000.0,
            value=100.0, step=50.0,
        )
        description = st.text_input(
            "Description", max_chars=200,
            placeholder="e.g. Weekly groceries",
        )
        transaction_date = st.date_input("Date", value=date.today())

        submitted = st.form_submit_button(
            "Save transaction", use_container_width=True
        )

    if submitted:
        db.add(Transaction(
            user_id=user_id,
            kind=kind,
            category=category,
            amount=round(amount, 2),
            description=description.strip(),
            transaction_date=transaction_date,
        ))
        db.commit()
        st.success("Transaction saved.")
        st.rerun()


def manage_transactions(db, user_id, month):
    st.subheader("Transaction history")

    rows = user_transactions(db, user_id, month)
    if not rows:
        st.info("No transactions found for this month.")
        return

    search = st.text_input("Search descriptions or categories")
    filtered = [
        r for r in rows
        if search.lower() in (
            r.description + " " + r.category + " " + r.kind
        ).lower()
    ]

    if filtered:
        frame = pd.DataFrame([
            {
                "ID": r.id,
                "Date": r.transaction_date,
                "Type": r.kind,
                "Category": r.category,
                "Description": r.description,
                "Amount (₹)": r.amount,
            }
            for r in filtered
        ])
        st.dataframe(frame, use_container_width=True, hide_index=True)

    with st.expander("Edit or delete a transaction"):
        options = {f"#{r.id} · {r.transaction_date} · "
                   f"{r.category} · {money(r.amount)}": r.id
                   for r in filtered}

        if not options:
            st.info("No matching transactions to edit.")
            return

        selected_label = st.selectbox("Select transaction", list(options))
        selected_id = options[selected_label]
        record = next(r for r in filtered if r.id == selected_id)

        with st.form("edit_transaction"):
            new_kind = st.selectbox(
                "Type", ["Expense", "Income"],
                index=0 if record.kind == "Expense" else 1,
            )
            new_category = st.selectbox(
                "Category", CATEGORIES,
                index=CATEGORIES.index(record.category),
            )
            new_amount = st.number_input(
                "Amount (₹)", min_value=0.01,
                max_value=1_000_000_000.0,
                value=float(record.amount),
            )
            new_description = st.text_input(
                "Description", value=record.description, max_chars=200
            )
            new_date = st.date_input(
                "Transaction date", value=record.transaction_date
            )
            save_edit = st.form_submit_button("Save changes")

        if save_edit:
            record.kind = new_kind
            record.category = new_category
            record.amount = round(new_amount, 2)
            record.description = new_description.strip()
            record.transaction_date = new_date
            db.commit()
            st.success("Transaction updated.")
            st.rerun()

        if st.button("Delete selected transaction", type="secondary"):
            db.delete(record)
            db.commit()
            st.success("Transaction deleted.")
            st.rerun()


def manage_budgets(db, user_id, month):
    st.subheader("Monthly budgets")

    with st.form("budget_form"):
        category = st.selectbox("Budget category", EXPENSE_CATEGORIES)
        limit_amount = st.number_input(
            "Monthly limit (₹)", min_value=1.0,
            max_value=1_000_000_000.0, value=5000.0, step=500.0,
        )
        save_budget = st.form_submit_button("Save budget")

    if save_budget:
        existing = db.scalar(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.month == month,
                Budget.category == category,
            )
        )
        if existing:
            existing.limit_amount = round(limit_amount, 2)
        else:
            db.add(Budget(
                user_id=user_id,
                month=month,
                category=category,
                limit_amount=round(limit_amount, 2),
            ))
        db.commit()
        st.success("Budget saved.")
        st.rerun()

    budgets = list(db.scalars(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.month == month,
        ).order_by(Budget.category)
    ).all())

    if budgets:
        for budget in budgets:
            col1, col2 = st.columns([4, 1])
            col1.write(
                f"**{budget.category}** — {money(budget.limit_amount)}"
            )
            if col2.button("Delete", key=f"delete_budget_{budget.id}"):
                db.delete(budget)
                db.commit()
                st.rerun()
    else:
        st.info("No budgets configured for this month.")


def export_transactions(db, user_id, month):
    st.subheader("Export your data")
    rows = user_transactions(db, user_id, month)

    if not rows:
        st.info("No transactions to export for this month.")
        return

    frame = pd.DataFrame([
        {
            "date": r.transaction_date.isoformat(),
            "type": r.kind,
            "category": r.category,
            "description": r.description,
            "amount": r.amount,
        }
        for r in rows
    ])

    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=f"expenses-{month}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def main():
    if "user_id" not in st.session_state:
        show_auth()
        return

    user_id = st.session_state["user_id"]
    username = st.session_state.get("username", "User")

    with st.sidebar:
        st.title("💰 Expense Tracker")
        st.write(f"Logged in as **{username}**")
        month = st.date_input(
            "Select month",
            value=date.today().replace(day=1),
        ).strftime("%Y-%m")

        page = st.radio(
            "Navigation",
            ["Dashboard", "Add transaction", "Transactions",
             "Budgets", "Export"],
        )

        if st.button("Log out", use_container_width=True):
            st.session_state.pop("user_id", None)
            st.session_state.pop("username", None)
            st.rerun()

    with SessionLocal() as db:
        if page == "Dashboard":
            dashboard(db, user_id, month)
        elif page == "Add transaction":
            add_transaction(db, user_id)
        elif page == "Transactions":
            manage_transactions(db, user_id, month)
        elif page == "Budgets":
            manage_budgets(db, user_id, month)
        elif page == "Export":
            export_transactions(db, user_id, month)


if __name__ == "__main__":
    main()
