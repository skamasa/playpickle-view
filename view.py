import streamlit as st
import requests, json, time

st.set_page_config(page_title="🏓 Live Pickle Round Viewer", layout="centered")
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

placeholder = st.empty()

def fetch_data():
    try:
        res = requests.get(DATA_URL, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

while True:
    data = fetch_data()
    if not data:
        placeholder.info("⌛ Waiting for game data...")
        time.sleep(refresh_sec)
        st.rerun()

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
        st.caption(f"Last updated: {data.get('updated', '')}")

    time.sleep(refresh_sec)
    st.rerun()