import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pytz
import time

st.set_page_config(page_title="PlayPickle Live Match Viewer", page_icon="🎾", layout="wide")

# ─────────────────────────────────────────────
# HEADER / BRANDING
# ─────────────────────────────────────────────
st.markdown(
    """
    <h1 style='text-align:center;'>
        <img src="https://raw.githubusercontent.com/skamasa/playpickle-view/main/pickleballrandom.png"
             width="50" style="vertical-align:middle;margin-right:10px;">
        PlayPickle 🧠 Live Match Viewer
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
REFRESH_SEC = 5  # auto refresh interval (seconds)
LOCAL_TZ = pytz.timezone("America/New_York")

# ─────────────────────────────────────────────
# FIREBASE INIT
# ─────────────────────────────────────────────
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(st.secrets["firebase"])
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://playpickle-live-default-rtdb.firebaseio.com/"
        })
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {e}")
        st.stop()

# ─────────────────────────────────────────────
# MATCH CODE INPUT
# ─────────────────────────────────────────────
st.subheader("🎯 Enter 3-Digit Match Code")
code_input = st.text_input("Enter match code", key="match_code_input")

if "code" not in st.session_state:
    st.session_state.code = None

if code_input:
    st.session_state.code = code_input.strip()

# ─────────────────────────────────────────────
# AUTO-REFRESH
# ─────────────────────────────────────────────
try:
    st_autorefresh = st.experimental_data_editor  # dummy line placeholder for compatibility
    st_autorefresh_interval = st.empty()
except Exception:
    pass

# ─────────────────────────────────────────────
# DISPLAY MATCH DATA
# ─────────────────────────────────────────────
if st.session_state.code:
    match_code = st.session_state.code
    ref = db.reference(f"/matches/{match_code}")

    try:
        data = ref.get()
    except Exception as e:
        st.error(f"⚠️ Error reading Firebase: {e}")
        data = None

    if not data:
        st.warning(
            "🤔 That code’s acting sneaky... like a let serve that *just clipped the net but didn’t count!*<br>"
            "Double-check your 3-digit code or ask your organizer again!",
            icon="🎾"
        )
    else:
        group_name = data.get("group_name", "Unknown Group")
        current_round = data.get("round_number", "N/A")
        courts = data.get("courts", [])
        benched = data.get("benched", [])
        timestamp = data.get("last_updated")

        st.markdown(f"### 🏓 **{group_name}** — Round {current_round}")
        st.markdown("---")

        # Show court matches
        for i, court in enumerate(courts, 1):
            st.markdown(
                f"🏟️ **Court {i}:** {court['team1']} vs {court['team2']}"
            )

        # Show benched players
        if benched:
            st.markdown(f"🪑 **Benched:** {', '.join(benched)}")

        # Show last-updated timestamp (local)
        if timestamp:
            try:
                utc_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(LOCAL_TZ)
                st.caption(f"🕒 Last updated: {local_dt.strftime('%b %d, %I:%M %p %Z')}")
            except Exception:
                st.caption("🕒 Last updated: N/A")

        st.markdown("---")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Refresh Now"):
                st.rerun()
        with col2:
            if st.button("🎮 Join another match"):
                st.session_state.clear()
                st.experimental_set_query_params(code="")
                time.sleep(0.5)
                st.rerun()
else:
    st.info("👋 Enter your 3-digit match code above to watch live rounds in real time 🎾")