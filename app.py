
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "supplier_reliability.db"

st.set_page_config(
    page_title="Supplier Reliability Dashboard",
    layout="wide",
)

st.title("Supplier Reliability Scoring System")
st.caption("YottaFlex.ai Challenge | Supplier Performance Analytics")


@st.cache_data
def load_data():
    with sqlite3.connect(DB_PATH) as connection:
        suppliers = pd.read_sql_query(
            "SELECT * FROM Supplier", connection
        )
        scores = pd.read_sql_query(
            "SELECT * FROM SupplierScore", connection
        )
        risks = pd.read_sql_query(
            "SELECT * FROM RiskSignal", connection
        )
    return suppliers, scores, risks


try:
    suppliers, scores, risks = load_data()
except Exception as error:
    st.error(f"Could not load database: {error}")
    st.stop()

data = scores.merge(suppliers, on="supplier_id", how="left")

st.sidebar.header("Filters")

bands = sorted(data["reliability_band"].dropna().unique())
selected_bands = st.sidebar.multiselect(
    "Reliability band",
    bands,
    default=bands,
)

countries = sorted(data["country"].dropna().unique())
selected_countries = st.sidebar.multiselect(
    "Supplier country",
    countries,
    default=countries,
)

filtered = data[
    data["reliability_band"].isin(selected_bands)
    & data["country"].isin(selected_countries)
].copy()

if filtered.empty:
    st.warning("No suppliers match the selected filters.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Suppliers", f"{len(filtered):,}")
c2.metric("Average reliability", f"{filtered['final_score'].mean():.2f}")
c3.metric(
    "Excellent suppliers",
    int((filtered["reliability_band"] == "EXCELLENT").sum()),
)
c4.metric(
    "Average delivery score",
    f"{filtered['delivery_score'].mean():.2f}",
)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Reliability Band Distribution")
    band_counts = (
        filtered["reliability_band"]
        .value_counts()
        .rename_axis("Reliability Band")
        .reset_index(name="Suppliers")
    )
    fig = px.pie(
        band_counts,
        names="Reliability Band",
        values="Suppliers",
        hole=0.45,
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Reliability Score Distribution")
    fig = px.histogram(
        filtered,
        x="final_score",
        nbins=20,
        labels={"final_score": "Reliability Score"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Average Component Scores")

component_columns = {
    "delivery_score": "Delivery",
    "quality_score": "Quality",
    "cost_score": "Cost",
    "capacity_score": "Capacity",
    "compliance_score": "Compliance",
    "disruption_score": "Disruption",
}

component_data = pd.DataFrame({
    "Component": [component_columns[c] for c in component_columns],
    "Average Score": [
        filtered[c].mean() for c in component_columns
    ],
})

fig = px.bar(
    component_data,
    x="Component",
    y="Average Score",
    range_y=[0, 100],
    text_auto=".1f",
)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Top 10 Suppliers")
    top = filtered.nlargest(10, "final_score")
    st.dataframe(
        top[["supplier_id", "supplier_name", "country",
             "final_score", "reliability_band"]],
        hide_index=True,
        use_container_width=True,
    )

with right:
    st.subheader("Lowest 10 Suppliers")
    bottom = filtered.nsmallest(10, "final_score")
    st.dataframe(
        bottom[["supplier_id", "supplier_name", "country",
                "final_score", "reliability_band"]],
        hide_index=True,
        use_container_width=True,
    )
st.subheader("Individual Supplier Analysis")

supplier_options = filtered.sort_values("supplier_id")["supplier_id"].tolist()
selected_supplier = st.selectbox(
    "Select supplier",
    supplier_options,
)

detail = filtered[
    filtered["supplier_id"] == selected_supplier
].iloc[0]

a, b, c = st.columns(3)
a.metric("Reliability score", f"{detail['final_score']:.2f}")
b.metric("Reliability band", detail["reliability_band"])
c.metric("Country", detail["country"])

detail_scores = pd.DataFrame({
    "Component": [component_columns[c] for c in component_columns],
    "Score": [detail[c] for c in component_columns],
})

fig = px.bar(
    detail_scores,
    x="Component",
    y="Score",
    range_y=[0, 100],
    text_auto=".1f",
    title=f"Score Breakdown — {selected_supplier}",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Supplier Risk Signals")

supplier_risks = risks[
    risks["supplier_id"] == selected_supplier
].sort_values("severity", ascending=False)

if supplier_risks.empty:
    st.info("No risk signals found for this supplier.")
else:
    st.dataframe(
        supplier_risks[
            ["signal_type", "severity", "source", "signal_time"]
        ],
        hide_index=True,
        use_container_width=True,
    )
st.subheader("Export Results")

csv_data = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Supplier Report (CSV)",
    data=csv_data,
    file_name="supplier_reliability_report.csv",
    mime="text/csv",
)

st.caption(
    "Scores are generated by a preliminary rule-based model "
    "using synthetic challenge data. Review scoring assumptions "
    "before using the scores for real supplier decisions."
)