import pandas as pd, plotly.express as px, streamlit as st
from utils import load_features, load_geojson, GEO_NAME_KEY, BAND_COLORS

st.set_page_config(page_title="Sahaaya", page_icon="🗺️", layout="wide")
st.title("SAHAAYA — Social Vulnerability & Early Warning")
st.caption("Decision-support for exploring district vulnerability. Scores are indicators, not causal claims.")

df = load_features()
year = st.sidebar.selectbox("Year", sorted(df["year"].unique(), reverse=True))
metric_label = st.sidebar.selectbox("Metric", ["Overall", "Education", "Health", "Employment", "Infrastructure"])
metric = {"Overall": "overall_score", "Education": "edu_risk", "Health": "health_risk",
          "Employment": "emp_risk", "Infrastructure": "infra_risk"}[metric_label]

d = df[df["year"] == year]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Districts", len(d))
c2.metric("Avg score", f"{d['overall_score'].mean():.1f}")
c3.metric("High/Critical", int(d["risk_band"].isin(["High", "Critical"]).sum()))
c4.metric("Anomalies flagged", int(d["anomaly_flag"].sum()))

left, right = st.columns([3, 2])
with left:
    geo = load_geojson()
    if geo:
        fig = px.choropleth(d, geojson=geo, locations="district_name",
                            featureidkey=GEO_NAME_KEY, color=metric,
                            color_continuous_scale="YlOrRd", range_color=(0, 100),
                            hover_data=["risk_band", "overall_score"])
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=600)
    else:
        st.warning("No GeoJSON found at data/raw/tn_districts.geojson, showing a bar chart instead.")
        fig = px.bar(d.sort_values(metric), x=metric, y="district_name", orientation="h",
                     color=metric, color_continuous_scale="YlOrRd", height=700)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader(f"Top 10 highest: {metric_label}")
    top = d.sort_values(metric, ascending=False).head(10)[["district_name", metric, "risk_band"]]
    top.columns = ["District", "Score", "Band"]
    st.dataframe(top.round(1), hide_index=True, use_container_width=True)

    st.subheader("Risk band counts")
    counts = d["risk_band"].value_counts().reindex(list(BAND_COLORS)).fillna(0).reset_index()
    counts.columns = ["Band", "Count"]
    st.plotly_chart(px.bar(counts, x="Band", y="Count", color="Band",
                           color_discrete_map=BAND_COLORS).update_layout(showlegend=False, height=250),
                    use_container_width=True)