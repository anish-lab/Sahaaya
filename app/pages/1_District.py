import plotly.express as px, streamlit as st
from utils import load_features, SUB_COLS

st.set_page_config(page_title="District detail", layout="wide")
df = load_features()

district = st.sidebar.selectbox("District", sorted(df["district_name"].unique()))
dd = df[df["district_name"] == district].sort_values("year")
latest = dd.iloc[-1]

st.title(district)
c1, c2, c3 = st.columns(3)
c1.metric("Vulnerability score", f"{latest['overall_score']:.0f} / 100", latest["risk_band"], delta_color="off")
c2.metric("Predicted next year", f"{latest['pred_next_score']:.0f}",
          f"{latest['pred_next_score'] - latest['overall_score']:+.1f}", delta_color="inverse")
c3.metric("Cluster", int(latest["cluster"]))
if latest["anomaly_flag"]:
    st.warning("Flagged as unusual: indicators differ from what similar districts show.")

left, right = st.columns(2)
with left:
    st.subheader("Dimension scores")
    sub = {k: latest[v] for k, v in SUB_COLS.items()}
    fig = px.bar(x=list(sub.values()), y=list(sub.keys()), orientation="h",
                 range_x=[0, 100], color=list(sub.values()), color_continuous_scale="YlOrRd")
    fig.update_layout(coloraxis_showscale=False, xaxis_title="Risk (higher = worse)", yaxis_title="", height=350)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Trend")
    fig = px.line(dd, x="year", y="overall_score", markers=True, range_y=[0, 100])
    fig.update_xaxes(dtick=1).update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Key risk drivers (SHAP)")
st.info("Placeholder: Person A's SHAP values will be plotted here (Day 6).")