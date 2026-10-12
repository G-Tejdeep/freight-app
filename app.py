import numpy as np
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Freight Cost & Variance Analytics", page_icon="🚢", layout="wide"
)


# Embed self-contained sample data so no SQL or external files are needed
@st.cache_data
def load_bundled_data():
  # Main transactional data mimicking vw_freight_cost_variance
  transactions = {
      "transaction_id": [
          "TRX-1001",
          "TRX-1002",
          "TRX-1003",
          "TRX-1004",
          "TRX-1005",
          "TRX-1006",
          "TRX-1007",
      ],
      "lane_id": [
          "LANE-001",
          "LANE-002",
          "LANE-003",
          "LANE-004",
          "LANE-005",
          "LANE-006",
          "LANE-007",
      ],
      "origin_hub": [
          "Chennai Port",
          "Cochin Port",
          "Mumbai BOM",
          "Mumbai BOM",
          "Delhi DEL",
          "Bangalore",
          "Hyderabad",
      ],
      "destination_hub": [
          "Singapore Port",
          "Hamburg Port",
          "Singapore Port",
          "Frankfurt FRA",
          "Dubai DXB",
          "Chennai",
          "Mumbai",
      ],
      "mode_of_transport": ["Ocean", "Ocean", "Ocean", "Air", "Air", "Road", "Road"],
      "carrier_name": [
          "Maersk",
          "CMA CGM",
          "Maersk",
          "Emirates Skycargo",
          "DHL Aviation",
          "VRL Logistics",
          "Blue Dart",
      ],
      "cost_performance_status": [
          "Optimized",
          "High Overspend",
          "Optimized",
          "Critical Overspend",
          "Critical Overspend",
          "Optimized",
          "Moderate Overspend",
      ],
      "actual_rate_paid_usd": [
          18500.0,
          31200.0,
          19000.0,
          45200.0,
          38100.0,
          4100.0,
          6300.0,
      ],
      "contracted_base_rate_usd": [
          18000.0,
          24000.0,
          19000.0,
          32000.0,
          28000.0,
          3900.0,
          5500.0,
      ],
      "variance_vs_contract_usd": [
          500.0,
          7200.0,
          0.0,
          13200.0,
          10100.0,
          200.0,
          800.0,
      ],
      "transit_days": [14.0, 22.0, 13.0, 2.5, 3.0, 2.0, 1.5],
  }

  # Carrier tradeoffs summary data mimicking vw_carrier_tradeoffs
  carriers = {
      "carrier_name": [
          "Emirates Skycargo",
          "DHL Aviation",
          "CMA CGM",
          "Maersk",
          "Blue Dart",
          "VRL Logistics",
      ],
      "transport_mode": ["Air", "Air", "Ocean", "Ocean", "Road", "Road"],
      "operational_tier": [
          "Tier 1 - Premium",
          "Tier 1 - Premium",
          "Tier 2 - Standard",
          "Tier 1 - Reliable",
          "Tier 2 - Standard",
          "Tier 3 - Economy",
      ],
      "avg_rate_paid": [45200.0, 38100.0, 31200.0, 18500.0, 6300.0, 4100.0],
      "avg_contract_rate": [32000.0, 28000.0, 24000.0, 18000.0, 5500.0, 3900.0],
      "total_leakage_usd": [13200.0, 10100.0, 7200.0, 500.0, 800.0, 200.0],
      "avg_transit_days": [2.5, 3.0, 22.0, 14.0, 1.5, 2.0],
  }

  return pd.DataFrame(transactions), pd.DataFrame(carriers)


df, df_carriers = load_bundled_data()

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
      df["lane_id"] + " (" + df["origin_hub"] + " ➔ " + df["destination_hub"] + ")"
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

# 4. Performance Status Filter
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
    st.dataframe(
        df_carriers.style.format({
            "avg_rate_paid": "${:,.2f}",
            "avg_contract_rate": "${:,.2f}",
            "total_leakage_usd": "${:,.2f}",
            "avg_transit_days": "{:.1f} days",
        }),
        use_container_width=True,
    )
  else:
    st.warning("No carrier tradeoff data found.")
