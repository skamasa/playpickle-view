import streamlit as st
import os, json, time

st.set_page_config(page_title="🏓 Live Pickle Round Viewer", layout="centered")
st.title("🏓 Live Match Viewer")

query = st.experimental_get_query_params()
room_id = query.get("room_id", [None])[0]

if not room_id:
    st.warning("❗ No room ID provided. Use a link shared by the organizer.")
    st.stop()

file_path = os.path.join("rooms", f"{room_id}.json")

if not os.path.exists(file_path):
    st.info("⌛ Waiting for game data...")
    st.stop()

st.markdown(f"### Room: `{room_id}`")

refresh_sec = 10
st.caption(f"Auto-refreshes every {refresh_sec} seconds")

placeholder = st.empty()

while True:
    if not os.path.exists(file_path):
        placeholder.warning("❌ Room file not found. The organizer may have ended the session.")
        time.sleep(refresh_sec)
        st.experimental_rerun()

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception:
        placeholder.error("⚠️ Could not read room data.")
        time.sleep(refresh_sec)
        st.experimental_rerun()

    round_no = data.get("round", "?")
    courts = data.get("courts", [])
    benched = data.get("benched", [])

    with placeholder.container():
        st.subheader(f"🏓 Round {round_no}")
        for i, court in enumerate(courts, 1):
            if len(court) == 4:
                st.write(f"🏟️ Court {i}: **{court[0]} + {court[1]}** vs **{court[2]} + {court[3]}**")
        if benched:
            st.write(f"🪑 Benched: {', '.join(benched)}")
        st.caption(f"Last updated: {data.get('updated', '')}")

    time.sleep(refresh_sec)
    st.experimental_rerun()