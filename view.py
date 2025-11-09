import streamlit as st
import requests, json, time

st.set_page_config(page_title="🏓 Live Pickle Round Viewer", layout="centered")
st.image("pickleballrandom.png", use_container_width=False, width=150)
st.title("🏓 Live Match Viewer")

query = st.experimental_get_query_params()
room_id = query.get("room_id", [None])[0]

if not room_id:
    st.warning("❗ No room ID provided. Use a link shared by the organizer.")
    st.stop()

# Remote GitHub data source
DATA_URL = f"https://raw.githubusercontent.com/skamasa/playpickle-data/main/rooms/{room_id}.json"

refresh_sec = 10
st.caption(f"Auto-refreshes every {refresh_sec} seconds")
st_autorefresh = st.autorefresh(interval=refresh_sec * 1000, key="auto_refresh_viewer")

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
    st.markdown(f"### Room: `{room_id}`")
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