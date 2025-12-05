import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

API_URL = "http://127.0.0.1:8000"

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="FinSolve AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------------------------------
# SESSION VARIABLES (must be at top)
# -----------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

if "greeted" not in st.session_state:
    st.session_state.greeted = False

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# -----------------------------------------------------
# THEME CSS (LIGHT + DARK, PREMIUM)
# -----------------------------------------------------
def apply_theme():
    if st.session_state.dark_mode:
        # Dark theme
        st.markdown("""
        <style>
        .stApp {
            background-color: #05070A;
            color: #EAEAEA;
        }

        [data-testid="stSidebar"] {
            background-color: #0D1117 !important;
            color: #EAEAEA !important;
            border-right: 1px solid #30363D;
        }

        h1, h2, h3, h4, h5, h6, label, p, span {
            color: #EAEAEA !important;
        }

        .stTextInput input {
            background-color: #161B22 !important;
            color: #F0F6FC !important;
            border-radius: 10px !important;
            border: 1px solid #30363D !important;
        }

        .stButton button {
            background-color: #238636 !important;
            color: #FFFFFF !important;
            border-radius: 999px !important;
            padding: 8px 22px !important;
            font-size: 15px !important;
            border: none !important;
        }
        .stButton button:hover {
            background-color: #2EA043 !important;
        }

        .answer-card {
            background: rgba(22, 27, 34, 0.9);
            border-radius: 16px;
            border: 1px solid #30363D;
            padding: 18px 20px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
        }

        .answer-title {
            font-weight: 700;
            margin-bottom: 6px;
            font-size: 16px;
        }

        .answer-body {
            font-size: 15px;
            line-height: 1.6;
        }

        .sources-card {
            margin-top: 14px;
            background: #0D1117;
            border-radius: 12px;
            border: 1px solid #30363D;
            padding: 12px 16px;
            font-size: 14px;
        }

        .role-expander > details {
            border-radius: 12px !important;
            border: 1px solid #30363D !important;
            background-color: #0D1117 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light theme
        st.markdown("""
        <style>
        .stApp {
            background-color: #F5F7FB;
            color: #000000;
        }

        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border-right: 1px solid #E0E4EC;
        }

        .stTextInput input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border-radius: 10px !important;
            border: 1px solid #C5CAD6 !important;
        }

        .stButton button {
            background-color: #1A73E8 !important;
            color: #FFFFFF !important;
            border-radius: 999px !important;
            padding: 8px 22px !important;
            font-size: 15px !important;
            border: none !important;
        }
        .stButton button:hover {
            background-color: #1558B0 !important;
        }

        .answer-card {
            background: #FFFFFF;
            border-radius: 16px;
            border: 1px solid #E0E4EC;
            padding: 18px 20px;
            box-shadow: 0 16px 35px rgba(15, 23, 42, 0.08);
        }

        .answer-title {
            font-weight: 700;
            margin-bottom: 6px;
            font-size: 16px;
            color: #111827;
        }

        .answer-body {
            font-size: 15px;
            line-height: 1.6;
            color: #111827;
        }

        .sources-card {
            margin-top: 14px;
            background: #F9FAFB;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            padding: 12px 16px;
            font-size: 14px;
        }

        .role-expander > details {
            border-radius: 12px !important;
            border: 1px solid #E0E4EC !important;
            background-color: #FFFFFF !important;
        }
        </style>
        """, unsafe_allow_html=True)


apply_theme()

# -----------------------------------------------------
# SIDEBAR LOGIN
# -----------------------------------------------------
with st.sidebar:
    st.title("🔐 Login")

    if st.session_state.user is None:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            resp = requests.get(
                f"{API_URL}/login",
                auth=HTTPBasicAuth(username, password)
            )

            if resp.status_code == 200:
                data = resp.json()
                st.session_state.user = {"username": username, "role": data["role"]}
                st.session_state.history = []
                st.session_state.greeted = False
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.stop()  # stop here if not logged in

    else:
        st.write(f"👤 User: {st.session_state.user['username']}")
        st.write(f"🛡️ Role: {st.session_state.user['role']}")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.history = []
            st.session_state.greeted = False
            st.rerun()


# -----------------------------------------------------
# HEADER WITH PREMIUM THEME TOGGLE
# -----------------------------------------------------
header_left, header_right = st.columns([8, 2])

with header_left:
    st.markdown("")  # small spacer

with header_right:
    # styles for toggle container
    st.markdown("""
        <style>
        .theme-toggle-box {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
            margin-top: 8px;
            padding: 6px 12px;
            border-radius: 999px;
            background-color: rgba(148, 163, 184, 0.16);
        }
        .theme-toggle-text {
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="theme-toggle-box">', unsafe_allow_html=True)
    tcol1, tcol2 = st.columns([1, 2])

    with tcol1:
        toggle = st.toggle(" ", value=st.session_state.dark_mode, label_visibility="collapsed")

    with tcol2:
        label = "🌗 Dark Mode" if st.session_state.dark_mode else "💡 Light Mode"
        st.markdown(f'<span class="theme-toggle-text">{label}</span>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = toggle
        st.rerun()


# -----------------------------------------------------
# MAIN TITLE + ROLE INFO
# -----------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.title("🤖 FinSolve AI Assistant")
st.caption("Ask me anything about your allowed documents.")

# Greeting
if not st.session_state.greeted:
    st.info("👋 Hello! I am your AI assistant. How can I help you today?")
    st.session_state.greeted = True

# Role explanation
with st.expander("📘 Role & Access Explanation", expanded=False):
    expander_container = st.container()
    expander_container.markdown('<div class="role-expander"></div>', unsafe_allow_html=True)
    role = st.session_state.user["role"].lower()

    if "c-levelexecutives" in role:
        st.success("🔓 Full access — You can view all department documents.")
    elif "employee" in role:
        st.info("📂 Employee access — You can only view **general** category documents.")
    else:
        st.warning(f"📁 Department filter — You can view **{role}** documents (plus general, if allowed).")


# -----------------------------------------------------
# TABS (Chat / Upload / Admin)
# -----------------------------------------------------
role_full = st.session_state.user["role"]

if "c-levelexecutives" in role_full.lower():
    tab_chat, tab_upload, tab_admin = st.tabs(["💬 Chat", "📤 Upload Docs", "⚙️ Admin"])

    # fetch roles once for upload + admin
    try:
        roles_response = requests.get(f"{API_URL}/roles")
        roles = roles_response.json().get("roles", [])
    except Exception:
        roles = []
else:
    (tab_chat,) = st.tabs(["💬 Chat"])
    roles = []  # not used for non-C-level


# -----------------------------------------------------
# CHAT TAB
# -----------------------------------------------------
with tab_chat:
    st.subheader("Ask a question")

    question = st.text_input("Your question here...")

    if st.button("Ask"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing your documents…"):
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={"user": st.session_state.user, "message": question},
                    # backend doesn't require auth for /chat, but this won't hurt
                    auth=HTTPBasicAuth(st.session_state.user["username"], "")
                )

                if resp.status_code != 200:
                    st.error("Server error: Could not get a response.")
                else:
                    data = resp.json()
                    answer = data.get("response", "")

                    # Answer card
                    st.markdown(
                        f"""
                        <div class="answer-card">
                            <div class="answer-title">✅ Answer</div>
                            <div class="answer-body">{answer}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Sources card
                    sources = data.get("sources", [])
                    if sources:
                        st.markdown(
                            """
                            <div class="sources-card">
                                <b>📄 Sources used:</b><br>
                            """,
                            unsafe_allow_html=True,
                        )
                        for s in sources:
                            st.markdown(f"- {s}")
                        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------
# UPLOAD DOCS TAB (C-Level Only)
# -----------------------------------------------------
if "c-levelexecutives" in role_full.lower():
    with tab_upload:
        st.subheader("📤 Upload Documents")

        upload_role = st.selectbox("Select role for document access", roles) if roles else st.text_input("Role")
        doc_file = st.file_uploader("Upload file (.txt, .md, .csv, .pdf)", type=["txt", "md", "csv", "pdf"])

        if st.button("Upload") and doc_file:
            with st.spinner("Uploading & indexing document..."):
                try:
                    res = requests.post(
                        f"{API_URL}/upload-docs",
                        data={"role": upload_role},
                        files={"file": doc_file},
                        auth=HTTPBasicAuth(st.session_state.user["username"], "")
                    )
                    if res.ok:
                        st.success(res.json().get("message", "Upload successful."))
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")


# -----------------------------------------------------
# ADMIN TAB (C-Level Only)
# -----------------------------------------------------
if "c-levelexecutives" in role_full.lower():
    with tab_admin:
        st.subheader("⚙️ Admin Controls")

        # Add user section
        st.markdown("### ➕ Add User")
        new_user = st.text_input("New username")
        new_pass = st.text_input("New password", type="password")
        new_role = st.selectbox("Assign role", roles) if roles else st.text_input("Role name")

        if st.button("Create User"):
            if not new_user or not new_pass or not new_role:
                st.warning("Please fill all fields.")
            else:
                try:
                    res = requests.post(
                        f"{API_URL}/create-user",
                        data={"username": new_user, "password": new_pass, "role": new_role},
                    )
                    if res.ok:
                        st.success(res.json().get("message", "User created."))
                    else:
                        st.error(f"Could not create user: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

        st.markdown("---")

        # Add role section
        st.markdown("### ➕ Create New Role")
        new_role_input = st.text_input("New role name")

        if st.button("Add Role"):
            if not new_role_input:
                st.warning("Please enter a role name.")
            else:
                try:
                    res = requests.post(
                        f"{API_URL}/create-role",
                        data={"role_name": new_role_input},
                    )
                    if res.ok:
                        st.success(res.json().get("message", "Role added."))
                    else:
                        st.error(f"Could not create role: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
