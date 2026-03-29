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
                    SUM(User_count) AS Total_registrations,
                    ROUND(AVG(User_percentage), 2) AS Avg_usage_share_pct
                FROM aggregated_users
                GROUP BY User_brand
                ORDER BY Avg_usage_share_pct DESC
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(df, x="Avg_usage_share_pct", y="User_brand",
                             orientation="h", text="Avg_usage_share_pct",
                             title="Average Usage Share % by Device Brand",
                             color="Avg_usage_share_pct",
                             color_continuous_scale="Purples",
                             labels={"Avg_usage_share_pct": "Avg Usage Share (%)", "User_brand": "Brand"})
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q2: FUNNEL CHART ──
        with tabs[1]:
            st.subheader("Top 10 States by App Opens — User Funnel")
            st.caption("Chart type: Funnel — shows registered users narrowing to actual app opens")
            query = """
                SELECT State,
                    SUM(Registered_user) AS Total_registered_users,
                    SUM(App_opens) AS Total_app_opens,
                    ROUND(SUM(App_opens)*100.0 / NULLIF(SUM(Registered_user),0),2) AS Open_rate_pct
                FROM map_users
                GROUP BY State
                ORDER BY Total_app_opens DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                fig = go.Figure()
                fig.add_trace(go.Funnel(
                    name="Registered Users",
                    y=df["State"],
                    x=df["Total_registered_users"],
                    textinfo="value+percent initial",
                    marker=dict(color="#a855f7"),
                ))
                fig.add_trace(go.Funnel(
                    name="App Opens",
                    y=df["State"],
                    x=df["Total_app_opens"],
                    textinfo="value+percent initial",
                    marker=dict(color="#06b6d4"),
                ))
                fig.update_layout(title="Registered Users → App Opens Funnel (Top 10 States)",
                                  height=520, paper_bgcolor="rgba(0,0,0,0)",
                                  font_color="#e9d5ff")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # -- Q3: UNDERUTILIZED BRANDS (BEST GRAPH) --
        with tabs[2]: 
            st.subheader("Underutilized vs High Performing Brands")

            query = """
                SELECT
                    User_brand,
                    SUM(User_count) AS Total_registrations,
                    ROUND(AVG(User_percentage)*100, 2) AS Engagement_rate
                FROM aggregated_users
                GROUP BY User_brand
                ORDER BY Total_registrations DESC
            """

            try:
                df = pd.read_sql(query, engine)

                if df.empty:
                    st.warning("No data available")
                else:
                    # ── CLASSIFICATION ──
                    avg_reg = df["Total_registrations"].mean()
                    avg_rate = df["Engagement_rate"].mean()

                    df["Status"] = df.apply(
                        lambda r: "Underutilized"
                        if r["Total_registrations"] > avg_reg and r["Engagement_rate"] < avg_rate
                        else ("High Performer"
                            if r["Total_registrations"] > avg_reg
                            else "Normal"),
                        axis=1
                    )

                    # ── BAR CHART ──
                    fig = px.bar(
                        df,
                        x="User_brand",
                        y="Total_registrations",
                        color="Status",
                        text="Total_registrations",
                        title="Brand Classification Based on Engagement",
                        color_discrete_map={
                            "Underutilized": "blue",
                            "High Performer": "green",
                            "Normal": "red"
                        }
                    )

                    fig.update_traces(textposition="outside")

                    st.plotly_chart(fig, use_container_width=True)

                    # ── OPTIONAL ALERT ONLY (NO TABLE) ──
                    underutil = df[df["Status"] == "Underutilized"]
                    if not underutil.empty:
                        st.warning("Underutilized: " + ", ".join(underutil["User_brand"]))

            except Exception as e:
                st.error(e)
 
        # -- Q4: TOP BRAND PER STATE --
        with tabs[3]:
            st.subheader("Dominant Device Brand per State")
            st.caption("Chart type: Bar -- shows which brand has the highest user count in each state")
            query = """
                SELECT a.State, a.User_brand, a.Total_users
                FROM (
                    SELECT State, User_brand,
                        SUM(User_count) AS Total_users,
                        RANK() OVER (PARTITION BY State ORDER BY SUM(User_count) DESC) AS rnk
                    FROM aggregated_users
                    GROUP BY State, User_brand
                ) a
                WHERE a.rnk = 1
                ORDER BY a.Total_users DESC
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(
                    df,
                    x="State",
                    y="Total_users",
                    color="User_brand",
                    text="User_brand",
                    title="Top Dominant Brand per State",
                    labels={"Total_users": "Total Users", "User_brand": "Dominant Brand"},
                    color_discrete_sequence=[
                        "#a855f7","#06b6d4","#10b981","#f59e0b","#ef4444",
                        "#3b82f6","#ec4899","#14b8a6","#f97316","#8b5cf6"
                    ],
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    height=540,
                    xaxis_tickangle=-45,
                    hovermode="x unified",
                    legend=dict(orientation="h", y=-0.35),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Summary table — one row per state
                st.markdown("**Dominant Brand Summary by State**")
                st.dataframe(df[["State","User_brand","Total_users"]].rename(columns={
                    "User_brand": "Dominant Brand",
                    "Total_users": "Total Users"
                }), use_container_width=True)

            except Exception as e:
                st.error(e)

        # -- Q5: BRAND DIVERSITY INDEX PER STATE --
        with tabs[4]:
            st.subheader("Brand Diversity Index by State")
            st.caption("Chart type: Horizontal Bar -- states ranked by how diversified their device usage is")
            query = """
                SELECT
                    State,
                    COUNT(DISTINCT User_brand)              AS Brand_count,
                    MAX(User_percentage)                    AS Top_brand_share,
                    ROUND(100 - MAX(User_percentage), 2)   AS Diversity_index
                FROM aggregated_users
                GROUP BY State
                ORDER BY Diversity_index DESC
            """
            try:
                df = pd.read_sql(query, engine)

                fig = px.bar(
                    df,
                    x="Diversity_index",
                    y="State",
                    orientation="h",
                    text="Diversity_index",
                    color="Diversity_index",
                    color_continuous_scale="Purples",
                    title="Brand Diversity Index by State (Higher = More Diverse)",
                    labels={"Diversity_index": "Diversity Index", "State": "State"},
                )
                fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                fig.update_layout(
                    height=700,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

                # Insight cards
                most_diverse  = df.iloc[0]
                least_diverse = df.iloc[-1]
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <div style="background:#1e0a3c;border-radius:10px;padding:14px;
                                    border-left:4px solid #10b981;">
                            <div style="color:#9ca3af;font-size:0.75rem;">Most Diverse State</div>
                            <div style="color:#10b981;font-size:1.2rem;font-weight:700;">
                                {most_diverse['State']}
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
                                {least_diverse['State']}
                            </div>
                            <div style="color:#6b7280;font-size:0.75rem;">
                                Index: {least_diverse['Diversity_index']} | 
                                Brands: {int(least_diverse['Brand_count'])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**Full State Diversity Table**")
                st.dataframe(df.rename(columns={
                    "Brand_count":     "No. of Brands",
                    "Top_brand_share": "Top Brand Share (%)",
                    "Diversity_index": "Diversity Index",
                }), use_container_width=True)

            except Exception as e:
                st.error(e)

    # ══════════════════════════════════════════════════════
    # SCENARIO 2: TRANSACTION ANALYSIS FOR MARKET EXPANSION
    # Chart types: Vertical Bar, Donut, Area, Gauge (Indicator), Bubble Scatter
    # ══════════════════════════════════════════════════════
    elif scenario == "Transaction Analysis for Market Expansion":
        st.markdown("""
        > **Scenario:** PhonePe operates in a highly competitive market, and understanding transaction
        dynamics at the state level is crucial for strategic decision-making. This analysis identifies
        trends, opportunities, and potential areas for expansion.
        """)

        tabs = st.tabs([
            "Q1 Top States by Amount",
            "Q2 Transaction Type Split",
            "Q3 YoY Growth by State",
            "Q4 Avg Txn Value by State",
            "Q5 Low Penetration States"
        ])

        # ── Q1: VERTICAL BAR ──
        with tabs[0]:
            st.subheader("Top 10 States by Total Transaction Amount")
            st.caption("Chart type: Vertical Bar — compares absolute transaction value across top states")
            query = """
                SELECT State,
                    SUM(Transaction_count) AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7,2) AS Total_amount_crores
                FROM aggregated_transaction
                GROUP BY State
                ORDER BY Total_amount_crores DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(df, x="State", y="Total_amount_crores",
                             text="Total_amount_crores",
                             title="Top 10 States by Transaction Amount (Crores)",
                             color="Total_amount_crores", color_continuous_scale="Blues",
                             labels={"Total_amount_crores": "Amount (Crores ₹)"})
                fig.update_traces(texttemplate="₹%{text:.1f}Cr", textposition="outside")
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q2: TOP 10 STATES BY TRANSACTION COUNT ──
        with tabs[1]:
            st.subheader("Top 10 States by Transaction Count")
            st.caption("Chart type: Vertical Bar -- states driving the highest transaction volume")
            query = """
                SELECT
                    State,
                    SUM(Transaction_count) AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores
                FROM aggregated_transaction
                GROUP BY State
                ORDER BY Total_transactions DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(
                    df,
                    x="State",
                    y="Total_transactions",
                    text="Total_transactions",
                    color="Total_transactions",
                    color_continuous_scale="Purples",
                    title="Top 10 States by Transaction Count",
                    labels={"Total_transactions": "Total Transactions",
                            "State": "State"},
                )
                fig.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig.update_layout(
                    height=500,
                    xaxis_tickangle=-30,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df.rename(columns={
                    "Total_transactions":  "Total Transactions",
                    "Total_amount_crores": "Amount (Crores ₹)",
                }), use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q3: YEAR OVER YEAR TRANSACTION GROWTH ──
        with tabs[2]:
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
        with tabs[3]:
            st.subheader("Average Transaction Value by Payment Type")
            st.caption("Chart type: Horizontal Bar -- which payment type has the highest ticket size")
            query = """
                SELECT
                    Transaction_type,
                    SUM(Transaction_count)  AS Total_count,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores,
                    ROUND(SUM(Transaction_amount) /
                          NULLIF(SUM(Transaction_count), 0), 2) AS Avg_txn_value
                FROM aggregated_transaction
                GROUP BY Transaction_type
                ORDER BY Avg_txn_value DESC
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(
                    df,
                    x="Avg_txn_value",
                    y="Transaction_type",
                    orientation="h",
                    text="Avg_txn_value",
                    color="Avg_txn_value",
                    color_continuous_scale="Blues",
                    title="Average Transaction Value per Payment Type (₹)",
                    labels={"Avg_txn_value":    "Avg Transaction Value (₹)",
                            "Transaction_type": "Payment Type"},
                )
                fig.update_traces(texttemplate="₹%{text:,.0f}",
                                   textposition="outside")
                fig.update_layout(
                    height=420,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

                # Metric cards for quick insight
                top_type = df.iloc[0]
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
                st.dataframe(df.rename(columns={
                    "Transaction_type":    "Payment Type",
                    "Total_count":         "Total Transactions",
                    "Total_amount_crores": "Amount (Crores ₹)",
                    "Avg_txn_value":       "Avg Value (₹)",
                }), use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q5: BOTTOM 10 STATES — UNTAPPED MARKETS ──
        with tabs[4]:
            st.subheader("Lowest Transaction States — Expansion Opportunities")
            st.caption("Chart type: Horizontal Bar -- states with least activity, prime for expansion")
            query = """
                SELECT
                    State,
                    SUM(Transaction_count) AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7, 2) AS Total_amount_crores,
                    COUNT(DISTINCT Year)   AS Years_active
                FROM aggregated_transaction
                GROUP BY State
                ORDER BY Total_transactions ASC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(
                    df,
                    x="Total_transactions",
                    y="State",
                    orientation="h",
                    text="Total_transactions",
                    color="Total_amount_crores",
                    color_continuous_scale="Reds",
                    title="Bottom 10 States by Transaction Count (Expansion Targets)",
                    labels={"Total_transactions":  "Total Transactions",
                            "Total_amount_crores": "Amount (Crores ₹)",
                            "State":               "State"},
                )
                fig.update_traces(texttemplate="%{text:,}",
                                   textposition="outside")
                fig.update_layout(
                    height=480,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    showlegend=False,
                    coloraxis_colorbar=dict(title="Amount (Cr ₹)"),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.info("💡 These states have the lowest transaction counts — "
                        "prime targets for PhonePe's market expansion campaigns.")
                st.dataframe(df.rename(columns={
                    "Total_transactions":  "Total Transactions",
                    "Total_amount_crores": "Amount (Crores ₹)",
                    "Years_active":        "Years Active",
                }), use_container_width=True)
            except Exception as e:
                st.error(e)
    # ══════════════════════════════════════════════════════
    # SCENARIO 3: USER ENGAGEMENT AND GROWTH STRATEGY
    # Chart types: Choropleth Bar, Horizontal Bar, Bubble, Area, Heatmap
    # ══════════════════════════════════════════════════════
    elif scenario == "User Engagement and Growth Strategy":
        st.markdown("""
        > **Scenario:** PhonePe seeks to enhance its market position by analyzing user engagement
        across different states and districts. Understanding user behavior provides valuable insights
        for strategic decision-making and growth opportunities.
        """)

        tabs = st.tabs([
            "Q1 State-wise Registered Users",
            "Q2 App Open Rate by District",
            "Q3 Engagement vs Registration",
            "Q4 Quarter-wise User Growth",
            "Q5 Low Engagement Districts"
        ])

        # ── Q1: VERTICAL BAR with dual axis ──
        with tabs[0]:
            st.subheader("State-wise Registered Users vs App Opens")
            st.caption("Chart type: Grouped Bar — side-by-side comparison of registrations and app opens per state")
            query = """
                SELECT State,
                    SUM(Registered_user) AS Total_registered_users,
                    SUM(App_opens) AS Total_app_opens
                FROM map_users
                GROUP BY State
                ORDER BY Total_registered_users DESC
            """
            try:
                df = pd.read_sql(query, engine)
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Registered Users", x=df["State"],
                                     y=df["Total_registered_users"],
                                     marker_color="#a855f7"))
                fig.add_trace(go.Bar(name="App Opens", x=df["State"],
                                     y=df["Total_app_opens"],
                                     marker_color="#06b6d4"))
                fig.update_layout(barmode="group",
                                  title="Registered Users vs App Opens by State",
                                  xaxis_tickangle=-45, height=550,
                                  hovermode="x unified",
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  font_color="#e9d5ff")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q2: HORIZONTAL BAR ──
        with tabs[1]:
            st.subheader("Top 10 Districts by App Open Rate")
            st.caption("Chart type: Horizontal Bar — ranks districts by open rate % for easy comparison")
            query = """
                SELECT District, State,
                    SUM(Registered_user) AS Total_registered,
                    SUM(App_opens) AS Total_app_opens,
                    ROUND(SUM(App_opens)*100.0/NULLIF(SUM(Registered_user),0),2) AS Open_rate_pct
                FROM map_users
                GROUP BY District, State
                HAVING Total_registered > 10000
                ORDER BY Open_rate_pct DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"
                fig = px.bar(df, x="Open_rate_pct", y="District_State", orientation="h",
                             text="Open_rate_pct",
                             title="Top 10 Districts by App Open Rate %",
                             color="Open_rate_pct", color_continuous_scale="Teal",
                             labels={"Open_rate_pct": "Open Rate (%)"})
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q3: BUBBLE SCATTER ──
        with tabs[2]:
            st.subheader("App Opens vs Registered Users by State")
            st.caption("Chart type: Pie — state-wise share of registered users and app opens")

            query = """
                SELECT State,
                    SUM(Registered_user) AS Total_registered,
                    SUM(App_opens) AS Total_app_opens,
                    ROUND(SUM(App_opens)/NULLIF(SUM(Registered_user),0),2) AS Opens_per_user
                FROM map_users
                GROUP BY State
                ORDER BY Total_registered DESC
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered"] = df["Total_registered"].astype(float)
                df["Total_app_opens"]  = df["Total_app_opens"].astype(float)
                df["Opens_per_user"]   = df["Opens_per_user"].astype(float)

                # ── top 10 + group rest as "Others" to keep pie readable ──
                top_n = 10
                df_top    = df.head(top_n).copy()
                df_others = df.iloc[top_n:].copy()

                others_row = pd.DataFrame([{
                    "State":            "Others",
                    "Total_registered": df_others["Total_registered"].sum(),
                    "Total_app_opens":  df_others["Total_app_opens"].sum(),
                    "Opens_per_user":   round(df_others["Total_app_opens"].sum() /
                                            df_others["Total_registered"].sum(), 2),
                }])
                df_pie = pd.concat([df_top, others_row], ignore_index=True)

                purple_palette = [
                    "#4c1d95", "#5b21b6", "#6d28d9", "#7c3aed",
                    "#8b5cf6", "#a855f7", "#c084fc", "#d8b4fe",
                    "#e9d5ff", "#f3e8ff", "#ede9fe",
                ]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**By Registered Users**")
                    fig_reg = go.Figure(go.Pie(
                        labels=df_pie["State"].tolist(),
                        values=df_pie["Total_registered"].tolist(),
                        hole=0.45,
                        marker=dict(colors=purple_palette),
                        textinfo="label+percent",
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Registered Users: %{value:,.0f}<br>"
                            "Share: %{percent}<extra></extra>"
                        ),
                    ))
                    fig_reg.update_layout(
                        height=480,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#e9d5ff",
                        legend=dict(orientation="h", y=-0.4),
                        annotations=[dict(
                            text="Users", x=0.5, y=0.5,
                            font_size=14, showarrow=False,
                            font_color="#e9d5ff"
                        )],
                    )
                    st.plotly_chart(fig_reg, use_container_width=True)

                with col2:
                    st.markdown("**By App Opens**")
                    fig_opens = go.Figure(go.Pie(
                        labels=df_pie["State"].tolist(),
                        values=df_pie["Total_app_opens"].tolist(),
                        hole=0.45,
                        marker=dict(colors=purple_palette),
                        textinfo="label+percent",
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "App Opens: %{value:,.0f}<br>"
                            "Share: %{percent}<extra></extra>"
                        ),
                    ))
                    fig_opens.update_layout(
                        height=480,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#e9d5ff",
                        legend=dict(orientation="h", y=-0.4),
                        annotations=[dict(
                            text="Opens", x=0.5, y=0.5,
                            font_size=14, showarrow=False,
                            font_color="#e9d5ff"
                        )],
                    )
                    st.plotly_chart(fig_opens, use_container_width=True)

                # ── opens per user insight ──
                top_state    = df.iloc[0]
                bottom_state = df.iloc[-1]
                st.info(
                    f"🏆 **{df.sort_values('Opens_per_user', ascending=False).iloc[0]['State']}** "
                    f"has the highest engagement at "
                    f"**{df.sort_values('Opens_per_user', ascending=False).iloc[0]['Opens_per_user']:,.0f}** "
                    f"app opens per registered user"
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

        # ── Q4: COLUMN + LINE CHART ──
        with tabs[3]:
            st.subheader("Year-wise Registered User Growth")
            st.caption("Chart type: Column + Line — bars show new users per year, line shows cumulative growth")
            query = """
                SELECT Year, SUM(Registered_user) AS Total_registered_users
                FROM map_users
                GROUP BY Year
                ORDER BY Year
            """
            try:
                df = pd.read_sql(query, engine)
                df["Total_registered_users"] = df["Total_registered_users"].astype(float)
                df["Year"]       = df["Year"].astype(str)
                df["Cumulative"] = df["Total_registered_users"].cumsum()

                fig = go.Figure()

                # ── Vertical Columns: new users per year ──
                fig.add_trace(go.Bar(
                    x=df["Year"],
                    y=df["Total_registered_users"],
                    name="New Users per Year",
                    marker_color="#2182CD",
                    yaxis="y1",
                    hovertemplate="<b>%{x}</b><br>New Users: %{y:,.0f}<extra></extra>",
                ))

                # ── Line: cumulative users ──
                fig.add_trace(go.Scatter(
                    x=df["Year"],
                    y=df["Cumulative"],
                    name="Cumulative Users",
                    mode="lines+markers",
                    line=dict(color="#facc15", width=3),
                    marker=dict(size=8, color="#facc15"),
                    yaxis="y2",
                    hovertemplate="<b>%{x}</b><br>Cumulative: %{y:,.0f}<extra></extra>",
                ))

                fig.update_layout(
                    title="Year-wise User Growth (New vs Cumulative)",
                    xaxis=dict(
                        tickmode="linear",
                        type="category",
                    ),
                    yaxis=dict(
                        title="New Users per Year",
                        title_font_color="#428ae1",
                        tickfont=dict(color="#2689b7"),
                    ),
                    yaxis2=dict(
                        title="Cumulative Users",
                        title_font_color="#facc15",
                        tickfont=dict(color="#facc15"),
                        overlaying="y",
                        side="right",
                    ),
                    barmode="group",
                    hovermode="x unified",
                    height=500,
                    legend=dict(orientation="h", y=-0.2),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                    bargap=0.35,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(
                    df[["Year", "Total_registered_users", "Cumulative"]].rename(columns={
                        "Year":                   "Year",
                        "Total_registered_users": "New Users",
                        "Cumulative":             "Cumulative Users",
                    }),
                    use_container_width=True
                )
            except Exception as e:
                st.error(e)

        # ── Q5: LINE CHART ──
        with tabs[4]:
            st.subheader("Low Engagement Districts — Open Rate Trend")
            st.caption("Chart type: Line — app open rate across the 20 lowest engagement districts")
            debug_query2 = """
            SELECT District, State, COUNT(*) as row_count,
                SUM(Registered_user) as total_reg,
                SUM(App_opens) as total_opens
            FROM map_users
            WHERE District = 'chandigarh'
            GROUP BY District, State
        """
        debug_df2 = pd.read_sql(debug_query2, engine)
        st.write(debug_df2)

    # ══════════════════════════════════════════════════════
    # SCENARIO 4: TRANSACTION ANALYSIS ACROSS STATES & DISTRICTS
    # Chart types: Horizontal Bar, Horizontal Bar, Sunburst, Treemap, Line
    # ══════════════════════════════════════════════════════
    elif scenario == "Transaction Analysis Across States and Districts":
        st.markdown("""
        > **Scenario:** PhonePe is conducting an analysis of transaction data to identify the
        top-performing states, districts, and pin codes in terms of transaction volume and value.
        This analysis highlights key areas for targeted marketing efforts.
        """)

        tabs = st.tabs([
            "Q1 Top Districts by Volume",
            "Q2 Top Districts by Value",
            "Q3 Top Pincodes",
            "Q4 State-District Breakdown",
            "Q5 Quarter-wise District Trend"
        ])

        # ── Q1: HORIZONTAL BAR ──
        with tabs[0]:
            st.subheader("Top 10 Districts by Transaction Volume")
            st.caption("Chart type: Horizontal Bar — clearly ranks districts by count from highest to lowest")
            query = """
                SELECT District, State,
                    SUM(Transaction_count) AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7,2) AS Total_amount_crores
                FROM top_transaction_district
                GROUP BY District, State
                ORDER BY Total_transactions DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"
                fig = px.bar(df, x="Total_transactions", y="District_State",
                             orientation="h", text="Total_transactions",
                             title="Top 10 Districts by Transaction Count",
                             color="Total_transactions", color_continuous_scale="Blues",
                             labels={"Total_transactions": "Transaction Count"})
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q2: WATERFALL CHART ──
        with tabs[1]:
            st.subheader("Top 10 Districts by Transaction Amount")
            st.caption("Chart type: Waterfall — shows cumulative transaction value buildup across top districts")
            query = """
                SELECT District, State,
                    ROUND(SUM(Transaction_amount)/1e7,2) AS Total_amount_crores
                FROM top_transaction_district
                GROUP BY District, State
                ORDER BY Total_amount_crores DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"
                fig = go.Figure(go.Waterfall(
                    name="Amount (Crores)",
                    orientation="v",
                    x=df["District_State"],
                    y=df["Total_amount_crores"],
                    textposition="outside",
                    text=[f"₹{v:.1f}Cr" for v in df["Total_amount_crores"]],
                    connector={"line": {"color": "#4c1d95"}},
                    increasing={"marker": {"color": "#a855f7"}},
                    totals={"marker": {"color": "#06b6d4"}},
                ))
                fig.update_layout(title="Cumulative Transaction Amount — Top 10 Districts (Waterfall)",
                                  xaxis_tickangle=-30, height=520,
                                  paper_bgcolor="rgba(0,0,0,0)", font_color="#e9d5ff")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q3: SUNBURST ──
        with tabs[2]:
            st.subheader("Top Pincodes by Transaction Value")
            st.caption("Chart type: Sunburst — shows State → Pincode hierarchy by transaction amount")
            query = """
                SELECT Pincode, State,
                    SUM(Transaction_count) AS Total_transactions,
                    ROUND(SUM(Transaction_amount)/1e7,2) AS Total_amount_crores
                FROM top_transaction_pincode
                GROUP BY Pincode, State
                ORDER BY Total_amount_crores DESC
                LIMIT 30
            """
            try:
                df = pd.read_sql(query, engine)
                df["Pincode"] = df["Pincode"].astype(str)
                fig = px.sunburst(df, path=["State", "Pincode"],
                                  values="Total_amount_crores",
                                  color="Total_amount_crores",
                                  color_continuous_scale="Blues",
                                  title="State → Pincode Transaction Amount (Sunburst)")
                fig.update_layout(height=580)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q4: TREEMAP ──
        with tabs[3]:
            st.subheader("State → District Transaction Breakdown")
            st.caption("Chart type: Treemap — nested boxes show each state's share and its top districts")
            query = """
                SELECT State, District,
                    ROUND(SUM(Transaction_amount)/1e7,2) AS Amount_crores
                FROM top_transaction_district
                WHERE State IN (
                    SELECT State FROM top_transaction_district
                    GROUP BY State ORDER BY SUM(Transaction_amount) DESC LIMIT 10
                )
                GROUP BY State, District
                ORDER BY State, Amount_crores DESC
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.treemap(df, path=["State", "District"],
                                 values="Amount_crores",
                                 color="Amount_crores",
                                 color_continuous_scale="Purples",
                                 title="State → District Transaction Breakdown (Top 10 States)")
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q5: LINE CHART ──
        with tabs[4]:
            st.subheader("Quarter-wise Transaction Trend — Top 5 Districts")
            st.caption("Chart type: Line with markers — tracks each district's transaction trajectory over time")
            query = """
                SELECT District, State, Year, Quarter,
                    SUM(Transaction_count) AS Total_transactions
                FROM map_transaction
                WHERE District IN (
                    SELECT District FROM map_transaction
                    GROUP BY District ORDER BY SUM(Transaction_count) DESC LIMIT 5
                )
                GROUP BY District, State, Year, Quarter
                ORDER BY Year, Quarter
            """
            try:
                df = pd.read_sql(query, engine)
                df["Period"] = df["Year"].astype(str) + " Q" + df["Quarter"].astype(str)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"
                fig = px.line(df, x="Period", y="Total_transactions",
                              color="District_State", markers=True,
                              title="Quarter-wise Transaction Trend — Top 5 Districts",
                              labels={"Total_transactions": "Transactions"})
                fig.update_layout(height=500, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

    # ══════════════════════════════════════════════════════
    # SCENARIO 5: USER REGISTRATION ANALYSIS
    # Chart types: Bar, Horizontal Bar, Sunburst, Funnel, Line+Bar combo
    # ══════════════════════════════════════════════════════
    elif scenario == "User Registration Analysis":
        st.markdown("""
        > **Scenario:** PhonePe aims to analyze user registration data to identify the top states,
        districts, and pin codes with the most registrations. This provides insights into user
        engagement patterns and highlights potential growth areas.
        """)

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
                SELECT State, SUM(Registered_user) AS Total_registered_users
                FROM top_users_district
                GROUP BY State
                ORDER BY Total_registered_users DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                fig = px.bar(df, x="State", y="Total_registered_users",
                             text="Total_registered_users",
                             title="Top 10 States by Registered Users",
                             color="Total_registered_users",
                             color_continuous_scale="Purples",
                             labels={"Total_registered_users": "Registered Users"})
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig.update_layout(xaxis_tickangle=-30, height=500)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q2: HORIZONTAL BAR ──
        with tabs[1]:
            st.subheader("Top 10 Districts by Registered Users")
            st.caption("Chart type: Horizontal Bar — long district names fit better horizontally")
            query = """
                SELECT District, State, SUM(Registered_user) AS Total_registered_users
                FROM top_users_district
                GROUP BY District, State
                ORDER BY Total_registered_users DESC
                LIMIT 10
            """
            try:
                df = pd.read_sql(query, engine)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"
                fig = px.bar(df, x="Total_registered_users", y="District_State",
                             orientation="h", text="Total_registered_users",
                             title="Top 10 Districts by Registered Users",
                             color="Total_registered_users", color_continuous_scale="Blues",
                             labels={"Total_registered_users": "Registered Users"})
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q3: SUNBURST ──
        with tabs[2]:
            st.subheader("Top Pincodes by Registered Users")
            st.caption("Chart type: Sunburst — hierarchical State → Pincode view of user registrations")
            query = """
                SELECT Pincode, State, SUM(Registered_user) AS Total_registered_users
                FROM top_users_pincode
                GROUP BY Pincode, State
                ORDER BY Total_registered_users DESC
                LIMIT 30
            """
            try:
                df = pd.read_sql(query, engine)
                df["Pincode"] = df["Pincode"].astype(str)
                fig = px.sunburst(df, path=["State", "Pincode"],
                                  values="Total_registered_users",
                                  color="Total_registered_users",
                                  color_continuous_scale="Purples",
                                  title="State → Pincode Registered Users (Sunburst)")
                fig.update_layout(height=580)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q4: FUNNEL CHART ──
        with tabs[3]:
            st.subheader("Top Districts by Registration — Filtered by Year & Quarter")
            st.caption("Chart type: Funnel — shows registration drop-off across top districts for selected period")
            try:
                year_q   = pd.read_sql("SELECT DISTINCT Year, Quarter FROM top_users_district ORDER BY Year, Quarter", engine)
                years    = sorted(year_q["Year"].unique().tolist())
                quarters = sorted(year_q["Quarter"].unique().tolist())
                col1, col2 = st.columns(2)
                with col1:
                    sel_year = st.selectbox("Select Year", years)
                with col2:
                    sel_quarter = st.selectbox("Select Quarter", quarters)

                query = f"""
                    SELECT District, State, SUM(Registered_user) AS Total_registered_users
                    FROM top_users_district
                    WHERE Year={sel_year} AND Quarter={sel_quarter}
                    GROUP BY District, State
                    ORDER BY Total_registered_users DESC
                    LIMIT 12
                """
                df = pd.read_sql(query, engine)
                df["District_State"] = df["District"] + " (" + df["State"] + ")"

                fig = go.Figure(go.Funnel(
                    y=df["District_State"],
                    x=df["Total_registered_users"],
                    textinfo="value+percent initial",
                    marker=dict(
                        color=["#a855f7","#9333ea","#7c3aed","#6d28d9",
                               "#5b21b6","#4c1d95","#3b0764","#2d1060",
                               "#1a0533","#06b6d4","#0891b2","#0e7490"],
                    ),
                ))
                fig.update_layout(
                    title=f"User Registration Funnel — {sel_year} Q{sel_quarter}",
                    height=540,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)

        # ── Q5: COMBO LINE + BAR ──
        with tabs[4]:
            st.subheader("User Registration Growth Trend Over Time")
            st.caption("Chart type: Combo (Bar + Line) — bars = new quarterly registrations, line = cumulative total")
            query = """
                SELECT Year, Quarter, SUM(Registered_user) AS Total_registered_users
                FROM top_users_district
                GROUP BY Year, Quarter
                ORDER BY Year, Quarter
            """
            try:
                df = pd.read_sql(query, engine)
                df["Period"] = df["Year"].astype(str) + " Q" + df["Quarter"].astype(str)
                df["Cumulative_users"] = df["Total_registered_users"].cumsum()

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df["Period"], y=df["Total_registered_users"],
                    name="New Registrations (Quarter)",
                    marker_color="#a855f7",
                    opacity=0.85,
                ))
                fig.add_trace(go.Scatter(
                    x=df["Period"], y=df["Cumulative_users"],
                    name="Cumulative Users",
                    mode="lines+markers",
                    line=dict(color="#06b6d4", width=3),
                    marker=dict(size=7),
                    yaxis="y2",
                ))
                fig.update_layout(
                    title="Quarterly New Registrations (Bar) vs Cumulative Users (Line)",
                    yaxis=dict(title="New Registrations", title_font_color="#a855f7",
                               tickfont_color="#a855f7"),
                    yaxis2=dict(title="Cumulative Users", title_font_color="#06b6d4",
                                tickfont_color="#06b6d4", overlaying="y", side="right"),
                    hovermode="x unified",
                    height=520,
                    legend=dict(orientation="h", y=1.08),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e9d5ff",
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)