import streamlit as st
import requests, json, time
import pytz

from PIL import Image
import firebase_admin
from firebase_admin import credentials, db

REFRESH_SEC = 5
# Simple safe refresh fallback for Streamlit Cloud
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
else:
    elapsed = time.time() - st.session_state.last_refresh
    if elapsed > REFRESH_SEC:
        st.session_state.last_refresh = time.time()
        # Delay rerun slightly to avoid early rerun errors
        st.rerun()

st.set_page_config(page_title="🏓 Live Pickle Round Viewer", layout="centered")

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

query = st.experimental_get_query_params()
code = (query.get("code", [None])[0] or "").strip()

if not code:
    typed = st.text_input("Enter 3-digit match code:", key="code_input", max_chars=3).strip()
    if typed:
        st.experimental_set_query_params(code=typed)
        code = typed
    else:
        st.stop()

if "last_refresh_ts" not in st.session_state:
    st.session_state.last_refresh_ts = 0.0

def init_firebase():
    if not firebase_admin._apps:
        import base64
        key_json = base64.b64decode(st.secrets["FIREBASE_KEY_B64"]).decode("utf-8")
        key_data = json.loads(key_json)
        cred = credentials.Certificate(key_data)
        firebase_admin.initialize_app(cred, {
            "databaseURL": st.secrets["FIREBASE_DB_URL"]
        })

init_firebase()
try:
    ref = db.reference(f"/rooms/live/{code}")
    data = ref.get()
except Exception as e:
    st.error(f"❌ Firebase fetch error: {e}")
    st.stop()

if not data:
    st.warning("🤪 When in doubt, it’s in. But this code? Definitely out!")
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
if st.button("🔄 Refresh Now"):
    st.rerun()

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
        from datetime import datetime
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
if st.button("🎮 Join another match"):
    st.experimental_set_query_params(code="")
    st.session_state.clear()
    st.rerun()

# Branding footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 14px; color: gray;'>"
    "🏓 Powered by <strong>PlayPickle</strong> • Created by <strong>Sai Kamasani 🧠</strong>"
    "</div>",
    unsafe_allow_html=True,
)