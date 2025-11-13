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

def safe_rerun():
    """
    Cross-version safe rerun helper for Streamlit.
    Uses st.rerun() when available, falls back to st.experimental_rerun().
    Any unexpected errors are swallowed to avoid crashing the viewer.
    """
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        # On Streamlit Cloud, avoid surfacing rerun-related crashes
        pass

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

# Auto-load the latest live match (no code required)
live_data = db.reference("/rooms/live").get() or {}

if not live_data:
    st.warning("No live games at this moment.")
    live_data = {}

latest_code = None
data = None

if live_data:
    latest_code = max(
        live_data.keys(),
        key=lambda c: live_data[c].get("timestamp_epoch", 0)
    )
    data = live_data.get(latest_code)

if data:
    round_no = data.get("round", "?")
    courts = data.get("courts", [])
    benched = data.get("benched", [])

    st.markdown(
        f"""
        <div style='display: flex; align-items: center; gap: 12px; height: 100%; margin-top: 10px;'>
            <h1 style='margin: 0;'>Live Playpickle Viewer</h1>
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
        safe_rerun()

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

# Safe rerun handler
if st.session_state.get("force_rerun"):
    st.session_state.force_rerun = False
    safe_rerun()

st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 14px; color: gray;'>"
    "🏓 Powered by <strong>PlayPickle</strong> • Created by <strong>Sai Kamasani 🧠</strong>"
    "</div>",
    unsafe_allow_html=True,
)