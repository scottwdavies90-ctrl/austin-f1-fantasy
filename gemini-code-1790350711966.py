import streamlit as st
import requests
import pandas as pd

# Page Setup
st.set_page_config(
    page_title="Austin FF F1 Championship",
    page_icon="🏎️",
    layout="wide"
)

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

# Native Streamlit fragment decorator handles auto-refresh every 30s
@st.fragment(run_every="30s")
def render_dashboard():
    data = fetch_espn_data()

    # Header Section
    st.title("🏎️ F1 DRIVERS' CHAMPIONSHIP")
    st.caption("Live Telemetry & Standings | Auto-refreshes every 30 seconds")

    if not data:
        st.error("Unable to connect to ESPN API. Please ensure your league is set to 'Public' in ESPN League Settings.")
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

    # 2. Parse Matchup Data & Scores
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

        # Record W-L-T
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

    # 3. Calculate F1 Points & Podium Stats
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

    # Identify DNF Team (lowest score in latest active week)
    dnf_team_id = None
    if latest_completed_week > 0 and weekly_scores[latest_completed_week]:
        latest = sorted(weekly_scores[latest_completed_week], key=lambda x: x["score"])
        if latest:
            dnf_team_id = latest[0]["teamId"]

    # Sort Standings: Primary = F1 Points (Desc), Tiebreaker = Total Fantasy Points (Desc)
    sorted_teams = sorted(
        standings.values(),
        key=lambda x: (x["f1"], x["points"]),
        reverse=True
    )

    # 4. Top KPI Highlight Cards
    col1, col2, col3 = st.columns(3)
    leader_name = sorted_teams[0]["name"] if sorted_teams else "N/A"
    top_scorer_name = max(standings.values(), key=lambda x: x["points"])["name"] if standings else "N/A"
    dnf_name = teams_map.get(dnf_team_id, "None") if dnf_team_id else "None"

    col1.metric("🏆 Championship Leader (P1)", leader_name)
    col2.metric("🎯 Top Fantasy Scorer", top_scorer_name)
    col3.metric("💥 Latest DNF / Engine Failure", dnf_name)

    st.divider()

    # 5. Build Leaderboard
    table_data = []
    for idx, t in enumerate(sorted_teams):
        # Driver Form Indicator (Last 3 Weeks)
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
            
        status = "💥 DNF Engine Failure" if dnf_team_id and teams_map[dnf_team_id] == t["name"] else "✅ CLASSIFIED"
        
        table_data.append({
            "Rank": f"P{idx + 1}",
            "Team Name": t["name"],
            "Form": form,
            "Status": status,
            "F1 Points": t["f1"],
            "Total Points": round(t["points"], 2),
            "Record": f"{t['wins']}-{t['losses']}-{t['ties']}",
            "P1 Wins": t["p1"],
            "Podiums": t["podiums"]
        })

    df = pd.DataFrame(table_data)

    st.subheader("🏎️ Drivers' Championship Standings")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 6. F1 Points Bar Chart
    st.subheader("📊 Cumulative F1 Points Visualizer")
st.bar_chart(
    df,
    x="Team Name",
    y="F1 Points",
    sort=False,
    horizontal=True
)

render_dashboard()
