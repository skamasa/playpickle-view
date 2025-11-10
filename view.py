typed_code = st.text_input("Enter 3-digit match code:", key="code_input", max_chars=3).strip()

# Detect a new or changed code entry
if typed_code and len(typed_code) == 3 and typed_code != st.session_state.get("code", ""):
    st.session_state.code = typed_code
    st.session_state.last_code_valid = False  # reset validity flag
    st.experimental_set_query_params(code=typed_code)
    time.sleep(0.2)
    st.experimental_rerun()

code = st.session_state.get("code")

# Handle missing or invalid code early
if not code:
    st.stop()

# Fetch Firebase data
try:
    ref = db.reference(f"/rooms/live/{str(code)}")
    data = ref.get()
    if not data:
        st.session_state.last_code_valid = False
        st.warning("🤪 When in doubt, it’s in — but this code? Definitely out!")
        st.stop()
    else:
        st.session_state.last_code_valid = True
except Exception as e:
    st.error(f"❌ Firebase fetch error: {e}")
    st.stop()

# Ensure rerun after recovering from invalid state
if not st.session_state.get("last_code_valid", False):
    st.experimental_rerun()