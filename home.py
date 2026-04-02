import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import json
import os
import urllib.request

# ─────────────────────────────
# DB CONNECTION
# ─────────────────────────────
engine = create_engine("mysql+pymysql://root:12345678@localhost:3306/phone_pe_pulse")

# ─────────────────────────────
# GEOJSON
# ─────────────────────────────
GEOJSON_PATH = "india_states.geojson"
GEOJSON_URL  = (
    "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112"
    "/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
)

def get_geojson():
    if not os.path.exists(GEOJSON_PATH):
        urllib.request.urlretrieve(GEOJSON_URL, GEOJSON_PATH)
    with open(GEOJSON_PATH, "r") as f:
        return json.load(f)

# ─────────────────────────────
# STATE NAME MAP
# ─────────────────────────────
STATE_NAME_MAP = {
    "andaman-&-nicobar-islands":              "Andaman & Nicobar",
    "andhra-pradesh":                          "Andhra Pradesh",
    "arunachal-pradesh":                       "Arunachal Pradesh",
    "assam":                                   "Assam",
    "bihar":                                   "Bihar",
    "chandigarh":                              "Chandigarh",
    "chhattisgarh":                            "Chhattisgarh",
    "dadra-&-nagar-haveli-&-daman-&-diu":     "Dadra and Nagar Haveli and Daman and Diu",
    "delhi":                                   "Delhi",
    "goa":                                     "Goa",
    "gujarat":                                 "Gujarat",
    "haryana":                                 "Haryana",
    "himachal-pradesh":                        "Himachal Pradesh",
    "jammu-&-kashmir":                         "Jammu & Kashmir",
    "jharkhand":                               "Jharkhand",
    "karnataka":                               "Karnataka",
    "kerala":                                  "Kerala",
    "ladakh":                                  "Ladakh",
    "lakshadweep":                             "Lakshadweep",
    "madhya-pradesh":                          "Madhya Pradesh",
    "maharashtra":                             "Maharashtra",
    "manipur":                                 "Manipur",
    "meghalaya":                               "Meghalaya",
    "mizoram":                                 "Mizoram",
    "nagaland":                                "Nagaland",
    "odisha":                                  "Odisha",
    "puducherry":                              "Puducherry",
    "punjab":                                  "Punjab",
    "rajasthan":                               "Rajasthan",
    "sikkim":                                  "Sikkim",
    "tamil-nadu":                              "Tamil Nadu",
    "telangana":                               "Telangana",
    "tripura":                                 "Tripura",
    "uttar-pradesh":                           "Uttar Pradesh",
    "uttarakhand":                             "Uttarakhand",
    "west-bengal":                             "West Bengal",
}

# ─────────────────────────────
# CACHED DATA LOADERS
# ─────────────────────────────
@st.cache_data(ttl=600)
def load_years_quarters():
    q = "SELECT DISTINCT Year, Quarter FROM aggregated_transaction ORDER BY Year, Quarter"
    return pd.read_sql(q, engine)


@st.cache_data(ttl=600)
def load_transaction_map(year, quarter):
    q = f"""
        SELECT State,
            SUM(Transaction_count) AS Total_transactions,
            ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores,
            ROUND(SUM(Transaction_amount)/NULLIF(SUM(Transaction_count),0), 2) AS Avg_txn_value
        FROM aggregated_transaction
        WHERE Year = {year} AND Quarter = {quarter}
        GROUP BY State
    """
    df = pd.read_sql(q, engine)
    df["State_mapped"] = df["State"].map(STATE_NAME_MAP)
    return df


@st.cache_data(ttl=600)
def load_user_map(year, quarter):
    q = f"""
        SELECT State,
            SUM(Registered_user) AS Total_registered_users,
            SUM(App_opens)       AS Total_app_opens
        FROM map_users
        WHERE Year = {year} AND Quarter = {quarter}
        GROUP BY State
    """
    df = pd.read_sql(q, engine)
    df["State_mapped"] = df["State"].map(STATE_NAME_MAP)
    return df


@st.cache_data(ttl=600)
def load_category_data(year, quarter):
    q = f"""
        SELECT Transaction_type,
            SUM(Transaction_count) AS Total_count,
            ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
        FROM aggregated_transaction
        WHERE Year = {year} AND Quarter = {quarter}
        GROUP BY Transaction_type
        ORDER BY Total_count DESC
    """
    return pd.read_sql(q, engine)


@st.cache_data(ttl=600)
def load_overall_kpis(year, quarter):
    q = f"""
        SELECT
            SUM(Transaction_count) AS Total_transactions,
            ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores,
            ROUND(SUM(Transaction_amount)/NULLIF(SUM(Transaction_count),0), 2) AS Avg_txn_value
        FROM aggregated_transaction
        WHERE Year = {year} AND Quarter = {quarter}
    """
    return pd.read_sql(q, engine).iloc[0]


@st.cache_data(ttl=600)
def load_overall_user_kpis(year, quarter):
    q = f"""
        SELECT
            SUM(Registered_user) AS Total_registered_users,
            SUM(App_opens)       AS Total_app_opens
        FROM map_users
        WHERE Year = {year} AND Quarter = {quarter}
    """
    return pd.read_sql(q, engine).iloc[0]


# ─────────────────────────────
# MAIN RENDER FUNCTION
# ─────────────────────────────
def show_home():

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#1a0533 0%,#2d1060 100%);
                    padding:26px 32px;border-radius:16px;margin-bottom:20px;">
            <h1 style="color:#a855f7;margin:0;font-size:2.1rem;font-weight:800;">
                📱 PhonePe Pulse Dashboard
            </h1>
            <p style="color:#c4b5fd;margin:6px 0 0;font-size:0.95rem;">
                Explore India's digital payment landscape — hover over states for live insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        india_geojson = get_geojson()
    except Exception as e:
        st.error(f"Could not load India GeoJSON: {e}")
        return

    try:
        yq_df    = load_years_quarters()
        years    = sorted(yq_df["Year"].unique().tolist())
        quarters = [1, 2, 3, 4]
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    left_col, map_col, right_col = st.columns([1.1, 3.2, 1.7])

    # ══════════════
    # LEFT — FILTERS
    # ══════════════
    with left_col:
        st.markdown("<h4 style='color:#a855f7;margin-bottom:10px;'>🔍 Filters</h4>",
                    unsafe_allow_html=True)

        view_type   = st.radio("View Type", ["Transactions", "Users"], horizontal=False)
        sel_year    = st.selectbox("📅 Year", years, index=len(years) - 1)
        sel_quarter = st.selectbox("📆 Quarter", quarters)

        # ── hardcoded color metric — no selectbox ──
        if view_type == "Transactions":
            color_metric = "Total_transactions"
        else:
            color_metric = "Total_registered_users"

        st.markdown("---")

        try:
            if view_type == "Transactions":
                kpi   = load_overall_kpis(sel_year, sel_quarter)
                cards = [
                    ("#a855f7", "All India Transactions", f"{int(kpi['Total_transactions']):,}"),
                    ("#06b6d4", "Total Payment Value",    f"₹{kpi['Total_amount_crores']:,} Cr"),
                    ("#10b981", "Avg Transaction Value",  f"₹{int(kpi['Avg_txn_value']):,}"),
                ]
            else:
                kpi   = load_overall_user_kpis(sel_year, sel_quarter)
                cards = [
                    ("#a855f7", "Registered Users", f"{int(kpi['Total_registered_users']):,}"),
                    ("#06b6d4", "Total App Opens",  f"{int(kpi['Total_app_opens']):,}"),
                ]
            for color, label, value in cards:
                st.markdown(
                    f"""<div style="background:#1e0a3c;border-radius:11px;padding:13px 16px;
                        border-left:4px solid {color};margin-bottom:10px;">
                        <div style="color:#9ca3af;font-size:0.72rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:.4px;">{label}</div>
                        <div style="color:{color};font-size:1.15rem;font-weight:700;
                            margin-top:3px;">{value}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        except Exception as e:
            st.warning(f"KPI error: {e}")

    # ══════════════
    # CENTRE — MAP
    # ══════════════
    with map_col:
        st.markdown(
            f"<h4 style='color:#a855f7;margin-bottom:4px;'>"
            f"🗺️ India Map — {view_type} &nbsp;|&nbsp; {sel_year} Q{sel_quarter}</h4>",
            unsafe_allow_html=True,
        )

        color_scales = {
            "Total_transactions":     "Purples",
            "Total_amount_crores":    "Blues",
            "Avg_txn_value":          "Greens",
            "Total_registered_users": "Oranges",
            "Total_app_opens":        "Teal",
        }
        label_map = {
            "Total_transactions":     "Transaction Count",
            "Total_amount_crores":    "Amount (Crores ₹)",
            "Avg_txn_value":          "Avg Txn Value (₹)",
            "Total_registered_users": "Registered Users",
            "Total_app_opens":        "App Opens",
        }

        try:
            if view_type == "Transactions":
                df_map     = load_transaction_map(sel_year, sel_quarter)
                hover_data = {
                    "Total_transactions":  ":,",
                    "Total_amount_crores": ":.2f",
                    "Avg_txn_value":       ":,.0f",
                    "State_mapped":        False,
                }
            else:
                df_map     = load_user_map(sel_year, sel_quarter)
                hover_data = {
                    "Total_registered_users": ":,",
                    "Total_app_opens":        ":,",
                    "State_mapped":           False,
                }

            df_map = df_map.dropna(subset=["State_mapped"])

            fig = px.choropleth(
                df_map,
                geojson=india_geojson,
                featureidkey="properties.ST_NM",
                locations="State_mapped",
                color=color_metric,
                color_continuous_scale=color_scales[color_metric],
                hover_name="State_mapped",
                hover_data=hover_data,
                labels={k: v for k, v in label_map.items()},
            )

            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=8, b=0),
                height=560,
                coloraxis_colorbar=dict(
                    title=label_map[color_metric],
                    title_font_color="#c4b5fd",
                    tickfont_color="#c4b5fd",
                    bgcolor="rgba(30,10,60,0.85)",
                    bordercolor="#4c1d95",
                    borderwidth=1,
                    len=0.6,
                ),
                hoverlabel=dict(
                    bgcolor="#1e0a3c",
                    font_color="#e9d5ff",
                    bordercolor="#a855f7",
                    font_size=13,
                ),
            )

            from streamlit.components.v1 import html
            html(fig.to_html(full_html=False, include_plotlyjs='cdn'), height=560)

        except Exception as e:
            st.error(f"Map render error: {e}")

    # ══════════════════
    # RIGHT — CATEGORIES
    # ══════════════════
    with right_col:
        st.markdown("<h4 style='color:#06b6d4;margin-bottom:10px;'>💳 Transactions</h4>",
                    unsafe_allow_html=True)
        st.markdown("<div style='color:#9ca3af;font-size:0.78rem;margin-bottom:12px;'>"
                    "Categories</div>", unsafe_allow_html=True)

        accent = ["#a855f7", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"]
        try:
            df_cat = load_category_data(sel_year, sel_quarter)
            for i, row in df_cat.iterrows():
                c = accent[i % len(accent)]
                st.markdown(
                    f"""<div style="background:#1e0a3c;border-radius:10px;padding:10px 14px;
                        border-left:4px solid {c};margin-bottom:8px;">
                        <div style="color:#9ca3af;font-size:0.7rem;font-weight:600;
                            text-transform:uppercase;">{row['Transaction_type']}</div>
                        <div style="color:{c};font-size:1rem;font-weight:700;margin-top:2px;">
                            {int(row['Total_count']):,}</div>
                        <div style="color:#6b7280;font-size:0.68rem;">
                            ₹{row['Total_amount_crores']:,.2f} Cr</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown("---")
        except Exception as e:
            st.error(f"Category error: {e}")