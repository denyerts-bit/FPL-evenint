import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE = "https://fantasy.premierleague.com/api"

# ---------- API ----------
@st.cache_data(ttl=600)
def league_standings(league_id):
    return requests.get(f"{BASE}/leagues-classic/{league_id}/standings/").json()

@st.cache_data(ttl=600)
def team_history(team_id):
    return requests.get(f"{BASE}/entry/{team_id}/history/").json()

# ---------- Analytics ----------
def league_wrapped(league_id):
    data = league_standings(league_id)
    members = data["standings"]["results"]

    out = []
    for m in members:
        tid = m["entry"]
        hist = team_history(tid)["current"]
        if not hist: continue

        total = sum(g["points"] for g in hist)
        best_gw = max(hist, key=lambda g: g["points"])
        bench = sum(g.get("points_on_bench", 0) for g in hist)
        cap = sum(g.get("cpoints", 0) for g in hist)
        consistency = np.std([g["points"] for g in hist]) if len(hist)>1 else 0

        out.append({
            "Manager": m["player_name"],
            "Team": m["entry_name"],
            "Rank": m["rank"],
            "Total Points": m["total"],
            "Best GW": best_gw["event"],
            "Best GW Points": best_gw["points"],
            "Bench Points": bench,
            "Captain Points": cap,
            "Consistency": consistency
        })
    return pd.DataFrame(out).sort_values("Rank").reset_index(drop=True)

# ---------- Card UI ----------
def card(title, text, emoji="⭐", color="#0f5132"):
    st.markdown(
        f"""
        <div style='background:{color};color:white;padding:30px;
        border-radius:15px;margin:10px;text-align:center;'>
        <h2>{emoji} {title}</h2>
        <p style='font-size:20px;'>{text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------- Streamlit ----------
st.set_page_config(page_title="FPL Wrapped", layout="wide")
st.title("⚽ FPL Wrapped — Shareable Edition")

lid = st.text_input("Enter Mini-League ID:")

if st.button("Generate Wrapped") and lid.isdigit():
    df = league_wrapped(int(lid))

    if df.empty:
        st.error("No data found")
    else:
        champ = df.iloc[0]
        hero = df.loc[df["Best GW Points"].idxmax()]
        bench = df.loc[df["Bench Points"].idxmax()]
        cap = df.loc[df["Captain Points"].idxmax()]
        cons = df.loc[df["Consistency"].idxmin()]

        card("Champion 🏆", f"{champ['Manager']} ({champ['Team']}) — {champ['Total Points']} pts", "#198754")
        card("GW Hero 🔥", f"{hero['Manager']} scored {hero['Best GW Points']} in GW{hero['Best GW']}", "#dc3545")
        card("Bench Blunder 😬", f"{bench['Manager']} left {bench['Bench Points']} pts on the bench", "#fd7e14")
        card("Captain King 👑", f"{cap['Manager']} earned {cap['Captain Points']} from captains", "#0d6efd")
        card("Consistency 📈", f"{cons['Manager']} was most consistent (std dev {cons['Consistency']:.1f})", "#6f42c1")

        # Add a simple points vs bench chart
        st.subheader("📊 Points vs Bench Points")
        fig, ax = plt.subplots()
        ax.scatter(df["Total Points"], df["Bench Points"])
        for _, r in df.iterrows():
            ax.text(r["Total Points"], r["Bench Points"], r["Manager"], fontsize=7)
        ax.set_xlabel("Total Points")
        ax.set_ylabel("Bench Points")
        st.pyplot(fig)
