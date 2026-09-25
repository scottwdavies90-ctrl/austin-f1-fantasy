import streamlit as st
import requests
import pandas as pd

# Page Setup
st.set_page_config(
    page_title="Austin FF F1 Championship",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# High-End Motorsport Dark Mode CSS Injection
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0B0E14;
        color: #F3F4F6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Remove default padding for edge-to-edge mobile feel */
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }

    /* Hide default header/footer */
    header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
    footer { visibility: hidden; }

    /* Custom Title Typography */
    .app-title {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
    }
    .app-subtitle {
        font-size: 0.72rem;
        color: #9CA3AF;
    }

    /* Metric Cards Grid */
    .metric-card {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .metric-card.p1-card {
        border-left: 4px solid #F59E0B;
        background: linear-gradient(135deg, #1C1917 0%, #161B22 100%);
    }
    .metric-card.top-card {
        border-left: 4px solid #10B981;
    }
    .metric-card.dnf-card {
        border-left: 4px solid #EF4444;
    }
    .metric-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #8B949E;
        font-weight: 700;
    }
    .metric-value {
        font-size: 1.05rem;
        font-weight: 800;
        color: #F3F4F6;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Styled Driver Card for Mobile */
    .driver-card {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }
    .driver-card.p1-border {
        border: 1px solid #F59E0B;
        background: linear-gradient(135deg, #1C1917 0%, #161B22 100%);
    }
    .driver-rank {
        font-size: 1.1rem;
        font-weight: 900;
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .rank-p1 { background: #F59E0B; color: #000000; }
    .rank-p2 { background: #94A3B8; color: #000000; }
    .rank-p3 { background: #D97706; color: #FFFFFF; }
    .rank-points { background: #21262D; color: #C9D1D9; }

    .driver-info {
        flex-grow: 1;
        min-width: 0;
    }
    .driver-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #F0F6FC;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .driver-sub {
        font-size: 0.72rem;
        color: #8B949E;
        margin-top: 2px;
    }
    .driver-stats {
        text-align: right;
        flex-shrink: 0;
        padding-left: 10px;
    }
    .f1-badge {
        font-size: 1.2rem;
        font-weight: 900;
        color: #38BDF8;
        line-height: 1;
    }
    .f1-label {
        font-size: 0.65rem;
        color: #6E7681;
        text-transform: uppercase;
        font-weight: 700;
        margin-top: 2px;
    }

    /* Custom Streamlit Buttons & Tabs */
    .stButton>button {
        background-color: #E10600 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        padding: 6px 12px !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161B22;
        padding: 4px;
        border-radius: 10px;
        border: 1px solid #21262D;
        gap: 4px;
        margin-bottom: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8B949E;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 8px 12px;
        flex-grow: 1;
        text-align: center;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262D !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ESPN League Settings
LEAGUE_ID = "92432855"
SEASON_ID = "2026"
URL = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/segments/0/leagues/{LEAGUE_ID}?view=mMatchupScore&view=mTeam"

@st.cache_data(ttl=15)
def fetch_espn_data():
    try:
        resp = requests.get(URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None

def build_dashboard():
    # Top Mobile Action Bar
    col_title, col_btn = st.columns([3, 1], vertical_alignment="center")
    with col_title:
        st.markdown('''
        <div>
            <div class="app-title">🏎️ Austin FF F1</div>
            <div class="app-subtitle">Live Telemetry & Standings</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_btn:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    data = fetch_espn_data()

    if not data:
        st.error("Unable to connect to ESPN API. Ensure your league is set to 'Public'.")
        return

    # 1. Map Teams
    teams_map = {t["id"]: t["name"] for t in data.get("teams", [])}
    num_teams = len(teams_map)

    standings = {
        t_id: {
            "name": name,
            "wins": 0, "losses": 0, "ties": 0,
            "points": 0.0, "f1": 0, "p1": 0,
            "podiums": 0, "points_finishes": 0,
            "recent_ranks": []
        }
        for t_id, name in teams_map.items()
    }

    weekly_scores = {}

    # 2. Parse Matchups & Scores
    for game in data.get("schedule", []):
        week = game["matchupPeriodId"]
        if week not in weekly_scores:
            weekly_scores[week] = []
            
        for side in ["home", "away"]:
            if side in game and game[side]:
                t_id = game[side]["teamId"]
                score = game[side]["totalPoints"]
                weekly_scores[week].append({"teamId": t_id, "score": score})
                standings[t_id]["points"] += score

        if game.get("home") and game.get("away") and game.get("winner") and game["winner"] != "UNDECIDED":
            if game["winner"] == "HOME":
                standings[game["home"]["teamId"]]["wins"] += 1
                standings[game["away"]["teamId"]]["losses"] += 1
            elif game["winner"] == "AWAY":
                standings[game["away"]["teamId"]]["wins"] += 1
                standings[game["home"]["teamId"]]["losses"] += 1
            else:
                standings[game["home"]["teamId"]]["ties"] += 1
                standings[game["away"]["teamId"]]["ties"] += 1

    # 3. Calculate F1 Points & Podiums
    latest_completed_week = 0
    for week in sorted(weekly_scores.keys()):
        scores = weekly_scores[week]
        if all(s["score"] == 0 for s in scores):
            continue
        
        latest_completed_week = week
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        for idx, s in enumerate(scores):
            rank = idx + 1
            f1_pts = max(0, num_teams - idx)
            standings[s["teamId"]]["f1"] += f1_pts
            standings[s["teamId"]]["recent_ranks"].append(rank)
            
            if rank == 1:
                standings[s["teamId"]]["p1"] += 1
            if rank <= 3:
                standings[s["teamId"]]["podiums"] += 1
            if f1_pts > 0:
                standings[s["teamId"]]["points_finishes"] += 1

    # Identify DNF Team
    dnf_team_id = None
    if latest_completed_week > 0 and weekly_scores[latest_completed_week]:
        latest = sorted(weekly_scores[latest_completed_week], key=lambda x: x["score"])
        if latest:
            dnf_team_id = latest[0]["teamId"]

    # Sort Standings: Primary = F1 Points (Desc), Tiebreaker = Total Points (Desc)
    sorted_teams = sorted(
        standings.values(),
        key=lambda x: (x["f1"], x["points"]),
        reverse=True
    )

    # 4. Custom Styled KPI Cards (Mobile Grid)
    k1, k2, k3 = st.columns(3)
    leader_name = sorted_teams[0]["name"] if sorted_teams else "N/A"
    top_scorer_name = max(standings.values(), key=lambda x: x["points"])["name"] if standings else "N/A"
    dnf_name = teams_map.get(dnf_team_id, "None") if dnf_team_id else "None"

    with k1:
        st.markdown(f'''
        <div class="metric-card p1-card">
            <div class="metric-label">🏆 P1 Leader</div>
            <div class="metric-value">{leader_name}</div>
        </div>
        ''', unsafe_allow_html=True)
    with k2:
        st.markdown(f'''
        <div class="metric-card top-card">
            <div class="metric-label">🎯 Top Scorer</div>
            <div class="metric-value">{top_scorer_name}</div>
        </div>
        ''', unsafe_allow_html=True)
    with k3:
        st.markdown(f'''
        <div class="metric-card dnf-card">
            <div class="metric-label">💥 Latest DNF</div>
            <div class="metric-value">{dnf_name}</div>
        </div>
        ''', unsafe_allow_html=True)

    # Navigation Tabs
    tab_cards, tab_chart, tab_table = st.tabs(["🏎️ Leaderboard", "📊 Telemetry", "📋 Full Table"])

    with tab_cards:
        # Render Native Mobile Driver Cards
        for idx, t in enumerate(sorted_teams):
            rank_num = idx + 1
            
            # Rank Badge Styling
            if rank_num == 1:
                rank_class = "rank-p1"
                card_border = "p1-border"
            elif rank_num == 2:
                rank_class = "rank-p2"
                card_border = ""
            elif rank_num == 3:
                rank_class = "rank-p3"
                card_border = ""
            else:
                rank_class = "rank-points"
                card_border = ""

            # Form Indicator
            last3 = t["recent_ranks"][-3:]
            avg_rank = sum(last3) / len(last3) if last3 else 5
            if avg_rank <= 2:
                form = "🔥 Hot"
            elif avg_rank <= 4:
                form = "📈 Surging"
            elif avg_rank >= 8:
                form = "📉 Slumping"
            else:
                form = "➖ Steady"

            # DNF Flag
            is_dnf = dnf_team_id and teams_map[dnf_team_id] == t["name"]
            status_str = "💥 DNF" if is_dnf else f"{form}"

            st.markdown(f'''
            <div class="driver-card {card_border}">
                <div class="driver-rank {rank_class}">P{rank_num}</div>
                <div class="driver-info">
                    <div class="driver-name">{t["name"]}</div>
                    <div class="driver-sub">{t["points"]:.2f} Total Pts • {t["wins"]}-{t["losses"]}-{t["ties"]} • {status_str}</div>
                </div>
                <div class="driver-stats">
                    <div class="f1-badge">{t["f1"]}</div>
                    <div class="f1-label">F1 PTS</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    with tab_chart:
        st.subheader("📊 F1 Points Distribution")
        
        chart_data = []
        for idx, t in enumerate(sorted_teams):
            chart_data.append({
                "Team Name": t["name"],
                "F1 Points": t["f1"]
            })
        df_chart = pd.DataFrame(chart_data)
        
        st.bar_chart(
            df_chart,
            x="Team Name",
            y="F1 Points",
            sort=False,
            horizontal=True
        )

    with tab_table:
        table_data = []
        for idx, t in enumerate(sorted_teams):
            last3 = t["recent_ranks"][-3:]
            avg_rank = sum(last3) / len(last3) if last3 else 5
            if avg_rank <= 2:
                form = "🔥 Hot"
            elif avg_rank <= 4:
                form = "📈 Surging"
            elif avg_rank >= 8:
                form = "📉 Slumping"
            else:
                form = "➖ Steady"

            table_data.append({
                "Pos": f"P{idx + 1}",
                "Team Name": t["name"],
                "F1 Pts": t["f1"],
                "Total Pts": round(t["points"], 2),
                "Form": form,
                "Record": f"{t['wins']}-{t['losses']}-{t['ties']}",
                "P1 Wins": t["p1"],
                "Podiums": t["podiums"]
            })

        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

# Run App
build_dashboard()
