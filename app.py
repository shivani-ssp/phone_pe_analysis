import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from home import show_home

# ─────────────────────────────
# DB CONNECTION
# ─────────────────────────────
engine = create_engine("mysql+pymysql://root:12345678@localhost:3306/phone_pe_pulse")

# ─────────────────────────────
# PAGE CONFIG
# ─────────────────────────────
st.set_page_config(page_title="PhonePe Pulse", layout="wide")

# ─────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────
page = st.sidebar.selectbox("Navigation", ["Home", "Analysis"])

# ─────────────────────────────
# HOME PAGE
# ─────────────────────────────
if page == "Home":
    show_home()

# ─────────────────────────────
# ANALYSIS PAGE
# ─────────────────────────────
if page == "Analysis":
    st.title("Analysis")

    scenario = st.selectbox(
        "Select Scenario",
        [
            "Device Dominance and User Engagement Analysis",
            "Transaction Analysis for Market Expansion",
            "User Engagement and Growth Strategy",
            "Transaction Analysis Across States and Districts",
            "User Registration Analysis",
        ]
    )

    # ══════════════════════════════════════════════════════
    # SCENARIO 1: DEVICE DOMINANCE AND USER ENGAGEMENT
    # Chart types: Horizontal Bar, Funnel, Scatter, Line, Treemap
    # ══════════════════════════════════════════════════════
    if scenario == "Device Dominance and User Engagement Analysis":

        tabs = st.tabs([
            "Q1 Engagement Rate",
            "Q2 Top States",
            "Q3 Underutilized Brands",
            "Q4 Trend Over Time",
            "Q5 Regional Share"
        ])

        # ── Q1: HORIZONTAL BAR ──
        with tabs[0]:
            st.subheader("Engagement Rate by Device Brand")
            st.caption("Chart type: Horizontal Bar — ranks brands by average usage share %")
            query = """
                SELECT User_brand,
                    ROUND(AVG(User_percentage), 2) AS Avg_usage_share_pct
                FROM (
                    SELECT DISTINCT State, Year, Quarter, User_brand,
                                   User_count, User_percentage
                    FROM aggregated_users
                ) AS deduped
                GROUP BY User_brand
                ORDER BY Avg_usage_share_pct ASC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Avg_usage_share_pct"] = df["Avg_usage_share_pct"].astype(float)
                df = df.sort_values("Avg_usage_share_pct", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df["Avg_usage_share_pct"].tolist(),
                    y=df["User_brand"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Avg_usage_share_pct"].tolist(),
                        colorscale="Purples",
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Avg Usage Share: %{x:.2f}%<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Average Usage Share % by Device Brand",
                    height=520,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Avg Usage Share (%)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                        ticksuffix="%",
                    ),
                    yaxis=dict(
                        title=dict(text="Brand", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    margin=dict(r=80, l=120),
                )
                st.plotly_chart(fig, use_container_width=True)
                top = df.iloc[-1]
                st.info(
                    f"🏆 **{top['User_brand']}** leads with "
                    f"**{top['Avg_usage_share_pct']:.1f}%** average usage share — "
                    f"the most popular device brand among PhonePe users."
                )
                st.dataframe(
                    df.sort_values("Avg_usage_share_pct", ascending=False).rename(columns={
                        "User_brand":          "Device Brand",
                        "Avg_usage_share_pct": "Avg Usage Share (%)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q4: BAR COMPARISON CHART ──
        with tabs[3]:
            st.subheader("Top 10 States — Registered Users vs App Opens")
            st.caption("Chart type: Grouped Bar — compares registered users against actual app opens")
            query = """
                SELECT State,
                    SUM(Registered_user) AS Total_registered,
                    SUM(App_opens)       AS Total_app_opens,
                    ROUND(SUM(App_opens)*100.0/NULLIF(SUM(Registered_user),0),2) AS Open_rate_pct
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Registered_user, App_opens
                    FROM map_users
                ) AS deduped
                GROUP BY State
                ORDER BY Total_registered DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered"] = df["Total_registered"].astype(float)
                df["Total_app_opens"]  = df["Total_app_opens"].astype(float)
                df["Open_rate_pct"]    = df["Open_rate_pct"].astype(float)
                df = df.sort_values("Total_registered", ascending=True)

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=df["Total_registered"].tolist(),
                    y=df["State"].tolist(),
                    name="Registered Users",
                    orientation="h",
                    marker_color="#a855f7",
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Registered Users: %{x:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_trace(go.Bar(
                    x=df["Total_app_opens"].tolist(),
                    y=df["State"].tolist(),
                    name="App Opens",
                    orientation="h",
                    marker_color="#06b6d4",
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "App Opens: %{x:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Top 10 States — Registered Users vs App Opens",
                    barmode="group",
                    height=520,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Count", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    yaxis=dict(
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    legend=dict(
                        orientation="h", y=-0.2,
                        font=dict(color="#e9d5ff"),
                    ),
                    margin=dict(l=140, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                top = df.iloc[-1]
                st.info(
                    f"🏆 **{top['State'].title()}** leads with "
                    f"**{top['Total_registered']:,.0f}** registered users and "
                    f"**{top['Open_rate_pct']:.1f}%** open rate."
                )
                st.dataframe(
                    df.sort_values("Total_registered", ascending=False).rename(columns={
                        "Total_registered": "Registered Users",
                        "Total_app_opens":  "App Opens",
                        "Open_rate_pct":    "Open Rate (%)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q3: UNDERUTILIZED BRANDS ──
        with tabs[2]:
            st.subheader("Underutilized vs High Performing Brands")
            st.caption("Chart type: Horizontal Bar — brands classified by average usage share %")
            query = """
                SELECT User_brand,
                    ROUND(AVG(User_percentage), 2) AS Avg_usage_share_pct,
                    CASE
                        WHEN AVG(User_percentage) >= 10 THEN 'High Performer'
                        WHEN AVG(User_percentage) >= 5  THEN 'Mid Tier'
                        ELSE 'Low Performer'
                    END AS Status
                FROM (
                    SELECT DISTINCT State, Year, Quarter, User_brand,
                                   User_count, User_percentage
                    FROM aggregated_users
                ) AS deduped
                GROUP BY User_brand
                ORDER BY Avg_usage_share_pct DESC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Avg_usage_share_pct"] = df["Avg_usage_share_pct"].astype(float)
                df = df.sort_values("Avg_usage_share_pct", ascending=True)

                color_map = {
                    "High Performer": "#4ade80",
                    "Mid Tier":       "#facc15",
                    "Low Performer":  "#f87171",
                }

                order = ["Low Performer", "Mid Tier", "High Performer"]
                fig = go.Figure()
                for status in order:
                    grp = df[df["Status"] == status]
                    fig.add_trace(go.Bar(
                        x=grp["Avg_usage_share_pct"].tolist(),
                        y=grp["User_brand"].tolist(),
                        name=status,
                        orientation="h",
                        marker_color=color_map[status],
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Avg Usage Share: %{x:.2f}%<br>"
                            f"Status: {status}<br>"
                            "<extra></extra>"
                        ),
                    ))

                fig.update_layout(
                    title="Brand Classification Based on Engagement",
                    barmode="overlay",
                    height=540,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Avg Usage Share (%)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                        ticksuffix="%",
                    ),
                    yaxis=dict(
                        title=dict(text="Brand", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    legend=dict(
                        orientation="h", y=-0.2,
                        font=dict(color="#e9d5ff"),
                    ),
                    margin=dict(l=120, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🟢 High Performers (≥10%): "
                    f"{', '.join(df[df['Status']=='High Performer']['User_brand'].tolist())} | "
                    f"🟡 Mid Tier (5–10%): "
                    f"{', '.join(df[df['Status']=='Mid Tier']['User_brand'].tolist())}"
                )
                st.dataframe(
                    df.sort_values("Avg_usage_share_pct", ascending=False).rename(columns={
                        "User_brand":          "Device Brand",
                        "Avg_usage_share_pct": "Avg Usage Share (%)",
                        "Status":              "Classification",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

                     
 
        # ── Q2: PIE CHART — TOP 5 BRANDS ──
        with tabs[1]:
            st.subheader("Top 5 Dominant Device Brands")
            st.caption("Chart type: Pie — national average usage share of top 5 brands")
            query = """
                SELECT User_brand,
                    ROUND(AVG(User_percentage), 2) AS Avg_share_pct
                FROM (
                    SELECT DISTINCT State, Year, Quarter, User_brand,
                                   User_count, User_percentage
                    FROM aggregated_users
                ) AS deduped
                GROUP BY User_brand
                ORDER BY Avg_share_pct DESC
                LIMIT 5
            """
            try:
                df = pd.read_sql(query, engine)
                df["Avg_share_pct"] = df["Avg_share_pct"].astype(float)

                color_map = {
                    "Xiaomi":  "#a855f7",
                    "Samsung": "#06b6d4",
                    "Vivo":    "#10b981",
                    "Oppo":    "#f97316",
                    "Realme":  "#facc15",
                }
                colors = [color_map.get(b, "#e9d5ff") for b in df["User_brand"].tolist()]

                fig = go.Figure(go.Pie(
                    labels=df["User_brand"].tolist(),
                    values=df["Avg_share_pct"].tolist(),
                    hole=0.45,
                    marker=dict(colors=colors),
                    textinfo="label+percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Avg Usage Share: %{value:.2f}%<br>"
                        "Share of Top 5: %{percent}<br>"
                        "<extra></extra>"
                    ),
                    textfont=dict(size=13),
                ))

                fig.update_layout(
                    height=480,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    hovermode="closest",
                    legend=dict(orientation="h", y=-0.15),
                    annotations=[dict(
                        text="Top 5", x=0.5, y=0.5,
                        font_size=14, showarrow=False,
                        font_color="#e9d5ff"
                    )],
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[0]['User_brand']}** leads with "
                    f"**{df.iloc[0]['Avg_share_pct']:.1f}%** avg usage share — "
                    f"followed by {df.iloc[1]['User_brand']} at "
                    f"{df.iloc[1]['Avg_share_pct']:.1f}% and "
                    f"{df.iloc[2]['User_brand']} at {df.iloc[2]['Avg_share_pct']:.1f}%."
                )
                st.dataframe(
                    df.rename(columns={
                        "User_brand":     "Brand",
                        "Avg_share_pct":  "Avg Usage Share (%)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q5: BRAND DIVERSITY INDEX PER STATE ──
        with tabs[4]:
            st.subheader("Brand Diversity Index by State")
            st.caption("Chart type: Line — states ranked by how diversified their device usage is")
            query = """
                SELECT
                    State,
                    COUNT(DISTINCT User_brand)            AS Brand_count,
                    ROUND(MAX(User_percentage), 2)        AS Top_brand_share,
                    ROUND(100 - MAX(User_percentage), 2)  AS Diversity_index
                FROM (
                    SELECT DISTINCT State, Year, Quarter, User_brand,
                                   User_count, User_percentage
                    FROM aggregated_users
                ) AS deduped
                GROUP BY State
                ORDER BY Diversity_index DESC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Diversity_index"] = df["Diversity_index"].astype(float)
                df["Top_brand_share"] = df["Top_brand_share"].astype(float)
                df = df.sort_values("Diversity_index", ascending=True).reset_index(drop=True)

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df["State"].tolist(),
                    y=df["Diversity_index"].tolist(),
                    mode="lines+markers",
                    line=dict(color="#a855f7", width=3),
                    marker=dict(
                        size=8,
                        color=df["Diversity_index"].tolist(),
                        colorscale=[
                            [0.0, "#dc2626"],
                            [0.5, "#facc15"],
                            [1.0, "#4ade80"],
                        ],
                        showscale=True,
                        colorbar=dict(
                            title=dict(text="Diversity", font=dict(color="#e9d5ff")),
                            tickfont=dict(color="#e9d5ff"),
                            thickness=12, len=0.6,
                        ),
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Diversity Index: %{y:.1f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_hline(
                    y=df["Diversity_index"].mean(),
                    line_dash="dash", line_color="#f97316", line_width=2,
                    annotation_text=f"Avg: {df['Diversity_index'].mean():.1f}",
                    annotation_font_color="#f97316",
                    annotation_position="top right",
                )

                fig.update_layout(
                    title="Brand Diversity Index by State (Higher = More Diverse)",
                    height=520,
                    hovermode="x unified",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#e9d5ff", size=10),
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Diversity Index", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    margin=dict(b=160, r=60),
                )
                st.plotly_chart(fig, use_container_width=True)

                most_diverse  = df.iloc[-1]
                least_diverse = df.iloc[0]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <div style="background:#1e0a3c;border-radius:10px;padding:14px;
                                    border-left:4px solid #10b981;">
                            <div style="color:#9ca3af;font-size:0.75rem;">Most Diverse State</div>
                            <div style="color:#10b981;font-size:1.2rem;font-weight:700;">
                                {most_diverse['State'].title()}
                            </div>
                            <div style="color:#6b7280;font-size:0.75rem;">
                                Index: {most_diverse['Diversity_index']} |
                                Brands: {int(most_diverse['Brand_count'])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                with col2:
                    st.markdown(
                        f"""
                        <div style="background:#1e0a3c;border-radius:10px;padding:14px;
                                    border-left:4px solid #ef4444;">
                            <div style="color:#9ca3af;font-size:0.75rem;">Least Diverse State</div>
                            <div style="color:#ef4444;font-size:1.2rem;font-weight:700;">
                                {least_diverse['State'].title()}
                            </div>
                            <div style="color:#6b7280;font-size:0.75rem;">
                                Index: {least_diverse['Diversity_index']} |
                                Brands: {int(least_diverse['Brand_count'])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**Full State Diversity Table**")
                st.dataframe(
                    df.sort_values("Diversity_index", ascending=False).rename(columns={
                        "Brand_count":     "No. of Brands",
                        "Top_brand_share": "Top Brand Share (%)",
                        "Diversity_index": "Diversity Index",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

    # ══════════════════════════════════════════════════════
    # SCENARIO 2: TRANSACTION ANALYSIS FOR MARKET EXPANSION
    # Chart types: Vertical Bar, Donut, Area, Gauge (Indicator), Bubble Scatter
    # ══════════════════════════════════════════════════════
    elif scenario == "Transaction Analysis for Market Expansion": 

        tabs = st.tabs([
            "Q1 Top States by Amount",
            "Q2 Top Transaction Count",
            "Q3 Avg Txn Value by Pay Type",
            "Q4 YoY Growth by State",
            "Q5 Low Transaction States"
        ])

        # ── Q1: VERTICAL BAR ──
        with tabs[0]:
            st.subheader("Top 10 States by Total Transaction Amount")
            st.caption("Chart type: Vertical Bar — compares absolute transaction value across top states")
            query = """
                SELECT State,
                    SUM(Transaction_count)              AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Transaction_type,
                                   Transaction_count, Transaction_amount
                    FROM aggregated_transaction
                ) AS deduped
                GROUP BY State
                ORDER BY Total_amount_crores DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df["Total_transactions"]  = df["Total_transactions"].astype(float)

                fig = go.Figure(go.Bar(
                    x=df["State"].tolist(),
                    y=df["Total_amount_crores"].tolist(),
                    marker=dict(
                        color=df["Total_amount_crores"].tolist(),
                        colorscale="Blues",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Amount: ₹%{y:,.2f} Cr<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Top 10 States by Transaction Amount (Crores)",
                    height=500,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    hovermode="closest",
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#e9d5ff", size=11),
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Amount (Crores ₹)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    bargap=0.3,
                    margin=dict(b=120, t=60),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[0]['State'].title()}** leads with "
                    f"₹{df.iloc[0]['Total_amount_crores']:,.2f} Crores in transactions."
                )
                st.dataframe(
                    df.rename(columns={
                        "Total_transactions":  "Total Transactions",
                        "Total_amount_crores": "Amount (Crores ₹)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q2: TOP 10 STATES BY TRANSACTION COUNT ──
        with tabs[1]:
            st.subheader("Top 10 States by Transaction Count")
            st.caption("Chart type: Line — states driving the highest transaction volume")
            query = """
                SELECT State,
                    SUM(Transaction_count)                AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Transaction_type,
                                   Transaction_count, Transaction_amount
                    FROM aggregated_transaction
                ) AS deduped
                GROUP BY State
                ORDER BY Total_transactions DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_transactions"]  = df["Total_transactions"].astype(float)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df = df.sort_values("Total_transactions", ascending=True)

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df["State"].tolist(),
                    y=df["Total_transactions"].tolist(),
                    mode="lines+markers",
                    line=dict(color="#a855f7", width=3),
                    marker=dict(
                        size=10,
                        color=df["Total_transactions"].tolist(),
                        colorscale=[
                            [0.0, "#6d28d9"],
                            [0.5, "#a855f7"],
                            [1.0, "#e9d5ff"],
                        ],
                        showscale=True,
                        colorbar=dict(
                            title=dict(text="Transactions", font=dict(color="#e9d5ff")),
                            tickfont=dict(color="#e9d5ff"),
                            thickness=12, len=0.6,
                        ),
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Transactions: %{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_hline(
                    y=df["Total_transactions"].mean(),
                    line_dash="dash", line_color="#f97316", line_width=2,
                    annotation_text=f"Avg: {df['Total_transactions'].mean():,.0f}",
                    annotation_font_color="#f97316",
                    annotation_position="top right",
                )

                fig.update_layout(
                    title="Top 10 States by Transaction Count",
                    height=500,
                    hovermode="x unified",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        tickangle=-30,
                        tickfont=dict(color="#e9d5ff", size=11),
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Total Transactions", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    margin=dict(b=100, t=60),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['State'].title()}** leads with "
                    f"**{df.iloc[-1]['Total_transactions']:,.0f}** total transactions."
                )
                st.dataframe(
                    df.sort_values("Total_transactions", ascending=False).rename(columns={
                        "Total_transactions":  "Total Transactions",
                        "Total_amount_crores": "Amount (Crores ₹)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q3: YEAR OVER YEAR TRANSACTION GROWTH ──
        with tabs[3]:
            st.subheader("Year-over-Year Transaction Share")
            st.caption("Chart type: Pie — each year's share of total PhonePe transactions")

            query = """
                SELECT
                    Year,
                    SUM(Transaction_count) AS Total_transactions,
                    ROUND(SUM(Transaction_amount) / 1e7, 2) AS Total_amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Transaction_type,
                                Transaction_count, Transaction_amount
                    FROM aggregated_transaction
                ) AS deduped
                GROUP BY Year
                ORDER BY Year
            """
            try:
                df = pd.read_sql(query, engine)
                df["Year"] = df["Year"].astype(str)

                # ── THIS IS THE FIX ── convert int64 to Python float so Plotly doesn't overflow
                df["Total_transactions"] = df["Total_transactions"].astype(float)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**By Transaction Count**")
                    fig_count = go.Figure(go.Pie(
                        labels=df["Year"].tolist(),
                        values=df["Total_transactions"].tolist(),
                        hole=0.45,
                        marker=dict(colors=[
                            "#6d28d9", "#7c3aed", "#a855f7",
                            "#c084fc", "#d8b4fe", "#ede9fe", "#4c1d95"
                        ]),
                        textinfo="label+percent",
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Transactions: %{value:,.0f}<br>"
                            "Share: %{percent}<extra></extra>"
                        ),
                    ))
                    fig_count.update_layout(
                        height=420,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#e9d5ff",
                        legend=dict(orientation="h", y=-0.35),
                        annotations=[dict(
                            text="Count", x=0.5, y=0.5,
                            font_size=14, showarrow=False,
                            font_color="#e9d5ff"
                        )],
                    )
                    st.plotly_chart(fig_count, use_container_width=True)

                with col2:
                    st.markdown("**By Transaction Amount**")
                    fig_amt = go.Figure(go.Pie(
                        labels=df["Year"].tolist(),
                        values=df["Total_amount_crores"].tolist(),
                        hole=0.45,
                        marker=dict(colors=[
                            "#164e63", "#0e7490", "#06b6d4",
                            "#22d3ee", "#67e8f9", "#a5f3fc", "#083344"
                        ]),
                        textinfo="label+percent",
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Amount: ₹%{value:,.2f} Cr<br>"
                            "Share: %{percent}<extra></extra>"
                        ),
                    ))
                    fig_amt.update_layout(
                        height=420,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#e9d5ff",
                        legend=dict(orientation="h", y=-0.35),
                        annotations=[dict(
                            text="Amount", x=0.5, y=0.5,
                            font_size=14, showarrow=False,
                            font_color="#e9d5ff"
                        )],
                    )
                    st.plotly_chart(fig_amt, use_container_width=True)

                latest  = df.iloc[-1]
                earliest = df.iloc[0]
                growth = ((latest["Total_transactions"] - earliest["Total_transactions"])
                        / earliest["Total_transactions"] * 100)
                st.info(
                    f"📈 Transactions grew **{growth:,.1f}%** from "
                    f"{earliest['Year']} ({earliest['Total_transactions']:,.0f}) "
                    f"to {latest['Year']} ({latest['Total_transactions']:,.0f})"
                )

                st.dataframe(
                    df.rename(columns={
                        "Total_transactions":  "Total Transactions",
                        "Total_amount_crores": "Amount (Crores ₹)",
                    }),
                    use_container_width=True
                )

            except Exception as e:
                st.error(e)

        # ── Q4: AVG TRANSACTION VALUE PER PAYMENT TYPE ──
        with tabs[2]:
            st.subheader("Average Transaction Value by Payment Type")
            st.caption("Chart type: Horizontal Bar — which payment type has the highest ticket size")
            query = """
                SELECT
                    Transaction_type,
                    SUM(Transaction_count) AS Total_count,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores,
                    ROUND(SUM(Transaction_amount)/
                          NULLIF(SUM(Transaction_count),0), 2) AS Avg_txn_value
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Transaction_type,
                                   Transaction_count, Transaction_amount
                    FROM aggregated_transaction
                ) AS deduped
                GROUP BY Transaction_type
                ORDER BY Avg_txn_value ASC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Avg_txn_value"]       = df["Avg_txn_value"].astype(float)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df["Total_count"]         = df["Total_count"].astype(float)

                fig = go.Figure(go.Bar(
                    x=df["Avg_txn_value"].tolist(),
                    y=df["Transaction_type"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Avg_txn_value"].tolist(),
                        colorscale="Blues",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Avg Transaction Value: ₹%{x:,.2f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Average Transaction Value per Payment Type (₹)",
                    height=420,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Avg Transaction Value (₹)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                        tickprefix="₹",
                    ),
                    yaxis=dict(
                        title=dict(text="Payment Type", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    margin=dict(l=180, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)

                top_type = df.iloc[-1]
                st.markdown(
                    f"""
                    <div style="background:#1e0a3c;border-radius:10px;padding:14px;
                                border-left:4px solid #06b6d4;margin-top:10px;">
                        <div style="color:#9ca3af;font-size:0.75rem;">Highest Avg Ticket Size</div>
                        <div style="color:#06b6d4;font-size:1.2rem;font-weight:700;">
                            {top_type['Transaction_type']}
                        </div>
                        <div style="color:#6b7280;font-size:0.8rem;">
                            ₹{int(top_type['Avg_txn_value']):,} per transaction
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                st.dataframe(
                    df.sort_values("Avg_txn_value", ascending=False).rename(columns={
                        "Transaction_type":    "Payment Type",
                        "Total_count":         "Total Transactions",
                        "Total_amount_crores": "Amount (Crores ₹)",
                        "Avg_txn_value":       "Avg Value (₹)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q5: BOTTOM 10 STATES — UNTAPPED MARKETS ──
        with tabs[4]:
            st.subheader("Lowest Transaction States — Expansion Opportunities")
            st.caption("Chart type: Horizontal Bar — states with least activity, prime for expansion")
            query = """
                SELECT
                    State,
                    SUM(Transaction_count)                AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores,
                    COUNT(DISTINCT Year)                  AS Years_active
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Transaction_type,
                                   Transaction_count, Transaction_amount
                    FROM aggregated_transaction
                ) AS deduped
                GROUP BY State
                ORDER BY Total_transactions ASC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_transactions"]  = df["Total_transactions"].astype(float)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df = df.sort_values("Total_transactions", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df["Total_transactions"].tolist(),
                    y=df["State"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Total_transactions"].tolist(),
                        colorscale=[
                            [0.0, "#7f1d1d"],
                            [0.5, "#ef4444"],
                            [1.0, "#fca5a5"],
                        ],
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Total Transactions: %{x:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Bottom 10 States by Transaction Count (Expansion Targets)",
                    height=480,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Total Transactions", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    yaxis=dict(
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    margin=dict(l=200, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"💡 **{df.iloc[0]['State'].title()}** has the lowest transactions at "
                    f"**{df.iloc[0]['Total_transactions']:,.0f}** — "
                    f"prime target for PhonePe's market expansion."
                )
                st.dataframe(
                    df.rename(columns={
                        "Total_transactions":  "Total Transactions",
                        "Total_amount_crores": "Amount (Crores ₹)",
                        "Years_active":        "Years Active",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)
    # ══════════════════════════════════════════════════════
    # SCENARIO 3: USER ENGAGEMENT AND GROWTH STRATEGY
    # Chart types: Choropleth Bar, Horizontal Bar, Bubble, Area, Heatmap
    # ══════════════════════════════════════════════════════
    elif scenario == "User Engagement and Growth Strategy":
        tabs = st.tabs([
            "Q1 Year-wise User Growth",
            "Q2 App Open Rate by District",
            "Q3 Top User Engagement ",
            "Q4 State-wise Registered Users",
            "Q5 Low Engagement Districts"
        ])

       # ── Q1: VERTICAL COLUMN CHART ──
        with tabs[3]:
            st.subheader("State-wise Registered Users vs App Opens")
            st.caption("Chart type: Vertical Bar — registered users vs app opens per state")
            query = """
                SELECT State,
                    SUM(Registered_user) AS Total_registered,
                    SUM(App_opens)       AS Total_app_opens
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Registered_user, App_opens
                    FROM map_users
                ) AS deduped
                GROUP BY State
                ORDER BY Total_app_opens ASC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered"] = df["Total_registered"].astype(float)
                df["Total_app_opens"]  = df["Total_app_opens"].astype(float)

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=df["State"].tolist(),
                    y=df["Total_registered"].tolist(),
                    name="Registered Users",
                    marker_color="#a855f7",
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Registered Users: %{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_trace(go.Bar(
                    x=df["State"].tolist(),
                    y=df["Total_app_opens"].tolist(),
                    name="App Opens",
                    marker_color="#06b6d4",
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "App Opens: %{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    barmode="group",
                    title="Registered Users vs App Opens by State",
                    height=560,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#e9d5ff", size=10),
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Count", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    legend=dict(
                        orientation="h", y=-0.4,
                        font=dict(color="#e9d5ff"),
                    ),
                    bargap=0.2,
                    margin=dict(b=160, t=60),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['State'].title()}** leads with "
                    f"**{df.iloc[-1]['Total_app_opens']:,.0f}** app opens."
                )
                st.dataframe(
                    df.sort_values("Total_app_opens", ascending=False).rename(columns={
                        "Total_registered": "Registered Users",
                        "Total_app_opens":  "App Opens",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q2: HORIZONTAL BAR ──
        with tabs[1]:
            st.subheader("Top 10 Districts by App Open Rate")
            st.caption("Chart type: Horizontal Bar — ranks districts by open rate % for easy comparison")
            query = """
                SELECT District, State,
                    ROUND(SUM(Registered_user) / COUNT(*), 0) AS Total_registered,
                    ROUND(SUM(App_opens) / COUNT(*), 0)       AS Total_app_opens,
                    ROUND(
                        (SUM(App_opens) / COUNT(*)) * 100.0 /
                        NULLIF((SUM(Registered_user) / COUNT(*)), 0)
                    , 2) AS Open_rate_pct
                FROM map_users
                GROUP BY District, State
                HAVING ROUND(SUM(Registered_user) / COUNT(*), 0) > 10000
                ORDER BY Open_rate_pct DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)

                if df.empty:
                    st.warning("No data available.")
                else:
                    df["Open_rate_pct"]    = df["Open_rate_pct"].astype(float)
                    df["Total_registered"] = df["Total_registered"].astype(float)
                    df["Total_app_opens"]  = df["Total_app_opens"].astype(float)
                    df["District_State"]   = df["District"] + " (" + df["State"] + ")"
                    df = df.sort_values("Open_rate_pct", ascending=True)

                    fig = go.Figure(go.Bar(
                        x=df["Open_rate_pct"].tolist(),
                        y=df["District_State"].tolist(),
                        orientation="h",
                        marker=dict(
                            color=df["Open_rate_pct"].tolist(),
                            colorscale="Teal",
                            showscale=False,
                        ),
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Open Rate: %{x:.2f}%<br>"
                            "<extra></extra>"
                        ),
                    ))

                    fig.update_layout(
                        title="Top 10 Districts by App Open Rate %",
                        height=480,
                        hovermode="closest",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#e9d5ff",
                        xaxis=dict(
                            title=dict(text="Open Rate (%)", font=dict(color="#e9d5ff")),
                            tickfont=dict(color="#e9d5ff"),
                            ticksuffix="%",
                        ),
                        yaxis=dict(
                            title=dict(text="District (State)", font=dict(color="#e9d5ff")),
                            tickfont=dict(color="#e9d5ff", size=10),
                        ),
                        margin=dict(l=220, r=40),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.info(
                        f"🏆 **{df.iloc[-1]['District_State']}** has the highest open rate at "
                        f"**{df.iloc[-1]['Open_rate_pct']:.2f}%**"
                    )
                    st.dataframe(
                        df[["District_State", "Total_registered",
                            "Total_app_opens", "Open_rate_pct"]].sort_values(
                            "Open_rate_pct", ascending=False).rename(columns={
                            "District_State":   "District (State)",
                            "Total_registered": "Registered Users",
                            "Total_app_opens":  "App Opens",
                            "Open_rate_pct":    "Open Rate (%)",
                        }),
                        use_container_width=True
                    )
            except Exception as e:
                st.error(e)

        # ── Q3: TOP 5 STATES USER ENGAGEMENT ──
        with tabs[2]:
            st.subheader("Top 5 States by User Engagement")
            st.caption("Chart type: Pie — top 5 states by app opens per registered user")
            query = """
                SELECT State,
                    ROUND(SUM(Registered_user) / COUNT(*), 0) AS Total_registered,
                    ROUND(SUM(App_opens) / COUNT(*), 0)       AS Total_app_opens,
                    ROUND(
                        (SUM(App_opens) / COUNT(*)) /
                        NULLIF((SUM(Registered_user) / COUNT(*)), 0)
                    , 2) AS Opens_per_user
                FROM map_users
                GROUP BY State
                ORDER BY Opens_per_user DESC
                LIMIT 5
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered"] = df["Total_registered"].astype(float)
                df["Total_app_opens"]  = df["Total_app_opens"].astype(float)
                df["Opens_per_user"]   = df["Opens_per_user"].astype(float)

                colors = [
                    "#6d28d9", "#a855f7", "#c084fc", "#d8b4fe", "#e9d5ff"
                ]

                fig = go.Figure(go.Pie(
                    labels=df["State"].tolist(),
                    values=df["Opens_per_user"].tolist(),
                    hole=0.45,
                    marker=dict(colors=colors),
                    textinfo="label+percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Opens per User: %{value:,.2f}<br>"
                        "Share: %{percent}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    height=480,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    hovermode="closest",
                    legend=dict(orientation="h", y=-0.15),
                    annotations=[dict(
                        text="Top 5", x=0.5, y=0.5,
                        font_size=14, showarrow=False,
                        font_color="#e9d5ff"
                    )],
                )
                st.plotly_chart(fig, use_container_width=True)

                st.info(
                    f"🏆 **{df.iloc[0]['State'].title()}** leads with "
                    f"**{df.iloc[0]['Opens_per_user']:,.2f}** app opens per registered user — "
                    f"the most engaged state on PhonePe."
                )
                st.dataframe(
                    df.rename(columns={
                        "Total_registered": "Registered Users",
                        "Total_app_opens":  "App Opens",
                        "Opens_per_user":   "Opens per User",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q4: BAR CHART ──
        with tabs[0]:
            st.subheader("Year-wise Registered User Growth")
            st.caption("Chart type: Bar — registered users per year")
            query = """
                SELECT Year,
                    ROUND(SUM(Registered_user) / COUNT(*), 0) AS Total_registered_users
                FROM map_users
                GROUP BY Year
                ORDER BY Year
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df["Year"] = df["Year"].astype(str)

                fig = go.Figure(go.Bar(
                    x=df["Year"].tolist(),
                    y=df["Total_registered_users"].tolist(),
                    marker_color="#2182CD",
                    hovertemplate="<b>%{x}</b><br>Users: %{y:,.0f}<extra></extra>",
                ))

                fig.update_layout(
                    title="Year-wise Registered User Growth",
                    height=460,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        tickmode="linear",
                        type="category",
                        tickfont=dict(color="#e9d5ff"),
                        title=dict(text="Year", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Registered Users", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    bargap=0.35,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['Year']}** had the most registrations with "
                    f"**{df.iloc[-1]['Total_registered_users']:,.0f}** users."
                )
                st.dataframe(
                    df.rename(columns={
                        "Year":                   "Year",
                        "Total_registered_users": "Registered Users",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q5: LINE CHART ──
        with tabs[4]:
            st.subheader("Low Engagement Districts — Open Rate")
            st.caption("Chart type: Line — app open rate across lowest engagement districts")
            query = """
                SELECT CONCAT(District, ' (', State, ')') AS Label,
                    SUM(Registered_user)  AS Total_registered,
                    SUM(App_opens)        AS Total_app_opens,
                    ROUND(SUM(App_opens)*100.0/NULLIF(SUM(Registered_user),0),2) AS Open_rate_pct
                FROM map_users
                GROUP BY District, State
                HAVING Total_registered > 50000
                ORDER BY Open_rate_pct ASC
                LIMIT 20
            """
            try:
                df = pd.read_sql(query, engine)
                df["Open_rate_pct"]    = df["Open_rate_pct"].astype(float)
                df["Total_registered"] = df["Total_registered"].astype(float)
                df["Total_app_opens"]  = df["Total_app_opens"].astype(float)

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df["Label"].tolist(),
                    y=df["Open_rate_pct"].tolist(),
                    mode="lines+markers",
                    name="Open Rate %",
                    line=dict(color="#f97316", width=3),
                    marker=dict(
                        size=10,
                        color=df["Open_rate_pct"].tolist(),
                        colorscale=[[0.0,"#dc2626"],[0.5,"#facc15"],[1.0,"#4ade80"]],
                        showscale=True,
                        colorbar=dict(
                            title=dict(text="Open Rate %", font=dict(color="#e9d5ff")),
                            tickfont=dict(color="#e9d5ff"),
                            thickness=12, len=0.6,
                        ),
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Open Rate: %{y:.2f}%<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_hline(
                    y=df["Open_rate_pct"].mean(),
                    line_dash="dash", line_color="#a855f7", line_width=2,
                    annotation_text=f"Avg: {df['Open_rate_pct'].mean():.2f}%",
                    annotation_font_color="#a855f7",
                    annotation_position="top right",
                )

                fig.update_layout(
                    title="Bottom 20 Districts by App Open Rate",
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#e9d5ff", size=10),
                        title=dict(text="District (State)", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Open Rate (%)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    hovermode="x unified",
                    height=520,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    margin=dict(b=160),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"💡 **{df.iloc[0]['Label']}** has the lowest engagement at "
                    f"**{df.iloc[0]['Open_rate_pct']:.2f}%** open rate — "
                    f"ideal target for re-engagement campaigns."
                )
                st.dataframe(df.rename(columns={
                    "Total_registered": "Registered Users",
                    "Total_app_opens":  "App Opens",
                    "Open_rate_pct":    "Open Rate (%)",
                }), use_container_width=True)

            except Exception as e:
                st.error(e)

    # ══════════════════════════════════════════════════════
    # SCENARIO 4: TRANSACTION ANALYSIS ACROSS STATES & DISTRICTS
    # Chart types: Horizontal Bar, Horizontal Bar, Sunburst, Treemap, Line
    # ══════════════════════════════════════════════════════
    elif scenario == "Transaction Analysis Across States and Districts": 

        tabs = st.tabs([
            "Q1 Top Districts by Volume",
            "Q2 Top Pincodes",
            "Q3 Top Districts by Value",
            "Q4 State-District Breakdown",
            "Q5 Quarter-wise District Trend"
        ])

        # ── Q1: HORIZONTAL BAR ──
        with tabs[0]:
            st.subheader("Top 10 Districts by Transaction Volume")
            st.caption("Chart type: Horizontal Bar — clearly ranks districts by count from highest to lowest")
            query = """
                SELECT District, State,
                    SUM(Transaction_count)                AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Transaction_count, Transaction_amount
                    FROM top_transaction_district
                ) AS deduped
                GROUP BY District, State
                ORDER BY Total_transactions DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_transactions"]  = df["Total_transactions"].astype(float)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df["District_State"]      = df["District"] + " (" + df["State"] + ")"
                df = df.sort_values("Total_transactions", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df["Total_transactions"].tolist(),
                    y=df["District_State"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Total_transactions"].tolist(),
                        colorscale="Blues",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Transactions: %{x:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Top 10 Districts by Transaction Count",
                    height=480,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Transaction Count", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    yaxis=dict(
                        title=dict(text="District (State)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff", size=10),
                    ),
                    margin=dict(l=220, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['District_State']}** leads with "
                    f"**{df.iloc[-1]['Total_transactions']:,.0f}** transactions."
                )
                st.dataframe(
                    df.sort_values("Total_transactions", ascending=False).rename(columns={
                        "District_State":      "District (State)",
                        "Total_transactions":  "Total Transactions",
                        "Total_amount_crores": "Amount (Crores ₹)",
                    })[["District (State)", "Total Transactions", "Amount (Crores ₹)"]],
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q2: HORIZONTAL BAR ──
        with tabs[2]:
            st.subheader("Top 10 Districts by Transaction Amount")
            st.caption("Chart type: Horizontal Bar — ranks districts by total transaction amount")
            query = """
                SELECT District, State,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Transaction_count, Transaction_amount
                    FROM top_transaction_district
                ) AS deduped
                GROUP BY District, State
                ORDER BY Total_amount_crores DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df["District_State"]      = df["District"] + " (" + df["State"] + ")"
                df = df.sort_values("Total_amount_crores", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df["Total_amount_crores"].tolist(),
                    y=df["District_State"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Total_amount_crores"].tolist(),
                        colorscale="Purples",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Amount: ₹%{x:,.2f} Cr<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Top 10 Districts by Transaction Amount (Crores)",
                    height=480,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Amount (Crores ₹)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                        tickprefix="₹",
                    ),
                    yaxis=dict(
                        title=dict(text="District (State)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff", size=10),
                    ),
                    margin=dict(l=220, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['District_State']}** leads with "
                    f"₹**{df.iloc[-1]['Total_amount_crores']:,.2f}** Crores in transactions."
                )
                st.dataframe(
                    df.sort_values("Total_amount_crores", ascending=False).rename(columns={
                        "District_State":      "District (State)",
                        "Total_amount_crores": "Amount (Crores ₹)",
                    })[["District (State)", "Amount (Crores ₹)"]],
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q3: PIE CHART — TOP 10 PINCODES ──
        with tabs[1]:
            st.subheader("Top 10 Pincodes by Transaction Amount")
            st.caption("Chart type: Pie — share of transaction amount across top 10 pincodes")
            query = """
                SELECT Pincode, State,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Pincode,
                                   Transaction_count, Transaction_amount
                    FROM top_transaction_pincode
                ) AS deduped
                GROUP BY Pincode, State
                ORDER BY Total_amount_crores DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_amount_crores"] = df["Total_amount_crores"].astype(float)
                df["Pincode"]  = df["Pincode"].astype(str)
                df["Label"]    = df["Pincode"] + " (" + df["State"] + ")"

                fig = go.Figure(go.Pie(
                    labels=df["Label"].tolist(),
                    values=df["Total_amount_crores"].tolist(),
                    hole=0.4,
                    marker=dict(colors=[
                        "#4c1d95", "#6d28d9", "#7c3aed", "#8b5cf6",
                        "#a855f7", "#c084fc", "#d8b4fe", "#e9d5ff",
                        "#f3e8ff", "#ede9fe",
                    ]),
                    textinfo="label+percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Amount: ₹%{value:,.2f} Cr<br>"
                        "Share: %{percent}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    height=500,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    hovermode="closest",
                    legend=dict(orientation="h", y=-0.2),
                    annotations=[dict(
                        text="Top 10", x=0.5, y=0.5,
                        font_size=13, showarrow=False,
                        font_color="#e9d5ff"
                    )],
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[0]['Label']}** leads with "
                    f"₹**{df.iloc[0]['Total_amount_crores']:,.2f}** Crores — "
                    f"{df.iloc[0]['Total_amount_crores']/df['Total_amount_crores'].sum()*100:.1f}% "
                    f"of top 10 total."
                )
                st.dataframe(
                    df[["Label", "Total_amount_crores"]].rename(columns={
                        "Label":              "Pincode (State)",
                        "Total_amount_crores": "Amount (Crores ₹)",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q4: COLUMN CHART ──
        with tabs[3]:
            st.subheader("Top 10 States — Transaction Breakdown")
            st.caption("Chart type: Column — transaction amount across top 10 states")
            query = """
                SELECT State,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Amount_crores
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Transaction_count, Transaction_amount
                    FROM top_transaction_district
                ) AS deduped
                GROUP BY State
                ORDER BY Amount_crores DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Amount_crores"] = df["Amount_crores"].astype(float)

                fig = go.Figure(go.Bar(
                    x=df["State"].tolist(),
                    y=df["Amount_crores"].tolist(),
                    marker=dict(
                        color=df["Amount_crores"].tolist(),
                        colorscale=[[0.0,"#4c1d95"],[0.5,"#a855f7"],[1.0,"#e9d5ff"]],
                        showscale=True,
                        colorbar=dict(
                            title=dict(text="Crores ₹", font=dict(color="#e9d5ff")),
                            tickfont=dict(color="#e9d5ff"),
                            thickness=12, len=0.6,
                        ),
                    ),
                    text=df["Amount_crores"].apply(lambda x: f"₹{x:,.0f} Cr"),
                    textposition="outside",
                    textfont=dict(color="#e9d5ff", size=10),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Amount: ₹%{y:,.2f} Cr<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_hline(
                    y=df["Amount_crores"].mean(),
                    line_dash="dash", line_color="#f97316", line_width=2,
                    annotation_text=f"Avg: ₹{df['Amount_crores'].mean():,.0f} Cr",
                    annotation_font_color="#f97316",
                    annotation_position="top right",
                )

                fig.update_layout(
                    title="Top 10 States by Transaction Amount",
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#e9d5ff", size=11),
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Amount (Crores ₹)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    height=540,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    showlegend=False,
                    bargap=0.3,
                    margin=dict(b=120, t=80),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[0]['State'].title()}** leads with "
                    f"₹{df.iloc[0]['Amount_crores']:,.0f} Crores in transactions."
                )
                st.dataframe(df.rename(columns={
                    "Amount_crores": "Amount (Crores ₹)"
                }), use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q5: PIE CHART ──
        with tabs[4]:
            st.subheader("Top 5 Districts — Transaction Share")
            st.caption("Chart type: Pie — share of total transactions across top 5 districts")
            query = """
                SELECT District, State,
                    SUM(Transaction_count) AS Total_transactions
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Transaction_count, Transaction_amount
                    FROM map_transaction
                ) AS deduped
                WHERE District IN (
                    SELECT District FROM (
                        SELECT District FROM map_transaction
                        GROUP BY District
                        ORDER BY SUM(Transaction_count) DESC
                        LIMIT 5
                    ) AS top_districts
                )
                GROUP BY District, State
                ORDER BY Total_transactions DESC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_transactions"] = df["Total_transactions"].astype(float)
                df["Label"] = df["District"] + " (" + df["State"] + ")"

                fig = go.Figure(go.Pie(
                    labels=df["Label"].tolist(),
                    values=df["Total_transactions"].tolist(),
                    hole=0.45,
                    marker=dict(colors=[
                        "#6d28d9", "#a855f7", "#f97316", "#06b6d4", "#facc15"
                    ]),
                    textinfo="label+percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Transactions: %{value:,.0f}<br>"
                        "Share: %{percent}<extra></extra>"
                    ),
                ))
                fig.update_layout(
                    height=480,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff", 
                    legend=dict(orientation="h", y=-0.15),
                    annotations=[dict(
                        text="Top 5", x=0.5, y=0.5,
                        font_size=14, showarrow=False,
                        font_color="#e9d5ff"
                    )],
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[0]['Label']}** leads with "
                    f"**{df.iloc[0]['Total_transactions']:,.0f}** transactions — "
                    f"{df.iloc[0]['Total_transactions']/df['Total_transactions'].sum()*100:.1f}% of top 5 total."
                )
                st.dataframe(df.rename(columns={
                    "Total_transactions": "Total Transactions",
                    "Label": "District (State)",
                })[["District (State)", "Total Transactions"]], use_container_width=True)
            except Exception as e:
                st.error(e)

    # ══════════════════════════════════════════════════════
    # SCENARIO 5: USER REGISTRATION ANALYSIS
    # Chart types: Bar, Horizontal Bar, Sunburst, Funnel, Line+Bar combo
    # ══════════════════════════════════════════════════════
    elif scenario == "User Registration Analysis": 

        tabs = st.tabs([
            "Q1 Top States by Registration",
            "Q2 Top Districts by Registration",
            "Q3 Top Pincodes by Registration",
            "Q4 Year-Quarter Filter",
            "Q5 Registration Growth Trend"
        ])

        # ── Q1: VERTICAL BAR ──
        with tabs[0]:
            st.subheader("Top 10 States by Total Registered Users")
            st.caption("Chart type: Vertical Bar — straightforward comparison of registration volume per state")
            query = """
                SELECT State,
                    SUM(Registered_user) AS Total_registered_users
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Registered_user
                    FROM top_users_district
                ) AS deduped
                GROUP BY State
                ORDER BY Total_registered_users ASC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df = df.sort_values("Total_registered_users", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df["State"].tolist(),
                    y=df["Total_registered_users"].tolist(),
                    marker=dict(
                        color=df["Total_registered_users"].tolist(),
                        colorscale="Purples",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Registered Users: %{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Top 10 States by Registered Users",
                    height=500,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        tickangle=-30,
                        tickfont=dict(color="#e9d5ff", size=11),
                        title=dict(text="State", font=dict(color="#e9d5ff")),
                    ),
                    yaxis=dict(
                        title=dict(text="Registered Users", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    bargap=0.3,
                    margin=dict(b=100, t=60),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['State'].title()}** leads with "
                    f"**{df.iloc[-1]['Total_registered_users']:,.0f}** registered users."
                )
                st.dataframe(
                    df.sort_values("Total_registered_users", ascending=False).rename(columns={
                        "Total_registered_users": "Registered Users",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        

        # ── Q3: PIE CHART — TOP 10 PINCODES BY REGISTERED USERS ──
        with tabs[2]:
            st.subheader("Top 10 Pincodes by Registered Users")
            st.caption("Chart type: Pie — share of registered users across top 10 pincodes")
            query = """
                SELECT Pincode, State,
                    SUM(Registered_user) AS Total_registered_users
                FROM (
                    SELECT DISTINCT State, Year, Quarter, Pincode,
                                   Registered_user
                    FROM top_users_pincode
                ) AS deduped
                GROUP BY Pincode, State
                ORDER BY Total_registered_users DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df["Pincode"] = df["Pincode"].astype(str)
                df["Label"]   = df["Pincode"] + " (" + df["State"] + ")"

                fig = go.Figure(go.Pie(
                    labels=df["Label"].tolist(),
                    values=df["Total_registered_users"].tolist(),
                    hole=0.4,
                    marker=dict(colors=[
                        "#4c1d95", "#6d28d9", "#7c3aed", "#8b5cf6",
                        "#a855f7", "#c084fc", "#d8b4fe", "#e9d5ff",
                        "#f3e8ff", "#ede9fe",
                    ]),
                    textinfo="label+percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Registered Users: %{value:,.0f}<br>"
                        "Share: %{percent}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    height=500,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    hovermode="closest",
                    legend=dict(orientation="h", y=-0.2),
                    annotations=[dict(
                        text="Top 10", x=0.5, y=0.5,
                        font_size=13, showarrow=False,
                        font_color="#e9d5ff"
                    )],
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[0]['Label']}** leads with "
                    f"**{df.iloc[0]['Total_registered_users']:,.0f}** registered users — "
                    f"{df.iloc[0]['Total_registered_users']/df['Total_registered_users'].sum()*100:.1f}% "
                    f"of top 10 total."
                )
                st.dataframe(
                    df[["Label", "Total_registered_users"]].rename(columns={
                        "Label":                 "Pincode (State)",
                        "Total_registered_users": "Registered Users",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q3: HORIZONTAL BAR ──
        with tabs[1]:
            st.subheader("Top 10 Districts by Registered Users")
            st.caption("Chart type: Horizontal Bar — long district names fit better horizontally")
            query = """
                SELECT District, State,
                    SUM(Registered_user) AS Total_registered_users
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District,
                                   Registered_user
                    FROM top_users_district
                ) AS deduped
                GROUP BY District, State
                ORDER BY Total_registered_users ASC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"

                fig = go.Figure(go.Bar(
                    x=df["Total_registered_users"].tolist(),
                    y=df["District_State"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Total_registered_users"].tolist(),
                        colorscale="Blues",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Registered Users: %{x:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))
                fig.update_layout(
                    title="Top 10 Districts by Registered Users",
                    height=480,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Registered Users", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    yaxis=dict(
                        title=dict(text="District (State)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff", size=10),
                    ),
                    margin=dict(l=220, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info(
                    f"🏆 **{df.iloc[-1]['District_State']}** leads with "
                    f"**{df.iloc[-1]['Total_registered_users']:,.0f}** registered users."
                )
                st.dataframe(
                    df.sort_values("Total_registered_users", ascending=False).rename(columns={
                        "District_State":        "District (State)",
                        "Total_registered_users": "Registered Users",
                    })[["District (State)", "Registered Users"]],
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q4: LINE CHART — YEAR WISE DISTRICT GROWTH ──
        with tabs[3]:
            st.subheader("Top Districts — Year-wise Registration Trend")
            st.caption("Chart type: Line — tracks registration growth of top districts over years")
            try:
                year_q = pd.read_sql(
                    "SELECT DISTINCT Year, Quarter FROM top_users_district ORDER BY Year, Quarter",
                    engine
                )
                years    = sorted(year_q["Year"].unique().tolist())
                quarters = sorted(year_q["Quarter"].unique().tolist())

                col1, col2 = st.columns(2)
                with col1:
                    sel_year = st.selectbox("Select Year", years)
                with col2:
                    sel_quarter = st.selectbox("Select Quarter", quarters)

                query = f"""
                    SELECT District, State,
                        SUM(Registered_user) AS Total_registered_users
                    FROM (
                        SELECT DISTINCT State, Year, Quarter, District, Registered_user
                        FROM top_users_district
                    ) AS deduped
                    WHERE Year = {sel_year} AND Quarter = {sel_quarter}
                    GROUP BY District, State
                    ORDER BY Total_registered_users DESC
                    LIMIT 12
                """
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"
                df = df.sort_values("Total_registered_users", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df["Total_registered_users"].tolist(),
                    y=df["District_State"].tolist(),
                    orientation="h",
                    marker=dict(
                        color=df["Total_registered_users"].tolist(),
                        colorscale="Purples",
                        showscale=False,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Registered Users: %{x:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title=f"Top Districts by Registered Users — {sel_year} Q{sel_quarter}",
                    height=540,
                    hovermode="closest",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    xaxis=dict(
                        title=dict(text="Registered Users", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff"),
                    ),
                    yaxis=dict(
                        title=dict(text="District (State)", font=dict(color="#e9d5ff")),
                        tickfont=dict(color="#e9d5ff", size=10),
                    ),
                    margin=dict(l=220, r=40),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(
                    df.sort_values("Total_registered_users", ascending=False).rename(columns={
                        "District_State":        "District (State)",
                        "Total_registered_users": "Registered Users",
                    })[["District (State)", "Registered Users"]],
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q5: COMBO LINE + BAR ──
        with tabs[4]:
            st.subheader("User Registration Growth Trend Over Time")
            st.caption("Chart type: Combo (Bar + Line) — bars = new quarterly registrations, line = cumulative total")
            query = """
                SELECT Year, Quarter,
                    SUM(Registered_user) AS Total_registered_users
                FROM (
                    SELECT DISTINCT State, Year, Quarter, District, Registered_user
                    FROM top_users_district
                ) AS deduped
                GROUP BY Year, Quarter
                ORDER BY Year, Quarter
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df["Period"]          = df["Year"].astype(str) + " Q" + df["Quarter"].astype(str)
                df["Cumulative_users"] = df["Total_registered_users"].cumsum()

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=df["Period"].tolist(),
                    y=df["Total_registered_users"].tolist(),
                    name="New Registrations",
                    marker=dict(
                        color=df["Total_registered_users"].tolist(),
                        colorscale=[[0.0,"#6d28d9"],[1.0,"#c084fc"]],
                        showscale=False,
                    ),
                    yaxis="y1",
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "New Registrations: %{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.add_trace(go.Scatter(
                    x=df["Period"].tolist(),
                    y=df["Cumulative_users"].tolist(),
                    name="Cumulative Users",
                    mode="lines+markers",
                    line=dict(color="#06b6d4", width=3),
                    marker=dict(size=6, color="#06b6d4"),
                    yaxis="y2",
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Cumulative: %{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    title="Quarterly New Registrations vs Cumulative Users",
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#e9d5ff", size=9),
                        title=dict(text="Quarter", font=dict(color="#e9d5ff")),
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title=dict(text="New Registrations", font=dict(color="#a855f7")),
                        tickfont=dict(color="#a855f7"),
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.05)",
                    ),
                    yaxis2=dict(
                        title=dict(text="Cumulative Users", font=dict(color="#06b6d4")),
                        tickfont=dict(color="#06b6d4"),
                        overlaying="y",
                        side="right",
                        showgrid=False,
                    ),
                    hovermode="x unified",
                    height=520,
                    legend=dict(
                        orientation="h", y=1.08,
                        font=dict(color="#e9d5ff"),
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    bargap=0.2,
                    margin=dict(b=100, t=60),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(
                    df[["Period", "Total_registered_users", "Cumulative_users"]].rename(columns={
                        "Period":                 "Quarter",
                        "Total_registered_users": "New Registrations",
                        "Cumulative_users":       "Cumulative Users",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)