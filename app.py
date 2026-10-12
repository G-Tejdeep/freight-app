import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Freight Cost & Variance Analytics", page_icon="🚢", layout="wide"
)


# Load Transaction Data from CSV (No live SQL required for cloud deployment)
@st.cache_data
def load_data():
  return pd.read_csv("freight_variance_export.csv")


# Load Carrier Tradeoffs Data from CSV or aggregate from export
@st.cache_data
def load_carrier_tradeoffs():
  try:
    return pd.read_csv("cost_leakage_audit_report.csv")
  except Exception:
    df = pd.read_csv("freight_variance_export.csv")
    carrier_summary = (
        df.groupby(["carrier_name", "mode_of_transport"])
        .agg(
            shipments=("transaction_id", "count"),
            avg_rate_paid=("actual_rate_paid_usd", "mean"),
            avg_contract_rate=("contracted_base_rate_usd", "mean"),
            total_leakage_usd=("variance_vs_contract_usd", "sum"),
            avg_transit_days=("transit_days", "mean"),
        )
        .reset_index()
    )
    return carrier_summary


df = load_data().copy()
df_carriers = load_carrier_tradeoffs().copy()

# Dashboard Header
st.title("🚢 Freight Cost & Variance Analytics Engine")
st.markdown(
    "Executive procurement dashboard tracking multi-modal spot-market exposure,"
    " contract compliance, and carrier efficiency."
)

# Sidebar Filters
st.sidebar.header("🔍 Filter Parameters")

# 1. Trade Lane Filter
if not df.empty and {"lane_id", "origin_hub", "destination_hub"}.issubset(
    df.columns
):
  df["lane_display"] = (
      df["lane_id"] + " - " + df["origin_hub"] + " ➔ " + df["destination_hub"]
  )
  selected_lane = st.sidebar.selectbox(
      "Select Trade Lane", ["All"] + sorted(list(df["lane_display"].unique()))
  )
  if selected_lane != "All":
    df = df[df["lane_display"] == selected_lane]

# 2. Carrier Filter
selected_carrier = st.sidebar.selectbox(
    "Select Carrier", ["All"] + sorted(list(df["carrier_name"].unique()))
)
if selected_carrier != "All":
  df = df[df["carrier_name"] == selected_carrier]

# 3. Mode of Transport Filter
selected_mode = st.sidebar.selectbox(
    "Transport Mode", ["All"] + sorted(list(df["mode_of_transport"].unique()))
)
if selected_mode != "All":
  df = df[df["mode_of_transport"] == selected_mode]

# 4. Performance Status Filter (Matches CSV values: High Overspend, Under Contract, Within Tolerance)
selected_status = st.sidebar.selectbox(
    "Performance Status",
    ["All"] + sorted(list(df["cost_performance_status"].unique())),
)
if selected_status != "All":
  df = df[df["cost_performance_status"] == selected_status]

# Create App Tabs for Multi-Page Feel
tab1, tab2 = st.tabs(
    ["📊 Executive Cost & Lane Analytics", "🚚 Carrier Performance & Tiers"]
)

with tab1:
  # KPI Metrics Row
  st.markdown("### 📊 Executive Overview")
  col1, col2, col3, col4 = st.columns(4)

  total_shipments = len(df)
  total_spend = df["actual_rate_paid_usd"].sum() if total_shipments > 0 else 0
  total_leakage = (
      df["variance_vs_contract_usd"].sum() if total_shipments > 0 else 0
  )
  avg_transit = df["transit_days"].mean() if total_shipments > 0 else 0

  col1.metric("Total Shipments", f"{total_shipments:,}")
  col2.metric("Total Freight Spend", f"${total_spend:,.2f}")
  col3.metric(
      "Total Cost Leakage", f"${total_leakage:,.2f}", delta_color="inverse"
  )
  col4.metric("Avg Transit Days", f"{avg_transit:.1f} days")

  st.markdown("---")

  # Trade Lane Summary Breakdown
  st.subheader("🌐 Trade Lane Cost Breakdown")
  if not df.empty:
    lane_summary = (
        df.groupby(
            ["lane_id", "origin_hub", "destination_hub", "mode_of_transport"]
        )
        .agg(
            shipments=("transaction_id", "count"),
            avg_actual=("actual_rate_paid_usd", "mean"),
            avg_contract=("contracted_base_rate_usd", "mean"),
            total_leakage=("variance_vs_contract_usd", "sum"),
        )
        .reset_index()
    )

    lane_summary["trade_lane"] = (
        lane_summary["lane_id"]
        + " - "
        + lane_summary["origin_hub"]
        + " ➔ "
        + lane_summary["destination_hub"]
    )
    lane_summary = lane_summary[[
        "trade_lane",
        "mode_of_transport",
        "shipments",
        "avg_actual",
        "avg_contract",
        "total_leakage",
    ]]
    lane_summary = lane_summary.sort_values(by="total_leakage", ascending=False)

    st.dataframe(
        lane_summary.style.format({
            "avg_actual": "${:,.2f}",
            "avg_contract": "${:,.2f}",
            "total_leakage": "${:,.2f}",
        }),
        use_container_width=True,
    )
  else:
    st.warning("No data matches the selected filters.")

  st.markdown("---")

  # Detailed Transaction View
  st.subheader("📋 Underlying Transactional Audit Log")
  display_df = df.drop(columns=["lane_display"], errors="ignore")
  st.dataframe(display_df, use_container_width=True)

with tab2:
  st.subheader("🏆 Multi-Modal Carrier Tradeoffs & Operational Tiers")
  st.markdown(
      "Evaluating carriers based on speed, cost variance, and overall"
      " operational efficiency tier."
  )

  if not df_carriers.empty:
    st.dataframe(df_carriers, use_container_width=True)
  else:
    st.warning("No carrier tradeoff data found.")
