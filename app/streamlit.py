
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="FinSolve-AI Document Assistant", layout="wide")

# --- CSS & Dark-style theme + custom overrides ---
st.markdown("""
<style>
/* Hide Streamlit default header/menu/footer (optional) */
#MainMenu { visibility: hidden; }
header { visibility: hidden; }
footer { visibility: hidden; }

/* Main app background + text color (dark theme) */
.stApp {
    background-color: #0d0f14 !important;
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] {
    background-color: #111214 !important;
    color: #e0e0e0 !important;
}

/* Header banner styling */
.app-header {
    background-color: #1a1d23;
    padding: 16px 24px;
    display: flex;
    align-items: center;
}
.app-header h1 {
    margin: 0;
    color: #ffffff;
}

/* Sidebar login container styling */
.login-container {
    padding: 30px 10px;
    margin-top: 50px;
    background-color: #1e2228;
    border-radius: 8px;
    width: 95%;
    margin-left: auto;
    margin-right: auto;
}
.login-container .stTextInput > div > input,
.login-container .stTextInput > div > textarea,
.login-container .stTextInput > div > button,
.login-container .stButton > button {
    font-size: 1.0rem !important;
    padding: 6px 10px !important;
}
.login-container .stButton > button {
    background-color: #0055aa !important;
    color: white !important;
    border-radius: 4px !important;
}
.login-container .stButton > button:hover {
    background-color: #004080 !important;
}

/* Chat message bubbles / cards styling */
/* Note: class names might change across Streamlit versions — adjust if needed */
.st-chat-message, .css-1q90xif {  /* fallback class name example */
    background-color: #1d1f24 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
    color: #e0e0e0 !important;
}

/* Chat input box styling */
.css-yyulav > div { 
    background-color: #202327 !important;
    border: 1px solid #444 !important;
    border-radius: 4px !important;
    padding: 8px !important;
    color: #e0e0e0 !important;
}

/* Buttons styling (upload, create user/role, etc.) */
.stButton > button {
    background-color: #0066cc !important;
    color: white !important;
    border-radius: 4px !important;
}
.stButton > button:hover {
    background-color: #0051a8 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Header title banner ---
st.markdown('<div class="app-header"><h1>FinSolve-AI Document Assistant</h1></div>', unsafe_allow_html=True)

# --- Session-state initialization ---
if "auth" not in st.session_state:
    st.session_state.auth = None
if "user" not in st.session_state:
    st.session_state.user = None
if "roles" not in st.session_state:
    st.session_state.roles = []
if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar: login or logged-in user info + logout ---
with st.sidebar:
    if st.session_state.user is None:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.subheader("🔐 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                resp = requests.get(f"{API_URL}/login", auth=HTTPBasicAuth(username, password))
                if resp.status_code == 200:
                    data = resp.json()
                    role = data.get("role", "")
                    st.session_state.user = {"username": username, "role": role}
                    st.session_state.auth = (username, password)
                    # for admin (C-level), fetch roles list
                    if "c-levelexecutives" in role.lower():
                        roles_resp = requests.get(f"{API_URL}/roles", auth=HTTPBasicAuth(username, password))
                        if roles_resp.status_code == 200:
                            st.session_state.roles = roles_resp.json().get("roles", [])
                    st.rerun()
                else:
                    st.error("Login failed: invalid credentials.")
            except Exception as e:
                st.error(f"Connection error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    else:
        st.write(f"**User:** {st.session_state.user.get('username')}")
        st.write(f"**Role:** {st.session_state.user.get('role')}")
        if st.button("Logout"):
            for key in ("auth", "user", "roles", "history"):
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# --- After login: main UI content ---
user = st.session_state.user
if not isinstance(user, dict):
    st.error("Invalid session. Please login again.")
    st.stop()

role = user.get("role", "").lower()

# Determine tabs based on role
if "c-levelexecutives" in role:
    tab_labels = ["💬 Chat", "📤 Upload Docs", "🛠️ Admin"]
else:
    tab_labels = ["💬 Chat"]

tabs = st.tabs(tab_labels)

### --- Chat Tab ---
with tabs[0]:
    
    st.caption("Ask me anything about your documents.")

    # Initial greeting if first time
    if len(st.session_state.history) == 0:
        st.session_state.history.append(("assistant", "Hello! I am your AI assistant. How can I help you today?"))

    # Role & Access explanation
    with st.expander("📘 Role & Access Explanation", expanded=False):
        ur = role
        if "c-levelexecutives" in ur:
            st.info("Unfiltered access — full visibility (C-Level Executives).")
        elif "employee" in ur:
            st.info("Filtered access — only general (public) documents (Employee).")
        else:
            st.info(f"Filtered by department: `{ur}`.")

    # Display chat history
    for speaker, message in st.session_state.history:
        with st.chat_message(speaker):
            st.markdown(message)

    # Input
    prompt = st.chat_input("Type your question here…")
    if prompt:
        st.session_state.history.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Fetching answer..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={"user": user, "message": prompt},
                    auth=HTTPBasicAuth(*st.session_state.auth)
                )
                if resp.status_code == 200:
                    answer = resp.json().get("response", "")
                else:
                    answer = f"⚠️ Server error: {resp.status_code}"
            except Exception as e:
                answer = f"🚫 Connection error: {e}"

        st.session_state.history.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.markdown(answer)

### --- Upload Docs Tab (only for admin) ---
if "c-levelexecutives" in role and len(tabs) >= 2:
    with tabs[1]:
        st.subheader("📤 Upload Document (.md or .csv)")
        selected_role = st.selectbox("Assign Role / Department:", st.session_state.roles)
        doc_file = st.file_uploader("Choose file to upload", type=["md", "csv"])
        if st.button("Upload"):
            if doc_file:
                files = {"file": (doc_file.name, doc_file.getvalue())}
                data = {"role": selected_role}
                try:
                    res = requests.post(
                        f"{API_URL}/upload-docs",
                        files=files,
                        data=data,
                        auth=HTTPBasicAuth(*st.session_state.auth)
                    )
                    if res.status_code == 200 or res.ok:
                        st.success(res.json().get("message", "Upload successful."))
                    else:
                        st.error(f"Upload failed: {res.status_code} — {res.text}")
                except Exception as e:
                    st.error("Connection error: " + str(e))
            else:
                st.warning("Please select a file first.")

### --- Admin Tab (only for admin) ---
if "c-levelexecutives" in role and len(tabs) >= 3:
    with tabs[2]:
        st.subheader("🛠️ User & Role Management")

        st.markdown("#### Create New User")
        new_user = st.text_input("Username", key="new_user")
        new_pass = st.text_input("Password", type="password", key="new_pass")
        new_role = st.selectbox("Role", st.session_state.roles, key="new_user_role")
        if st.button("Create User"):
            try:
                res = requests.post(
                    f"{API_URL}/create-user",
                    data={"username": new_user, "password": new_pass, "role": new_role},
                    auth=HTTPBasicAuth(*st.session_state.auth)
                )
                if res.status_code == 200 or res.ok:
                    st.success(res.json().get("message", "User created."))
                else:
                    st.error(f"Create user failed: {res.status_code} — {res.text}")
            except Exception as e:
                st.error("Connection error: " + str(e))

        st.markdown("---")

        st.markdown("#### Create New Role")
        new_role_input = st.text_input("New Role Name", key="new_role_input")
        if st.button("Add Role"):
            try:
                res = requests.post(
                    f"{API_URL}/create-role",
                    data={"role_name": new_role_input},
                    auth=HTTPBasicAuth(*st.session_state.auth)
                )
                if res.status_code == 200 or res.ok:
                    st.success(res.json().get("message", "Role added."))
                    # Refresh roles list
                    roles_resp = requests.get(
                        f"{API_URL}/roles",
                        auth=HTTPBasicAuth(*st.session_state.auth)
                    )
                    if roles_resp.status_code == 200:
                        st.session_state.roles = roles_resp.json().get("roles", [])
                        st.rerun()
                else:
                    st.error(f"Add role failed: {res.status_code} — {res.text}")
            except Exception as e:
                st.error("Connection error: " + str(e))


