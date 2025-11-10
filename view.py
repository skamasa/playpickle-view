import streamlit as st
import requests, json, time
import pytz
from datetime import datetime

from PIL import Image
import firebase_admin
from firebase_admin import credentials, db

REFRESH_SEC = 5
# Simple safe refresh fallback for Streamlit Cloud
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

col1, col2 = st.columns([1, 8])
try:
    logo = Image.open("assets/pickleballrandom.png")
    col1.image(logo, width=70)
except Exception:
    col1.markdown("<div style='color: gray; font-size: 14px;'>[Logo not found]</div>", unsafe_allow_html=True)
with col2:
    st.markdown(
        """
        <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
        .live-badge {
            display: flex;
            align-items: center;
            background-color: #d32f2f;
            color: white;
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 600;
            margin-left: 10px;
            animation: pulse 2s infinite;
        }
        .live-dot {
            width: 10px;
            height: 10px;
            background-color: #ff5252;
            border-radius: 50%;
            margin-right: 6px;
        }
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        h1, h2, h3, h4, h5, h6, p, div, span {
            color: var(--text-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

if "code" not in st.session_state:
    st.session_state.code = None

if not st.session_state.code:
    # Landing page: show code input and enter button
    st.markdown("<h1 style='margin: 0;'>Live Match Viewer</h1>", unsafe_allow_html=True)
    typed_code = st.text_input("Enter 3-digit match code:", max_chars=3).strip()
    if st.button("🎟️ Enter Match"):
        if typed_code and len(typed_code) == 3:
            st.session_state.code = typed_code
            st.experimental_set_query_params(code=typed_code)
            st.session_state.ready = True
        else:
            st.warning("🤪 When in doubt, it’s in — but this code? Definitely out!")
    elif typed_code and len(typed_code) == 3:
        # If user typed a code but didn't press enter yet, no warning here
        pass
    elif typed_code:
        st.warning("🤪 When in doubt, it’s in — but this code? Definitely out!")

    if st.session_state.get("ready"):
        st.session_state.ready = False
        # Instead of immediate rerun, exit early so rerun happens safely
        st.experimental_set_query_params(code=st.session_state.code)
        st.stop()

else:
    code = st.session_state.code

    if "last_refresh_ts" not in st.session_state:
        st.session_state.last_refresh_ts = 0.0

    @st.cache_resource
    def init_firebase():
        if not firebase_admin._apps:
            import base64
            key_json = base64.b64decode(st.secrets["FIREBASE_KEY_B64"]).decode("utf-8")
            key_data = json.loads(key_json)
            cred = credentials.Certificate(key_data)
            firebase_admin.initialize_app(cred, {
                "databaseURL": st.secrets["FIREBASE_DB_URL"]
            })

    @st.cache_data(ttl=5)
    def get_room_data(code):
        ref = db.reference(f"/rooms/live/{str(code)}")
        return ref.get()

    init_firebase()
    try:
        data = get_room_data(code)
        if not data:
            st.warning("🤪 When in doubt, it’s in — but this code? Definitely out!")
            st.session_state.code = None
            st.experimental_set_query_params()
            st.stop()
    except Exception as e:
        st.error(f"❌ Firebase fetch error: {e}")
        st.stop()

    round_no = data.get("round", "?")
    courts = data.get("courts", [])
    benched = data.get("benched", [])

    st.markdown(
        f"""
        <div style='display: flex; align-items: center; gap: 12px; height: 100%; margin-top: 10px;'>
            <h1 style='margin: 0;'>Live Match Viewer — Code {code}</h1>
            <div class='live-badge'><div class='live-dot'></div>LIVE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    group_name = data.get("group_name", "Unknown Group")
    timestamp = data.get("timestamp", "Unknown Time")
    st.markdown(f"### 🥒 *COME ON!!!* Here’s what’s cooking for **{group_name}**")
    st.subheader(f"🏓 Round {round_no}")
    st.markdown("Want to see who’s serving next? Tap **Refresh Now** to view the current round!")
    if st.button("🔄 Refresh Now"):
        st.experimental_rerun()

    for i, court in enumerate(courts, 1):
        players = []
        if isinstance(court, dict) and "players" in court:
            players = court["players"]
        elif isinstance(court, list) and len(court) == 4:
            players = court
        elif isinstance(court, list) and len(court) == 2 and all(isinstance(p, list) for p in court):
            players = court[0] + court[1]
        else:
            st.write(f"🏟️ Court {i}: Data unavailable or invalid format")
            continue

        if len(players) == 4:
            st.write(f"🏟️ Court {i}: **{players[0]} + {players[1]}** vs **{players[2]} + {players[3]}**")
        else:
            st.write(f"🏟️ Court {i}: Unexpected data format")

    if benched:
        st.write(f"🪑 Benched: {', '.join(benched)}")

    # Compute a friendly last-updated string from available fields
    last_updated_text = None
    # Prefer epoch fields if present
    ts_epoch = data.get("last_updated") or data.get("timestamp_epoch")
    if isinstance(ts_epoch, (int, float)):
        try:
            est = pytz.timezone("America/New_York")
            local_dt = datetime.fromtimestamp(ts_epoch, est)
            last_updated_text = local_dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")
        except Exception:
            local_time = time.strftime("%Y-%m-%d %I:%M:%S %p %Z", time.localtime(ts_epoch))
            last_updated_text = f"{local_time}"
    # Fallback to ISO/string timestamp if provided
    if not last_updated_text:
        last_updated_text = data.get("timestamp") or data.get("updated") or "Just now"
    st.caption(f"⏱️ Last updated: {last_updated_text}")

    st.markdown("---")

    if st.button("🎮 Switch to another live match"):
        # Clear relevant session data safely
        for key in ["code", "ready", "last_refresh_ts"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params()
        # Flag safe reset and stop current execution to avoid AttributeError
        st.session_state.reset_app = True
        st.stop()

# Safe rerun handler
if st.session_state.get("reset_app"):
    st.session_state.reset_app = False
    st.experimental_rerun()
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; font-size: 14px; color: gray;'>"
        "🏓 Powered by <strong>PlayPickle</strong> • Created by <strong>Sai Kamasani 🧠</strong>"
        "</div>",
        unsafe_allow_html=True,
    )