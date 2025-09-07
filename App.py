import requests
import streamlit as st
import pandas as pd

BASE = "https://fantasy.premierleague.com/api"

# --- Helpers ---
@st.cache_data(ttl=600)
def league_standings(league_id):
    url = f"{BASE}/leagues-classic/{league_id}/standings/"
    return requests.get(url).json()

@st.cache_data(ttl=600)
def team_history(team_id):
    url = f"{BASE}/entry/{team_id}/history/"
    return requests.get(url).json()

# --- Mini-League Wrapped ---
def league_wrapped(league_id):
    data = league_standings(league_id)
    members = data["standings"]["results"]

    table = []
    for m in members:
        tid = m["entry"]
        hist = team_history(tid)["current"]

        gw_points = [g["points"] for g in hist]
        best_gw = max(hist, key=lambda g: g["points"])

        table.append({
            "Manager": m["player_name"],
            "Team": m["entry_name"],
            "Total Points": m["total"],
            "Rank": m["rank"],
            "Best GW": best_gw["event"],
            "Best GW Points": best_gw["points"],
            "Bench Points": sum(g.get("points_on_bench", 0) for g in hist),
            "Captain Points": sum(g.get("cpoints", 0) for g in hist),
        })

    df = pd.DataFrame(table)
    return df.sort_values("Rank")

# --- Streamlit UI ---
st.title("⚽ FPL Wrapped (Mini-League)")

choice = st.radio("Choose mode:", ["Mini-League", "Team"])

if choice == "Mini-League":
    lid = st.text_input("Enter Mini-League ID:")
    if st.button("Generate"):
        df = league_wrapped(int(lid))
        st.subheader("League Summary")
        st.dataframe(df)

        champ = df.iloc[0]
        st.success(f"🏆 Champion: {champ['Manager']} ({champ['Team']}) with {champ['Total Points']} points")

elif choice == "Team":
    tid = st.text_input("Enter Team ID:")
    if st.button("Generate"):
        hist = team_history(int(tid))["current"]
        total = sum(g["points"] for g in hist)
        best = max(hist, key=lambda g: g["points"])
        st.subheader(f"Team Wrapped (ID {tid})")
        st.write(f"Total Points: {total}")
        st.write(f"Best GW: GW{best['event']} — {best['points']} points")
