import streamlit as st
import requests
import pandas as pd

# Page Setup
st.set_page_config(
    page_title="Austin FF F1 Championship",
    page_icon="🏎️",
    layout="wide"
)

# Mobile CSS Optimizations (Reduces padding, hides desktop space)
st.markdown("""
<style>
    /* Reduce top padding on mobile screens */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    /* Compact Metric Cards for narrow viewports */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    /* Touch-friendly tab headers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
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
        st.title("🏎️ Austin FF F1")
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

    # Primary Sort: F1 Points (Desc) | Tiebreaker: Total Points (Desc)
    sorted_teams = sorted(
        standings.values(),
        key=lambda x: (x["f1"], x["points"]),
        reverse=True
    )

    # Clean Mobile Tab Navigation
    tab_standings, tab_telemetry = st.tabs(["🏆 Standings", "📊 Telemetry & Chart"])

    with tab_standings:
        # Top Compact KPI Metrics
        c1, c2, c3 = st.columns(3)
        leader_name = sorted_teams[0]["name"] if sorted_teams else "N/A"
        top_scorer_name = max(standings.values(), key=lambda x: x["points"])["name"] if standings else "N/A"
        dnf_name = teams_map.get(dnf_team_id, "None") if dnf_team_id else "None"

        c1.metric("P1 Leader", leader_name)
        c2.metric("Top Scorer", top_scorer_name)
        c3.metric("Latest DNF 💥", dnf_name)

        st.divider()

        # Mobile Leaderboard Data Structure
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
                
            status = "💥 DNF" if dnf_team_id and teams_map[dnf_team_id] == t["name"] else "✅ OK"
            
            table_data.append({
                "Pos": f"P{idx + 1}",
                "Team Name": t["name"],
                "F1 Pts": t["f1"],
                "Total Pts": round(t["points"], 2),
                "Form": form,
                "Status": status,
                "Record": f"{t['wins']}-{t['losses']}-{t['ties']}",
                "P1 / Podiums": f"🥇{t['p1']} | 🏆{t['podiums']}"
            })

        df = pd.DataFrame(table_data)

        # Render Touch-Friendly Dataframe with Specific Column Formatting
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pos": st.column_config.TextColumn("Pos", width="small"),
                "Team Name": st.column_config.TextColumn("Team Name", width="medium"),
                "F1 Pts": st.column_config.NumberColumn("F1 Pts", format="%d Pts"),
                "Total Pts": st.column_config.NumberColumn("Total Pts", format="%.2f"),
                "Form": st.column_config.TextColumn("Form", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            }
        )

    with tab_telemetry:
        st.subheader("📊 F1 Points Leaderboard")
        st.bar_chart(
            df,
            x="Team Name",
            y="F1 Pts",
            sort=False,
            horizontal=True
        )

# Execute App
build_dashboard()
