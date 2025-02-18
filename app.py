import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def main():
    # Create a sidebar selectbox for navigation
    menu = ["Financial Dashboard", "1.Care Dashboard", "Care+ Dashboard"]
    choice = st.sidebar.selectbox("Select a page", menu)

    # Financial Dashboard Section
    if choice == "Financial Dashboard":
        st.title("📊 Financial Dashboard")
        
        # File uploader for Excel files
        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
        
        # Once a file is uploaded, perform your data analysis
        if uploaded_file is not None:
            # --- 1) Read Excel & Show Data ---
            df = pd.read_excel(uploaded_file)

            with st.expander("Preview of the uploaded data", expanded=False):
                st.dataframe(df)

            # --- 2) Display Some Baseline Info ---
            # Example: daily_working_capital is a fixed reference for your business
            daily_working_capital = 100_000_000  # MMK
            st.info(f"Daily Working Capital (Estimate): {daily_working_capital:,.0f} MMK")

            # --- 3) KPI Calculations ---
            # Make sure these columns exist in your file
            revenue = df["Revenue"].sum()
            gross_profit = df["Gross Profit"].sum()
            net_profit = df["Net Income"].sum()

            # Baseline (previous period) values — update to your real baselines
            previous_revenue = 80_000_000
            previous_gross_profit = 15_000_000
            previous_net_profit = 12_000_000

            revenue_delta = (revenue - previous_revenue) / previous_revenue * 100
            gross_profit_delta = (gross_profit - previous_gross_profit) / previous_gross_profit * 100
            net_profit_delta = (net_profit - previous_net_profit) / previous_net_profit * 100

            # --- 4) Display KPIs Side-by-Side ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Revenue (MMK)", f"{revenue:,.0f}", f"{revenue_delta:.2f}%")
            col2.metric("Gross Profit (MMK)", f"{gross_profit:,.0f}", f"{gross_profit_delta:.2f}%")
            col3.metric("Net Profit (MMK)", f"{net_profit:,.0f}", f"{net_profit_delta:.2f}%")

            # --- 5) Combined Bar + Line Chart ---
            # This chart will display monthly bars for several metrics and lines for Net Income & Cash
            fig = go.Figure()
            bar_metrics = ["Revenue", "COGS", "Gross Profit", "OpEx",
                           "Operating Income", "Other Income and Expenses"]
            for metric in bar_metrics:
                if metric in df.columns:
                    fig.add_trace(
                        go.Bar(x=df["Month"], y=df[metric], name=metric)
                    )
            line_metrics = ["Net Income", "Cash"]
            for metric in line_metrics:
                if metric in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df["Month"],
                            y=df[metric],
                            mode="lines+markers",
                            name=metric
                        )
                    )
            fig.update_layout(
                barmode='group',
                title="Combined Financial Metrics (in MMK)",
                xaxis_title="Month",
                yaxis_title="Amount (MMK)",
                legend_title="Metrics",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 6) Dynamic Working Capital Calculation ---
            # Check if the required columns exist
            needed_cols = {"Cash", "Accounts Receivable (A/R)", "Accounts Payable (A/P)",
                           "Inventory", "Short-Term Liabilities"}
            if needed_cols.issubset(df.columns):
                # Compute Working Capital for each row
                df["Working Capital"] = (
                    df["Cash"] 
                    + df["Accounts Receivable (A/R)"] 
                    + df["Inventory"]
                    - df["Accounts Payable (A/P)"] 
                    - df["Short-Term Liabilities"]
                )

                # Plot it (assuming Month column is present)
                fig_wc = px.line(
                    df,
                    x="Month",
                    y="Working Capital",
                    title="Working Capital Over Time",
                    markers=True
                )
                st.plotly_chart(fig_wc, use_container_width=True)
            else:
                st.warning(
                    "To calculate Working Capital dynamically, your Excel must have:\n"
                    "'Cash', 'Accounts Receivable (A/R)', 'Accounts Payable (A/P)', "
                    "'Inventory', and 'Short-Term Liabilities' columns."
                )

            # --- 7) Additional Metrics (Margins) ---
            # If you have Revenue, Gross Profit, Net Income columns, let's add margin calculations
            if "Revenue" in df.columns and "Gross Profit" in df.columns:
                df["Gross Profit Margin (%)"] = df["Gross Profit"] / df["Revenue"] * 100
            if "Revenue" in df.columns and "Net Income" in df.columns:
                df["Net Profit Margin (%)"] = df["Net Income"] / df["Revenue"] * 100

            with st.expander("View Margins by Month", expanded=False):
                # Show margin columns if they exist
                margin_cols = [col for col in ["Month", "Gross Profit Margin (%)", "Net Profit Margin (%)"] 
                               if col in df.columns]
                if len(margin_cols) > 1:
                    st.dataframe(df[margin_cols])
                else:
                    st.write("Margins not computed because some columns are missing.")

            # --- 8) Income, Expenses & Cash Flow Over Time ---
            # 1) Create a new figure
            fig_income_expenses_cash = go.Figure()

            # 2) Add bar traces for Income and Expenses
            fig_income_expenses_cash.add_trace(
                go.Bar(
                    x=df["Month"],
                    y=df["Revenue"],   # or df["Income"]
                    name="Income"
                )
            )

            fig_income_expenses_cash.add_trace(
                go.Bar(
                    x=df["Month"],
                    y=df["OpEx"],      # your expenses column
                    name="Expenses"
                )
            )

            # 3) Add line trace for Cash Flow on a secondary y-axis
            fig_income_expenses_cash.add_trace(
                go.Scatter(
                    x=df["Month"],
                    y=df["Cash"],      # your cash column
                    mode="lines+markers",
                    name="Cash Flow",
                    yaxis="y2"         # Tells Plotly to use a secondary y-axis
                )
            )

            # 4) Configure layout
            fig_income_expenses_cash.update_layout(
                title="Income, Expenses & Cash Flow (MMK)",
                barmode='group',                  # Group bars side by side
                xaxis=dict(title="Month"),
                yaxis=dict(
                    title="Income/Expenses (MMK)",
                    side="left"
                ),
                yaxis2=dict(
                    title="Cash (MMK)",
                    overlaying="y",              # Overlay on the same plot
                    side="right"                 # Place it on the right side
                ),
                legend_title="Metrics",
                template="plotly_white"
            )

            st.plotly_chart(fig_income_expenses_cash, use_container_width=True)


            # --- 9) Accounts Receivable vs. Accounts Payable Over Time ---
            fig_ar_ap = go.Figure()
            fig_ar_ap.add_trace(
                go.Scatter(
                    x=df["Month"], 
                    y=df["Accounts Receivable (A/R)"],
                    mode="lines+markers",
                    name="A/R"
                )
            )
            fig_ar_ap.add_trace(
                go.Scatter(
                    x=df["Month"], 
                    y=df["Accounts Payable (A/P)"],
                    mode="lines+markers",
                    name="A/P"
                )
            )
            fig_ar_ap.update_layout(
                title="A/R & A/P Trend (MMK)",
                xaxis_title="Month",
                yaxis_title="Amount (MMK)",
                legend_title="Metrics",
                template="plotly_white"
            )
            st.plotly_chart(fig_ar_ap, use_container_width=True)

            # --- 10) Income Progress bar ---
            if "Revenue" in df.columns and "Budget_Income" in df.columns:
                # 1) Grouped bar chart for actual vs. budgeted income
                fig_income_vs_budget = go.Figure()
                fig_income_vs_budget.add_trace(
                    go.Bar(x=df["Month"], y=df["Revenue"], name="Actual Income")
                )
                fig_income_vs_budget.add_trace(
                    go.Bar(x=df["Month"], y=df["Budget_Income"], name="Budgeted Income")
                )
                fig_income_vs_budget.update_layout(
                    barmode='group',
                    title="Actual vs. Budgeted Income",
                    xaxis_title="Month",
                    yaxis_title="MMK",
                    legend_title="Income",
                    template="plotly_white"
                )
                st.plotly_chart(fig_income_vs_budget, use_container_width=True)

                # 2) Overall total income progress
                total_income = df["Revenue"].sum()
                total_income_budget = df["Budget_Income"].sum()
                if total_income_budget > 0:
                    total_income_ratio = total_income / total_income_budget
                else:
                    total_income_ratio = 0
                st.write(
                    f"**Overall Income Usage**: {total_income_ratio * 100:.2f}% of total budgeted income "
                    f"(MMK {total_income:,.0f} / {total_income_budget:,.0f})"
                )
                st.progress(min(total_income_ratio, 1.0))
            else:
                st.warning("No 'Revenue' or 'Budget_Income' column found in Excel. Please add them to track income progress.")


            # --- 11) Expense Progress bar ---
            if "OpEx" in df.columns and "Budget_Expenses" in df.columns:
                # 1) Grouped bar chart: Actual vs. Budget
                fig_expense_vs_budget = go.Figure()
                fig_expense_vs_budget.add_trace(go.Bar(x=df["Month"], y=df["OpEx"], name="Actual Expense"))
                fig_expense_vs_budget.add_trace(go.Bar(x=df["Month"], y=df["Budget_Expenses"], name="Budgeted Expense"))
                fig_expense_vs_budget.update_layout(
                    barmode='group',
                    title="Actual vs. Budgeted Expenses",
                    xaxis_title="Month",
                    yaxis_title="MMK",
                    legend_title="Expenses",
                    template="plotly_white"
                )
                st.plotly_chart(fig_expense_vs_budget, use_container_width=True)

                # 2) Overall total expense progress
                total_expense = df["OpEx"].sum()
                total_budget = df["Budget_Expenses"].sum()

                if total_budget > 0:
                    total_ratio = total_expense / total_budget
                else:
                    total_ratio = 0

                st.write(f"**Overall Usage**: {total_ratio * 100:.2f}% of total budget used "
                        f"({total_expense:,.0f} / {total_budget:,.0f} MMK)")
                st.progress(min(total_ratio, 1.0))

            else:
                st.warning("No 'OpEx' or 'Budget_Expenses' column found in Excel...")


        else:
            st.warning("⚠️ Please upload an Excel file to see the financial chart.")

    # 1.Care Dashboard Section
    elif choice == "1.Care Dashboard":
        st.title("📊 1.Care Dashboard")
        # ... (Your existing 1.Care code remains unchanged) ...
        
    # Care+ Dashboard Section
    else:
        st.title("📊 Care+ Dashboard")
        st.write("Content or metrics related to Care+ go here.")
        # ... (Your existing Care+ code remains unchanged) ...

if __name__ == "__main__":
    main()
