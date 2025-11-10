import streamlit as st
import requests, json, time
from PIL import Image
import firebase_admin
from firebase_admin import credentials, db

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
code = query.get("code", [None])[0]

if not code:
    code = st.text_input("Enter 3-digit match code:", max_chars=3).strip()
    if not code:
        st.stop()

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

st_autorefresh_interval = st.autorefresh(interval=5 * 1000, key="auto_refresh_viewer")