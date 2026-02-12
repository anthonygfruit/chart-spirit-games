import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Chart Spirit Games Leaderboard",
    page_icon="🏆",
    layout="wide",
)

# --- Global styling ---
st.markdown(
    """
    <style>
    .main {
        background: radial-gradient(circle at top, #1f2933 0, #020617 55%);
        color: #e5e7eb;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #111827 60%, #0f172a 100%);
        color: #e5e7eb;
    }
    .metric-card {
        padding: 1.1rem 1.2rem;
        border-radius: 1.0rem;
        background: linear-gradient(135deg, rgba(56,189,248,0.12), rgba(59,130,246,0.08));
        border: 1px solid rgba(148,163,184,0.4);
        box-shadow: 0 18px 45px rgba(15,23,42,0.9);
        backdrop-filter: blur(16px);
    }
    .metric-label {
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f9fafb;
        margin-bottom: 0.15rem;
    }
    .metric-subvalue {
        font-size: 0.9rem;
        color: #e5e7eb;
        opacity: 0.9;
    }
    .stPlotlyChart {
        border-radius: 1.2rem;
        overflow: hidden;
        box-shadow: 0 22px 55px rgba(15,23,42,0.85);
        border: 1px solid rgba(148,163,184,0.35);
        background: radial-gradient(circle at top left, rgba(56,189,248,0.14), rgba(15,23,42,1) 55%);
        padding: 0.4rem 0.4rem 0.8rem 0.4rem;
    }
    .stDataFrame {
        border-radius: 1.0rem;
        overflow: hidden;
        box-shadow: 0 18px 45px rgba(15,23,42,0.85);
        border: 1px solid rgba(148,163,184,0.35);
        background: radial-gradient(circle at top left, rgba(59,130,246,0.16), rgba(15,23,42,1) 60%);
    }
    h1, h2, h3, h4 {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
        letter-spacing: 0.03em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_scores() -> pd.DataFrame:
    df = pd.read_csv("scores.csv")
    df = df.replace("x", None)
    df.rename(
        columns={
            "Unnamed: 5": "Game Total",
            "Unnamed: 10": "Spirit Total",
            "Unnamed: 11": "Total Total",
        },
        inplace=True,
    )
    df = df.dropna(subset=["Team Member"]).sort_values(
        by="Total Total", ascending=False
    )
    df["Emoji"] = df.apply(
        lambda row: "🏆" if row["Total Total"] == df["Total Total"].max() else "🍪",
        axis=1,
    )
    return df


df = load_scores()

# --- Header & hero copy ---
st.markdown("### Chart Spirit Games")
st.markdown(
    "Where **clutch performance** meets **elite vibes**. "
    "Totals combine raw game skill with spirit points to crown the true MVP. ✨"
)

# --- Sidebar controls ---
with st.sidebar:
    st.markdown("#### Controls")
    view_option = st.radio("Score view", ("Totals", "Game Scores"), index=0)
    show_table = st.checkbox("Show leaderboard table", value=True)
    team_filter = st.multiselect(
        "Highlight / focus players",
        options=list(df["Team Member"].unique()),
        help="Pick players to spotlight. Leave empty to see everyone.",
    )

if team_filter:
    plot_df = df[df["Team Member"].isin(team_filter)]
else:
    plot_df = df

# --- KPI cards ---
top_row = df.iloc[0]
top_name = top_row["Team Member"]
top_total = float(top_row["Total Total"])
avg_spirit = float(df["Spirit Total"].mean())
total_points = float(df["Total Total"].sum())

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Overall MVP</div>
            <div class="metric-value">{top_name} 🏆</div>
            <div class="metric-subvalue">{top_total:.0f} total points</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Average Spirit Score</div>
            <div class="metric-value">{avg_spirit:.1f}</div>
            <div class="metric-subvalue">Vibes per player</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total Points Awarded</div>
            <div class="metric-value">{total_points:.0f}</div>
            <div class="metric-subvalue">Across all games & spirit</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Main chart ---
score_columns = ["Free Throw", "Putting", "Beer Pong", "Corn Hole"]

if view_option == "Totals":
    fig = px.bar(
        plot_df,
        x="Team Member",
        y=["Game Total", "Spirit Total"],
        title="Total Score Breakdown",
        labels={"value": "Points", "variable": "Score type"},
        barmode="group",
        height=520,
    )
else:
    fig = px.bar(
        plot_df,
        x="Team Member",
        y=score_columns,
        title="Game-by-Game Scores",
        labels={"value": "Points", "variable": "Game"},
        barmode="group",
        height=520,
    )

fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e5e7eb"),
    legend_title_text="",
    title=dict(x=0.02, xanchor="left", font=dict(size=22)),
    margin=dict(l=40, r=40, t=70, b=40),
)
fig.update_traces(marker_line_width=0.5, marker_line_color="#020617")

# Emoji annotations on each player
for _, row in plot_df.iterrows():
    if view_option == "Totals":
        y_val = float(row["Total Total"])
    else:
        # Anchor emoji slightly above that player's highest single-game score
        y_vals = [
            v for v in [row.get(col) for col in score_columns] if pd.notnull(v)
        ]
        y_val = float(max(y_vals)) if y_vals else 0

    fig.add_annotation(
        x=row["Team Member"],
        y=y_val,
        text=row["Emoji"],
        showarrow=False,
        yshift=14,
        font=dict(size=20),
    )

st.plotly_chart(fig, use_container_width=True)

# --- Leaderboard table ---
if show_table:
    st.markdown("#### Full Leaderboard")
    leaderboard_df = df[
        ["Team Member", "Game Total", "Spirit Total", "Total Total", "Emoji"]
    ].reset_index(drop=True)
    st.dataframe(
        leaderboard_df,
        use_container_width=True,
        hide_index=True,
    )