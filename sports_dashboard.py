"""
All-in-one sports dashboard — live scores, standings, and visuals.
Uses ESPN's public API (no API key required).
"""

import json
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen, Request
from urllib.error import URLError

# ─── Config ─────────────────────────────────────────────────────────────
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

LEAGUES = [
    {"sport": "football", "league": "nfl", "name": "NFL", "icon": "🏈"},
    {"sport": "basketball", "league": "nba", "name": "NBA", "icon": "🏀"},
    {"sport": "baseball", "league": "mlb", "name": "MLB", "icon": "⚾"},
    {"sport": "hockey", "league": "nhl", "name": "NHL", "icon": "🏒"},
    {"sport": "soccer", "league": "usa.1", "name": "MLS", "icon": "⚽"},
]

st.set_page_config(
    page_title="Sports Command Center",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sport-themed styling ─────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@400;600;700&display=swap');
    .main {
        position: relative;
        background: #0c0f14;
        background-image:
            radial-gradient(ellipse 100% 60% at 20% 20%, rgba(34, 197, 94, 0.08), transparent 45%),
            radial-gradient(ellipse 80% 50% at 80% 80%, rgba(59, 130, 246, 0.06), transparent 45%),
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 60px,
                rgba(255, 255, 255, 0.015) 60px,
                rgba(255, 255, 255, 0.015) 61px
            ),
            linear-gradient(180deg, #0f1419 0%, #0c0f14 40%, #080a0d 100%);
        color: #f5f5f5;
        min-height: 100vh;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #0a0d12 100%);
        border-right: 2px solid rgba(34, 197, 94, 0.3);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #a3a3a3; }
    .hero {
        text-align: center;
        padding: 2rem 0 2.5rem;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.06) 0%, rgba(59, 130, 246, 0.04) 100%);
        border-bottom: 2px solid rgba(34, 197, 94, 0.4);
        border-radius: 0;
    }
    .hero h1 {
        font-family: 'Bebas Neue', sans-serif;
        font-weight: 400;
        font-size: 3.2rem;
        letter-spacing: 0.35em;
        color: #ffffff;
        margin: 0;
        text-transform: uppercase;
    }
    .hero p {
        font-family: 'Oswald', sans-serif;
        color: #737373;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
    }
    .game-card {
        padding: 1.25rem 1.5rem;
        border-radius: 8px;
        background: rgba(15, 20, 26, 0.95);
        border: 1px solid rgba(34, 197, 94, 0.25);
        border-left: 4px solid rgba(34, 197, 94, 0.6);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 1rem;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .game-card:hover {
        transform: translateX(4px);
        border-left-color: #22c55e;
    }
    .team-name {
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #ffffff;
        letter-spacing: 0.05em;
    }
    .score {
        font-family: 'Oswald', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #22c55e;
        letter-spacing: 0.05em;
    }
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-family: 'Oswald', sans-serif;
    }
    .status-live {
        background: rgba(34, 197, 94, 0.25);
        color: #86efac;
        border: 1px solid #22c55e;
    }
    .status-final {
        background: rgba(38, 38, 38, 0.8);
        color: #a3a3a3;
        border: 1px solid #404040;
    }
    .status-scheduled {
        background: transparent;
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.5);
    }
    .stPlotlyChart {
        border-radius: 8px;
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-left: 4px solid rgba(34, 197, 94, 0.5);
        background: rgba(12, 15, 20, 0.9);
    }
    h2, h3 {
        font-family: 'Bebas Neue', sans-serif;
        color: #ffffff;
        letter-spacing: 0.1em;
        font-weight: 400;
    }
    div[data-testid="stMetricValue"] { font-family: 'Oswald', sans-serif; color: #22c55e; }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-left: 4px solid rgba(34, 197, 94, 0.5);
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=120)
def fetch_json(url: str, timeout: int = 10) -> dict | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) SportsDashboard/1.0"})
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except (URLError, json.JSONDecodeError, OSError):
        return None


def get_scoreboard(sport: str, league: str) -> dict | None:
    url = f"{ESPN_BASE}/{sport}/{league}/scoreboard"
    return fetch_json(url)


def get_standings(sport: str, league: str) -> dict | None:
    url = f"{ESPN_BASE}/{sport}/{league}/standings"
    data = fetch_json(url, timeout=15)
    # NFL: try alternate CDN endpoint if main one fails or returns no children
    if (sport == "football" and league == "nfl") and (not data or not data.get("children")):
        year = datetime.datetime.now().year
        for season in (year, year - 1):
            alt_url = f"https://cdn.espn.com/core/nfl/standings?xhr=1&season={season}"
            data = fetch_json(alt_url, timeout=15)
            if data and (data.get("children") or data.get("content") or data.get("teams")):
                break
    return data


def _safe_image(url: str, width: int = 48) -> None:
    """Render team/player logo via st.image so it loads (HTML img is often blocked)."""
    if not url or not url.startswith("http"):
        st.write("")  # placeholder
        return
    try:
        st.image(url, width=width)
    except Exception:
        st.write("")


def render_game_card(comp: dict, league_name: str) -> None:
    competitors = comp.get("competitors", [])
    if len(competitors) < 2:
        return
    status = comp.get("status", {})
    status_type = status.get("type", {})
    state = status_type.get("state", "unknown")
    detail = status_type.get("shortDetail") or status_type.get("detail", "")
    display_clock = status.get("displayClock", "")

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

    if state == "in":
        badge = f'<span class="status-badge status-live">Live · {display_clock}</span>'
    elif state == "post":
        badge = f'<span class="status-badge status-final">Final</span>'
    else:
        badge = f'<span class="status-badge status-scheduled">{detail or "Scheduled"}</span>'

    venue = comp.get("venue", {})
    venue_name = venue.get("fullName", "")

    st.markdown(
        f"""
        <div class="game-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <span style="color:#737373; font-size:0.85rem;">{venue_name}</span>
                {badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Team logos via st.image() (larger, prominent) + name + score
    for label, c in [("Away", away), ("Home", home)]:
        name = c.get("team", {}).get("shortDisplayName", "TBD")
        score = c.get("score", "0")
        logo = c.get("logo", "") or (c.get("team", {}) or {}).get("logo", "")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            sub1, sub2 = st.columns([1, 4])
            with sub1:
                _safe_image(logo, width=56)
            with sub2:
                st.markdown(f"<span class='team-name'>{name}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span class='score'>{score}</span>", unsafe_allow_html=True)


def _parse_wins_losses(stats: list) -> tuple[int, int]:
    """Extract wins and losses from ESPN stats array (various naming conventions)."""
    wins = losses = 0
    for s in stats:
        if not isinstance(s, dict):
            continue
        n = (str(s.get("name") or s.get("abbreviation") or s.get("type") or "")).lower()
        v = s.get("value", 0) or 0
        try:
            v = int(float(v))
        except (ValueError, TypeError):
            v = 0
        if n in ("w", "win", "wins") or (n and "win" in n and "loss" not in n):
            wins = v
        elif n in ("l", "loss", "losses") or (n and "loss" in n):
            losses = v
    if wins == 0 and losses == 0 and len(stats) >= 2:
        try:
            wins = int(float(stats[0].get("value", 0) or 0))
            losses = int(float(stats[1].get("value", 0) or 0))
        except (ValueError, TypeError, IndexError):
            pass
    return wins, losses


def build_standings_df(standings_data: dict, sport: str, league: str) -> pd.DataFrame | None:
    if not standings_data:
        return None
    rows = []

    # Structure 1: site.api.espn.com — children[].standings.entries[]
    children = standings_data.get("children", [])
    for conf in children:
        conf_name = conf.get("name", "")
        entries = conf.get("standings", {}).get("entries", [])
        for group in entries:
            team = group.get("team", {})
            stats = group.get("stats", [])
            wins, losses = _parse_wins_losses(stats)
            team_name = team.get("displayName") or team.get("shortDisplayName", "")
            if team_name:
                rows.append({
                    "Conference": conf_name,
                    "Team": team_name,
                    "Abbr": team.get("abbreviation", ""),
                    "Wins": wins,
                    "Losses": losses,
                })

    # Structure 2: cdn.espn.com — content.standings.groups or flat teams
    if not rows:
        content = standings_data.get("content", standings_data)
        groups = content.get("standings", {}).get("groups", content.get("groups", []))
        if not groups and isinstance(content.get("standings"), list):
            groups = content["standings"]
        for grp in groups:
            conf_name = grp.get("name", grp.get("label", ""))
            entries = grp.get("standings", {}).get("entries", grp.get("entries", []))
            for group in entries:
                team = group.get("team", group)
                if isinstance(team, str):
                    continue
                stats = group.get("stats", [])
                wins, losses = _parse_wins_losses(stats)
                team_name = team.get("displayName") or team.get("shortDisplayName") or team.get("name", "")
                if team_name:
                    rows.append({
                        "Conference": conf_name,
                        "Team": team_name,
                        "Abbr": team.get("abbreviation", ""),
                        "Wins": wins,
                        "Losses": losses,
                    })

    # Structure 3: flat list of teams with record-like fields
    if not rows and "teams" in standings_data:
        for group in standings_data.get("teams", []):
            team = group.get("team", group)
            record = group.get("record", {}) or group.get("summary", "")
            if isinstance(record, str) and "-" in record:
                parts = record.split("-")
                try:
                    wins, losses = int(parts[0].strip()), int(parts[1].strip())
                except (ValueError, IndexError):
                    wins, losses = 0, 0
            else:
                wins = int(group.get("wins", 0) or 0)
                losses = int(group.get("losses", 0) or 0)
            team_name = team.get("displayName") if isinstance(team, dict) else str(team)
            if team_name:
                rows.append({
                    "Conference": "",
                    "Team": team_name,
                    "Abbr": team.get("abbreviation", "") if isinstance(team, dict) else "",
                    "Wins": wins,
                    "Losses": losses,
                })

    if not rows:
        return None
    return pd.DataFrame(rows)


def main():
    st.markdown(
        '<div class="hero">'
        '<h1>SPORTS COMMAND CENTER</h1>'
        '<p>Live scores · Standings · ESPN data</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected = st.sidebar.radio(
        "League",
        options=LEAGUES,
        format_func=lambda x: f"{x['icon']} {x['name']}",
        key="league_radio",
    )
    sport, league, league_name = selected["sport"], selected["league"], selected["name"]

    # Scoreboard
    data = get_scoreboard(sport, league)
    if not data:
        st.error(f"Could not load {league_name} scoreboard. Try again in a moment.")
        return

    events = data.get("events", [])
    season_info = data.get("leagues", [{}])[0].get("season", {}) or data.get("season", {})
    season_label = season_info.get("displayName", season_info.get("year", ""))

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(f"📅 {league_name} — {season_label}")

    if not events:
        st.info(f"No games on the board right now for {league_name}.")
    else:
        for event in events:
            comps = event.get("competitions", [])
            for comp in comps:
                render_game_card(comp, league_name)
                # Show game leaders (e.g. passing/rushing leaders for NFL, PPG for NBA)
                comp_state = (comp.get("status") or {}).get("type") or {}
                comp_state_str = comp_state.get("state", "unknown")
                leaders = comp.get("leaders", [])
                if leaders and comp_state_str != "pre":
                    with st.expander("⭐ Game leaders", expanded=False):
                        for cat in leaders[:4]:
                            name = cat.get("displayName", cat.get("shortDisplayName", ""))
                            lead_list = cat.get("leaders", [])
                            if not lead_list:
                                continue
                            lead = lead_list[0]
                            athlete = lead.get("athlete", {})
                            headshot = athlete.get("headshot", "")
                            display_val = lead.get("displayValue", "")
                            a, b = st.columns([1, 4])
                            with a:
                                if headshot:
                                    st.image(headshot, width=56)
                            with b:
                                st.markdown(f"**{name}**")
                                st.caption(f"{athlete.get('displayName', '')} — {display_val}")

    # Standings + charts
    st.divider()
    st.subheader(f"📊 {league_name} standings & visuals")

    standings_data = get_standings(sport, league)
    df = build_standings_df(standings_data, sport, league) if standings_data else None

    if df is not None and not df.empty:
        confs = [c for c in df["Conference"].unique().tolist() if c and str(c).strip()]
        if not confs:
            confs = ["All"]
            df = df.assign(Conference=df["Conference"].replace("", "All"))
        pick = st.selectbox("Conference", confs, key="conf_pick")
        sub = df[df["Conference"] == pick].sort_values("Wins", ascending=False).head(12)

        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(
                sub[["Team", "Wins", "Losses"]],
                use_container_width=True,
                hide_index=True,
            )
        with c2:
            fig = go.Figure(
                data=[
                    go.Bar(
                        name="Wins",
                        x=sub["Team"].str.replace(" ", "\n"),
                        y=sub["Wins"],
                        marker_color="#22c55e",
                        text=sub["Wins"],
                        textposition="outside",
                    ),
                    go.Bar(
                        name="Losses",
                        x=sub["Team"].str.replace(" ", "\n"),
                        y=sub["Losses"],
                        marker_color="rgba(120, 113, 108, 0.5)",
                        text=sub["Losses"],
                        textposition="outside",
                    ),
                ]
            )
            fig.update_layout(
                barmode="group",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(12, 15, 20, 0.6)",
                font={"color": "#f5f5f5", "family": "JetBrains Mono"},
                margin=dict(t=40, b=120),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Win distribution radar-style
        st.markdown("#### Win share (top 8)")
        top8 = sub.head(8)
        fig2 = px.bar_polar(
            pd.DataFrame({
                "Team": top8["Team"],
                "Wins": top8["Wins"],
                "Full": 1,
            }),
            theta="Team",
            r="Wins",
            color="Wins",
            color_continuous_scale="Greens",
            template="plotly_dark",
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#f5f5f5"},
            showlegend=False,
            margin=dict(t=60, b=60),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(f"Standings for {league_name} are not available at the moment.")


if __name__ == "__main__":
    main()
