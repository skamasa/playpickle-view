import streamlit as st
import requests, json, time

st.set_page_config(page_title="🏓 Live Pickle Round Viewer", layout="centered")
col1, col2 = st.columns([1, 8])
with col1:
    st.markdown("<div style='display: flex; align-items: center; justify-content: center; height: 100%;'><img src='assets/pickleballrandom.png' width='70'></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<h1 style='display: flex; align-items: center; height: 100%; margin-top: 10px;'>Live Match Viewer</h1>", unsafe_allow_html=True)

query = st.experimental_get_query_params()
room_id = query.get("room_id", [None])[0]

if not room_id:
    st.warning("❗ No room ID provided. Use a link shared by the organizer.")
    st.stop()

# Remote GitHub data source
DATA_URL = f"https://raw.githubusercontent.com/skamasa/playpickle-data/main/rooms/{room_id}.json"

refresh_sec = 10
st.caption(f"Auto-refreshes every {refresh_sec} seconds")

placeholder = st.empty()

def fetch_data():
    try:
        res = requests.get(DATA_URL, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

data = fetch_data()
if not data:
    placeholder.info("⌛ Waiting for game data...")
    st.stop()

round_no = data.get("round", "?")
courts = data.get("courts", [])
benched = data.get("benched", [])

with placeholder.container():
    group_name = data.get("group_name", "Unknown Group")
    timestamp = data.get("updated", "Unknown Time")
    st.markdown(f"### 🥒 *COME ON!!!* Here’s what’s cooking for **{group_name}**  \n🕒 {timestamp}")
    st.subheader(f"🏓 Round {round_no}")

    for i, court in enumerate(courts, 1):
        if len(court) == 4:
            st.write(f"🏟️ Court {i}: **{court[0]} + {court[1]}** vs **{court[2]} + {court[3]}**")

    if benched:
        st.write(f"🪑 Benched: {', '.join(benched)}")

    st.caption(f"⏱️ Last updated: {data.get('updated', 'N/A')}")

# Branding footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 14px; color: gray;'>"
    "🏓 Powered by <strong>PlayPickle</strong> • Created by <strong>Sai Kamasani 🧠</strong>"
    "</div>",
    unsafe_allow_html=True,
)

# ---- Auto-refresh (fallback) ----
time.sleep(refresh_sec)
st.rerun()