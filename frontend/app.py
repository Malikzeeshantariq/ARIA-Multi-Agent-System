import os
import json
import streamlit as st
import requests
import time
import base64

st.set_page_config(
    page_title="ARIA — AI Research Intelligence Agent",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Claude-inspired Design System ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@300;400;500&family=Geist:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --clay:    #E8E0D5;
  --sand:    #D4C9B8;
  --dusk:    #2D2A26;
  --ember:   #8B4513;
  --coral:   #CC5500;
  --mist:    #F5F0E8;
  --ink:     #1A1714;
  --ghost:   #9B9589;
  --line:    rgba(45,42,38,0.12);
  --warm-glow: rgba(139,69,19,0.08);
}

/* ── Global ── */
.stApp {
  background: var(--mist) !important;
  font-family: 'Geist', sans-serif;
}
.main .block-container {
  padding: 2rem 2.5rem !important;
  max-width: 1100px !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
.stDeployButton { display: none; }

/* ── Typography ── */
h1, h2, h3 {
  font-family: 'Instrument Serif', Georgia, serif !important;
  color: var(--ink) !important;
}

/* ── Hero Header ── */
.aria-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 2.5rem 0 2rem;
  border-bottom: 1px solid var(--line);
  margin-bottom: 2.5rem;
  position: relative;
}
.aria-header::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 0;
  width: 80px; height: 2px;
  background: var(--coral);
}
.aria-wordmark {
  font-family: 'Instrument Serif', serif;
  font-size: 2.8rem;
  color: var(--ink);
  letter-spacing: -1px;
  line-height: 1;
}
.aria-wordmark span {
  color: var(--coral);
}
.aria-tagline {
  font-family: 'Geist Mono', monospace;
  font-size: 0.68rem;
  color: var(--ghost);
  letter-spacing: 2.5px;
  text-transform: uppercase;
  margin-top: 6px;
}
.aria-badge {
  font-family: 'Geist Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--coral);
  border: 1px solid rgba(204,85,0,0.3);
  padding: 5px 12px;
  border-radius: 2px;
  background: rgba(204,85,0,0.06);
}

/* ── Input Zone ── */
.input-zone {
  background: white;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.zone-label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--ghost);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.zone-label::before {
  content: '';
  width: 4px; height: 4px;
  background: var(--coral);
  border-radius: 50%;
  display: inline-block;
}

/* ── Streamlit input overrides ── */
.stTextInput > div > div > input {
  background: var(--mist) !important;
  border: 1px solid var(--line) !important;
  border-radius: 3px !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 1rem !important;
  color: var(--ink) !important;
  padding: 0.75rem 1rem !important;
  box-shadow: none !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--coral) !important;
  box-shadow: 0 0 0 3px rgba(204,85,0,0.08) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--ghost) !important; }

/* ── Buttons ── */
.stButton > button {
  font-family: 'Geist Mono', monospace !important;
  font-size: 0.72rem !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  border-radius: 3px !important;
  border: 1px solid var(--line) !important;
  background: white !important;
  color: var(--dusk) !important;
  padding: 0.5rem 1rem !important;
  transition: all 0.15s ease !important;
  box-shadow: none !important;
}
.stButton > button:hover {
  border-color: var(--coral) !important;
  color: var(--coral) !important;
  background: rgba(204,85,0,0.04) !important;
}
.stButton > button[kind="primary"] {
  background: var(--ink) !important;
  color: var(--clay) !important;
  border-color: var(--ink) !important;
  font-weight: 500 !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--dusk) !important;
  color: var(--coral) !important;
  border-color: var(--dusk) !important;
}

/* ── Agent Pipeline Panel ── */
.pipeline-panel {
  background: var(--ink);
  border-radius: 4px;
  padding: 1.75rem;
  margin: 1.5rem 0;
  color: var(--clay);
  font-family: 'Geist Mono', monospace;
}
.pipeline-title {
  font-size: 0.65rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--ghost);
  margin-bottom: 1.25rem;
}
.agent-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 0.82rem;
}
.agent-row:last-child { border-bottom: none; }
.agent-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-waiting { background: #3a3733; border: 1px solid #4a4743; }
.dot-running { background: var(--coral); animation: pulse-dot 1s infinite; }
.dot-done    { background: #4ade80; }
.agent-name  { color: #c8c0b4; flex: 1; }
.agent-status-text { color: var(--ghost); font-size: 0.72rem; }
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.8); }
}

/* ── Progress bar override ── */
.stProgress > div > div > div > div {
  background: var(--coral) !important;
  border-radius: 1px !important;
}
.stProgress > div > div > div {
  background: var(--line) !important;
  border-radius: 1px !important;
  height: 2px !important;
}

/* ── Result card ── */
.result-card {
  background: white;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2rem;
  margin: 1.5rem 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.result-meta {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--line);
}
.meta-item {
  font-family: 'Geist Mono', monospace;
  font-size: 0.7rem;
}
.meta-label { color: var(--ghost); letter-spacing: 1px; text-transform: uppercase; }
.meta-value { color: var(--ink); font-size: 0.85rem; margin-top: 2px; font-weight: 500; }

/* ── Content render ── */
.stMarkdown p {
  font-family: 'Geist', sans-serif !important;
  font-size: 0.95rem !important;
  line-height: 1.75 !important;
  color: var(--dusk) !important;
}
.stMarkdown h1 {
  font-family: 'Instrument Serif', serif !important;
  font-size: 1.8rem !important;
  color: var(--ink) !important;
  margin: 1.5rem 0 0.75rem !important;
}
.stMarkdown h2 {
  font-family: 'Instrument Serif', serif !important;
  font-size: 1.3rem !important;
  color: var(--ink) !important;
  margin: 1.25rem 0 0.5rem !important;
}

/* ── Export strip ── */
.export-strip {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--mist);
  border: 1px solid var(--line);
  border-radius: 3px;
  margin-top: 1rem;
}
.export-label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ghost);
  flex-shrink: 0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--ink) !important;
  border-right: none !important;
}
section[data-testid="stSidebar"] * {
  color: var(--clay) !important;
}
.sidebar-section {
  padding: 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-family: 'Geist Mono', monospace;
}
.sidebar-heading {
  font-size: 0.6rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--ghost) !important;
  margin-bottom: 0.75rem;
}
.sidebar-item {
  font-size: 0.78rem;
  color: #a09890 !important;
  padding: 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sidebar-stat {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  padding: 5px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.sidebar-stat-val { color: var(--coral) !important; font-weight: 500; }

/* ── Example chips ── */
.stButton > button.example-btn {
  font-size: 0.7rem !important;
  padding: 0.35rem 0.75rem !important;
  background: var(--mist) !important;
  color: var(--ghost) !important;
}

/* ── Alert overrides ── */
.stAlert {
  border-radius: 3px !important;
  border: 1px solid var(--line) !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 0.88rem !important;
}

/* ── Image captions ── */
.stImage > div > p {
  font-family: 'Geist Mono', monospace !important;
  font-size: 0.68rem !important;
  color: var(--ghost) !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
}

/* ── Download buttons ── */
.stDownloadButton > button {
  font-family: 'Geist Mono', monospace !important;
  font-size: 0.7rem !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  background: var(--ink) !important;
  color: var(--clay) !important;
  border: 1px solid var(--ink) !important;
  border-radius: 3px !important;
  width: 100% !important;
}
.stDownloadButton > button:hover {
  background: var(--coral) !important;
  border-color: var(--coral) !important;
}

/* ── Spinner ── */
.stSpinner > div {
  border-top-color: var(--coral) !important;
}

/* ── Divider ── */
hr { border-color: var(--line) !important; }
</style>
""", unsafe_allow_html=True)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Auth helpers ───────────────────────────────────────────────

def _auth_headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _show_auth_page():
    """Full-screen login / register page in ARIA style."""
    st.markdown("""
    <div style="max-width:420px;margin:4rem auto 0;">
      <div style="text-align:center;margin-bottom:2.5rem;">
        <div style="font-family:'Instrument Serif',serif;font-size:3rem;
                    color:var(--ink);letter-spacing:-1px;line-height:1;">
          AR<span style="color:var(--coral);">I</span>A
        </div>
        <div style="font-family:'Geist Mono',monospace;font-size:0.65rem;
                    color:var(--ghost);letter-spacing:3px;text-transform:uppercase;
                    margin-top:6px;">AI Research Intelligence Agent</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Center column
    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        # ── Login tab ─────────────────────────────────────────
        with tab_login:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            email    = st.text_input("Email",    key="login_email",    placeholder="you@example.com")
            password = st.text_input("Password", key="login_password", placeholder="••••••••", type="password")

            if st.button("Sign In", type="primary", width='stretch', key="btn_login"):
                if not email or not password:
                    st.warning("Please fill in both fields.")
                else:
                    with st.spinner("Signing in…"):
                        try:
                            r = requests.post(
                                f"{API_URL}/auth/login",
                                data={"username": email, "password": password},
                                timeout=10,
                            )
                            if r.status_code == 200:
                                data = r.json()
                                st.session_state["token"] = data["access_token"]
                                st.session_state["user"]  = data["user"]
                                st.rerun()
                            else:
                                try:
                                    detail = r.json().get("detail", "Login failed")
                                except Exception:
                                    detail = f"Login failed (HTTP {r.status_code}) — check the API logs"
                                st.error(f"✗ {detail}")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot reach API. Make sure the backend is running.")

        # ── Register tab ───────────────────────────────────────
        with tab_register:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            reg_name     = st.text_input("Full Name (optional)", key="reg_name",     placeholder="Jane Doe")
            reg_email    = st.text_input("Email",                key="reg_email",    placeholder="you@example.com")
            reg_password = st.text_input("Password (min 8 chars)", key="reg_password", placeholder="••••••••", type="password")
            reg_confirm  = st.text_input("Confirm Password",     key="reg_confirm",  placeholder="••••••••", type="password")

            if st.button("Create Account", type="primary", width='stretch', key="btn_register"):
                if not reg_email or not reg_password:
                    st.warning("Email and password are required.")
                elif len(reg_password) < 8:
                    st.warning("Password must be at least 8 characters.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating account…"):
                        try:
                            r = requests.post(
                                f"{API_URL}/auth/register",
                                json={"email": reg_email, "password": reg_password,
                                      "full_name": reg_name},
                                timeout=10,
                            )
                            if r.status_code == 201:
                                data = r.json()
                                st.session_state["token"] = data["access_token"]
                                st.session_state["user"]  = data["user"]
                                st.success("Account created! Welcome to ARIA.")
                                st.rerun()
                            else:
                                try:
                                    detail = r.json().get("detail", "Registration failed")
                                except Exception:
                                    detail = r.text or "Registration failed"
                                st.error(f"✗ {detail}")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot reach API. Make sure the backend is running.")


# ── Guard — show login if not authenticated ────────────────────
if "token" not in st.session_state or not st.session_state.get("token"):
    _show_auth_page()
    st.stop()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="aria-header">
  <div>
    <div class="aria-wordmark">AR<span>I</span>A</div>
    <div class="aria-tagline">AI Research Intelligence Agent · Powered by Claude</div>
  </div>
  <div class="aria-badge">◈ Multi-Agent System v2.0</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    # ── User info + logout ─────────────────────────────────────
    user      = st.session_state.get("user", {})
    user_name = user.get("full_name") or user.get("email", "User")
    st.markdown(f"""
    <div class="sidebar-section">
      <div class="sidebar-heading">Signed In As</div>
      <div class="sidebar-item" style="color:#c8c0b4 !important;font-size:0.82rem;">
        {user_name}
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sign Out", width='stretch', key="btn_signout"):
        for k in ["token", "user", "result", "topic_used", "elapsed",
                  "pdf_bytes", "docx_bytes", "history_post"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("""
    <div class="sidebar-section">
      <div class="sidebar-heading">Active Agents</div>
      <div class="sidebar-item">◎ &nbsp;Orchestrator</div>
      <div class="sidebar-item">◉ &nbsp;Research Agent</div>
      <div class="sidebar-item">◉ &nbsp;Writer Agent</div>
      <div class="sidebar-item">◉ &nbsp;Image Agent</div>
      <div class="sidebar-item">◉ &nbsp;Export Agent</div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-heading">Cost per Run</div>
      <div class="sidebar-stat"><span>GPT-4o mini</span><span class="sidebar-stat-val">~$0.01</span></div>
      <div class="sidebar-stat"><span>GPT Image 2 × 3</span><span class="sidebar-stat-val">~$0.015</span></div>
      <div class="sidebar-stat"><span>Web Search</span><span class="sidebar-stat-val">built-in</span></div>
      <div class="sidebar-stat"><span><strong>Total</strong></span><span class="sidebar-stat-val">~$0.03</span></div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-heading">API Status</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        h = requests.get(f"{API_URL}/health", timeout=3)
        if h.status_code == 200:
            st.success("● API Online")
        else:
            st.error("● API Error")
    except:
        st.error("● API Offline — run uvicorn")

    # ── ChromaDB Memory Stats ──────────────────────────────────
    try:
        stats_res = requests.get(f"{API_URL}/memory/stats", timeout=3)
        if stats_res.status_code == 200:
            s = stats_res.json()
            st.markdown(f"""
            <div class="sidebar-section">
              <div class="sidebar-heading">Memory (ChromaDB)</div>
              <div class="sidebar-stat">
                <span>Blog Posts Saved</span>
                <span class="sidebar-stat-val">{s.get('blog_posts_saved', 0)}</span>
              </div>
              <div class="sidebar-stat">
                <span>Topics Tracked</span>
                <span class="sidebar-stat-val">{s.get('topics_tracked', 0)}</span>
              </div>
              <div class="sidebar-stat">
                <span>Doc Chunks</span>
                <span class="sidebar-stat-val">{s.get('document_chunks', 0)}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass

    # ── Favourite Topics ───────────────────────────────────────
    try:
        fav_res = requests.get(f"{API_URL}/memory/topics?n=5", timeout=3)
        if fav_res.status_code == 200:
            favs = fav_res.json().get("topics", [])
            if favs:
                items_html = "".join(
                    f'<div class="sidebar-stat">'
                    f'<span style="font-size:0.75rem">{t["topic"][:22]}</span>'
                    f'<span class="sidebar-stat-val">×{t["count"]}</span>'
                    f'</div>'
                    for t in favs
                )
                st.markdown(f"""
                <div class="sidebar-section">
                  <div class="sidebar-heading">Favourite Topics</div>
                  {items_html}
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown("""
    <div class="sidebar-section" style="margin-top:auto;">
      <div class="sidebar-heading">Stack</div>
      <div class="sidebar-item">CrewAI 1.x · LangChain 1.x</div>
      <div class="sidebar-item">OpenAI 2.x · FastAPI</div>
      <div class="sidebar-item">Streamlit · SupabaseDB</div>
    </div>
    """, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
for _k, _v in [("result", None), ("topic_used", ""), ("elapsed", 0.0),
               ("pdf_bytes", None), ("docx_bytes", None), ("history_post", None)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _pipeline_html(stage: str) -> str:
    agents = {
        "research": [
            ("done",    "Orchestrator",   "Delegating tasks →"),
            ("running", "Research Agent", "Searching the web…"),
            ("waiting", "Writer Agent",   "Waiting for research…"),
            ("waiting", "Image Agent",    "Queued"),
            ("waiting", "Export Agent",   "Queued"),
        ],
        "writing": [
            ("done",    "Orchestrator",   "Delegating tasks →"),
            ("done",    "Research Agent", "Research complete ✓"),
            ("running", "Writer Agent",   "Writing blog post…"),
            ("waiting", "Image Agent",    "Queued"),
            ("waiting", "Export Agent",   "Queued"),
        ],
        "images": [
            ("done",    "Orchestrator",   "Delegating tasks →"),
            ("done",    "Research Agent", "Research complete ✓"),
            ("done",    "Writer Agent",   "Blog post written ✓"),
            ("running", "Image Agent",    "Generating images…"),
            ("waiting", "Export Agent",   "Queued"),
        ],
        "done": [
            ("done", "Orchestrator",   "Complete ✓"),
            ("done", "Research Agent", "Research complete ✓"),
            ("done", "Writer Agent",   "Blog post written ✓"),
            ("done", "Image Agent",    "Images generated ✓"),
            ("done", "Export Agent",   "Ready to export ✓"),
        ],
    }
    rows = "".join(
        f'<div class="agent-row">'
        f'<div class="agent-dot dot-{dot}"></div>'
        f'<span class="agent-name">{name}</span>'
        f'<span class="agent-status-text">{text}</span>'
        f'</div>'
        for dot, name, text in agents[stage]
    )
    running = stage != "done"
    title = f"Agent Pipeline · {'Running' if running else 'Complete'}"
    return f'<div class="pipeline-panel"><div class="pipeline-title">{title}</div>{rows}</div>'


# ── Main Tabs ─────────────────────────────────────────────────
tab_research, tab_history = st.tabs(["New Research", "My History"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — New Research
# ══════════════════════════════════════════════════════════════
with tab_research:

    # ── Input Zone ────────────────────────────────────────────
    st.markdown('<div class="input-zone">', unsafe_allow_html=True)
    st.markdown('<div class="zone-label">Research Topic</div>', unsafe_allow_html=True)

    topic = st.text_input(
        "topic",
        placeholder="e.g.  Future of AI in Healthcare  ·  Quantum Computing  ·  Climate Tech",
        label_visibility="collapsed",
        key="topic_input",
    )

    c1, c2, c3, c4, c5 = st.columns([2,2,2,2,2])
    examples = {
        c1: "🏥 AI Healthcare",
        c2: "🌍 Climate Tech",
        c3: "🔗 Blockchain",
        c4: "🚀 Space Exploration",
        c5: "🧬 Biotechnology",
    }
    def _pick_example(text):
        st.session_state["topic_input"] = text

    for col, label in examples.items():
        col.button(
            label,
            width='stretch',
            on_click=_pick_example,
            args=(label.split(" ", 1)[1],),
        )

    st.markdown("</div>", unsafe_allow_html=True)

    _, btn_col, _ = st.columns([3, 2, 3])
    with btn_col:
        generate = st.button("◈  Run Agent Pipeline", type="primary", width='stretch')

    # ── Document Upload Zone ───────────────────────────────────
    with st.expander("📂  Add documents to research base (optional)", expanded=False):
        st.caption("Upload .txt, .md, or .pdf files — agents will use this as extra context during research.")
        doc_col1, doc_col2 = st.columns([1, 1])

        with doc_col1:
            uploaded_file = st.file_uploader(
                "Upload .txt, .md, or .pdf file",
                type=["txt", "md", "pdf"],
                label_visibility="collapsed",
            )
            if uploaded_file:
                # Extract text based on file type
                if uploaded_file.name.lower().endswith(".pdf"):
                    try:
                        from pypdf import PdfReader
                        import io
                        pdf_bytes = uploaded_file.read()
                        reader = PdfReader(io.BytesIO(pdf_bytes))
                        pages_text = []
                        for page in reader.pages:
                            extracted = page.extract_text()
                            if extracted:
                                pages_text.append(extracted)
                        doc_text = "\n\n".join(pages_text)
                        if not doc_text.strip():
                            st.warning("Could not extract text from this PDF (it may be a scanned image). Try a text-based PDF.")
                            doc_text = None
                        else:
                            st.caption(f"✓ Extracted {len(reader.pages)} pages · {len(doc_text.split())} words")
                    except Exception as pdf_err:
                        st.error(f"PDF read error: {pdf_err}")
                        doc_text = None
                else:
                    doc_text = uploaded_file.read().decode("utf-8", errors="replace")

                if doc_text and st.button(f"Add '{uploaded_file.name}' to base", width='stretch'):
                    with st.spinner("Adding to document base…"):
                        r = requests.post(f"{API_URL}/memory/documents", json={
                            "text": doc_text,
                            "source": uploaded_file.name,
                        }, timeout=30)
                    if r.status_code == 200:
                        d = r.json()
                        st.success(f"✓ Added {d['chunks_created']} chunks from '{d['source']}'")
                    else:
                        st.error(f"Failed: {r.text}")

        with doc_col2:
            paste_text = st.text_area("Or paste text directly", height=100, label_visibility="collapsed",
                                      placeholder="Paste any article, report, or notes here…")
            paste_label = st.text_input("Source label", value="pasted_content", label_visibility="collapsed")
            if st.button("Add pasted text to base", width='stretch'):
                if paste_text and len(paste_text.strip()) >= 50:
                    with st.spinner("Adding to document base…"):
                        r = requests.post(f"{API_URL}/memory/documents", json={
                            "text": paste_text,
                            "source": paste_label or "pasted_content",
                        }, timeout=30)
                    if r.status_code == 200:
                        d = r.json()
                        st.success(f"✓ Added {d['chunks_created']} chunks from '{d['source']}'")
                    else:
                        st.error(f"Failed: {r.text}")
                else:
                    st.warning("Please paste at least 50 characters.")

    # ── Pipeline Execution ────────────────────────────────────
    if generate and topic:
        st.session_state.result     = None
        st.session_state.pdf_bytes  = None
        st.session_state.docx_bytes = None

        pipeline_slot = st.empty()
        progress      = st.progress(0)
        status        = st.empty()

        pipeline_slot.markdown(_pipeline_html("research"), unsafe_allow_html=True)
        progress.progress(5)
        status.caption("◎  Orchestrator is initialising the pipeline…")

        _stage_cfg = {
            "research": (10,  "research", "◎  Research Agent is querying the web…"),
            "writing":  (45,  "writing",  "◎  Writer Agent is drafting the blog post…"),
            "images":   (70,  "images",   "◎  Image Agent is generating visuals…"),
        }

        try:
            start  = time.time()
            result = None

            with requests.get(
                f"{API_URL}/research/stream",
                params={"topic": topic},
                headers=_auth_headers(),
                stream=True,
                timeout=300,
            ) as resp:
                if resp.status_code == 401:
                    st.warning("Session expired. Please sign in again.")
                    st.session_state.pop("token", None)
                    st.session_state.pop("user", None)
                    st.rerun()
                if resp.status_code != 200:
                    st.error(f"Pipeline error: {resp.text}")
                    st.stop()

                for raw in resp.iter_lines():
                    if not raw:
                        continue
                    if isinstance(raw, bytes):
                        raw = raw.decode()
                    if not raw.startswith("data: "):
                        continue
                    event = json.loads(raw[6:])
                    stage = event.get("stage")

                    if stage in _stage_cfg:
                        pct, panel, caption = _stage_cfg[stage]
                        pipeline_slot.markdown(_pipeline_html(panel), unsafe_allow_html=True)
                        progress.progress(pct)
                        status.caption(caption)

                    elif stage == "done":
                        result = event.get("result")

                    elif stage == "error":
                        st.error(f"Pipeline error: {event.get('msg')}")
                        st.stop()

            elapsed = round(time.time() - start, 1)

            pipeline_slot.markdown(_pipeline_html("done"), unsafe_allow_html=True)
            progress.progress(100)
            status.caption(
                f"✓  Complete in {elapsed}s  ·  "
                f"{result.get('word_count','—')} words  ·  "
                f"{len(result.get('images', []))} images"
            )

            st.session_state.result     = result
            st.session_state.topic_used = topic
            st.session_state.elapsed    = elapsed

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to FastAPI backend.\n\nRun: `uvicorn api.main:app --reload --port 8000`")
            st.stop()
        except requests.exceptions.Timeout:
            st.warning("The agents are still working — this can take 60–90 seconds on first run.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

    elif generate and not topic:
        st.warning("Please enter a topic before running the pipeline.")

    # ── Results ───────────────────────────────────────────────
    if st.session_state.result:
        result    = st.session_state.result
        content   = result.get("content", "")
        images    = result.get("images", [])
        topic     = st.session_state.topic_used
        elapsed   = st.session_state.elapsed
        cover_url = images[0]["url"] if images else ""

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="result-meta">
          <div class="meta-item">
            <div class="meta-label">Topic</div>
            <div class="meta-value">{topic}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Words</div>
            <div class="meta-value">{result.get('word_count','—')}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Images</div>
            <div class="meta-value">{len(images)}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Time</div>
            <div class="meta-value">{elapsed}s</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Est. Cost</div>
            <div class="meta-value">~$0.03</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if images:
            img_col, txt_col = st.columns([1, 2])
            with img_col:
                for img in images:
                    st.image(img["url"], caption=img.get("label", ""), width='stretch')
            with txt_col:
                st.markdown(content)
        else:
            st.markdown(content)

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Similar Past Posts ─────────────────────────────────
        similar = result.get("similar_posts", [])
        if similar:
            st.markdown("---")
            st.markdown('<div class="zone-label">Similar Past Posts</div>', unsafe_allow_html=True)
            sim_cols = st.columns(len(similar))
            for col, post in zip(sim_cols, similar):
                with col:
                    st.markdown(f"""
                    <div style="background:white;border:1px solid var(--line);border-radius:4px;
                                padding:1rem;font-family:'Geist',sans-serif;">
                      <div style="font-family:'Geist Mono',monospace;font-size:0.65rem;
                                  color:var(--ghost);letter-spacing:2px;text-transform:uppercase;
                                  margin-bottom:6px;">Past Post</div>
                      <div style="font-weight:600;font-size:0.9rem;color:var(--ink);
                                  margin-bottom:8px;">{post['topic']}</div>
                      <div style="font-size:0.78rem;color:var(--ghost);margin-bottom:8px;
                                  line-height:1.5;">{post['content_preview'][:150]}…</div>
                      <div style="font-family:'Geist Mono',monospace;font-size:0.65rem;
                                  color:var(--coral);">{post['word_count']} words · {post['created_at'][:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Export ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="zone-label">Export</div>', unsafe_allow_html=True)

        ex1, ex2, ex3 = st.columns(3)

        with ex1:
            if st.session_state.pdf_bytes:
                st.download_button(
                    "◎  Save PDF",
                    st.session_state.pdf_bytes,
                    f"{topic[:25].replace(' ', '_')}.pdf",
                    "application/pdf",
                    width='stretch',
                    key="dl_pdf",
                )
            else:
                if st.button("⬇  Export as PDF", width='stretch', key="btn_pdf"):
                    with st.spinner("Building PDF…"):
                        r = requests.post(f"{API_URL}/export", json={
                            "topic": topic, "content": content,
                            "image_url": cover_url, "format": "pdf",
                        }, timeout=60)
                    if r.status_code == 200:
                        st.session_state.pdf_bytes = r.content
                        st.rerun()
                    else:
                        st.error(f"PDF export failed: {r.text}")

        with ex2:
            if st.session_state.docx_bytes:
                st.download_button(
                    "◎  Save Word",
                    st.session_state.docx_bytes,
                    f"{topic[:25].replace(' ', '_')}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width='stretch',
                    key="dl_docx",
                )
            else:
                if st.button("⬇  Export as Word", width='stretch', key="btn_word"):
                    with st.spinner("Building Word doc…"):
                        r = requests.post(f"{API_URL}/export", json={
                            "topic": topic, "content": content,
                            "image_url": cover_url, "format": "word",
                        }, timeout=60)
                    if r.status_code == 200:
                        st.session_state.docx_bytes = r.content
                        st.rerun()
                    else:
                        st.error(f"Word export failed: {r.text}")

        with ex3:
            st.download_button(
                "◎  Save Plain Text",
                content,
                f"{topic[:25].replace(' ', '_')}.txt",
                "text/plain",
                width='stretch',
                key="dl_txt",
            )

# ══════════════════════════════════════════════════════════════
# TAB 2 — My History
# ══════════════════════════════════════════════════════════════
with tab_history:
    st.markdown('<div class="zone-label">Your Research History</div>', unsafe_allow_html=True)

    if st.button("↺  Refresh", key="btn_refresh_history"):
        st.session_state["history_post"] = None
        st.rerun()

    try:
        hist_resp = requests.get(
            f"{API_URL}/history",
            headers=_auth_headers(),
            timeout=30,          # increased: first DB connection can be slow
        )
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach API — make sure `uvicorn api.main:app` is running.")
        hist_resp = None
    except requests.exceptions.ReadTimeout:
        st.warning("History request timed out. Check your DATABASE_URL in .env — "
                   "Supabase needs port **6543** (Session pooler), not 5432.")
        hist_resp = None

    if hist_resp is not None and hist_resp.status_code == 401:
        st.warning("Session expired. Please sign in again.")
        st.session_state.pop("token", None)
        st.rerun()
    elif hist_resp is not None and hist_resp.status_code == 503:
        st.warning("Database unavailable. Check DATABASE_URL in .env")
    elif hist_resp is not None and hist_resp.status_code == 200:
        hist_posts = hist_resp.json()
        if not hist_posts:
            st.info("No research history yet. Run your first research in the New Research tab!")
        else:
            for hp_summary in hist_posts:
                h_col_text, h_col_btn = st.columns([5, 1])
                with h_col_text:
                    st.markdown(f"""
                    <div style="background:white;border:1px solid var(--line);
                                border-radius:4px;padding:1rem;margin-bottom:0.5rem;">
                      <div style="font-family:'Geist Mono',monospace;font-size:0.65rem;
                                  color:var(--ghost);letter-spacing:2px;text-transform:uppercase;">
                        {hp_summary['created_at'][:10]}
                      </div>
                      <div style="font-family:'Instrument Serif',serif;font-size:1.1rem;
                                  color:var(--ink);margin:4px 0;">
                        {hp_summary['topic']}
                      </div>
                      <div style="font-family:'Geist Mono',monospace;font-size:0.7rem;
                                  color:var(--ghost);">
                        {hp_summary['word_count']} words · {hp_summary['image_count']} images
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with h_col_btn:
                    if st.button("Read", key=f"hist_{hp_summary['id']}"):
                        r2 = requests.get(
                            f"{API_URL}/history/{hp_summary['id']}",
                            headers=_auth_headers(),
                            timeout=10,
                        )
                        if r2.status_code == 200:
                            st.session_state["history_post"] = r2.json()
                        else:
                            st.error(f"Could not load article: {r2.text}")

            # ── Full article viewer ────────────────────────────
            if st.session_state.get("history_post"):
                hp = st.session_state["history_post"]
                st.markdown("---")
                st.markdown(f"""
                <div class="result-card">
                  <div style="font-family:'Geist Mono',monospace;font-size:0.65rem;
                              color:var(--ghost);letter-spacing:2px;text-transform:uppercase;
                              margin-bottom:0.5rem;">{hp['created_at'][:10]} · {hp['word_count']} words</div>
                </div>
                """, unsafe_allow_html=True)

                h_images = hp.get("images", [])
                if h_images:
                    h_img_col, h_txt_col = st.columns([1, 2])
                    with h_img_col:
                        for img in h_images:
                            st.image(img["url"], caption=img.get("label", ""),
                                     width='stretch')
                    with h_txt_col:
                        st.markdown(hp["content"])
                else:
                    st.markdown(hp["content"])

                if st.button("✕  Close Article", key="btn_close_hist"):
                    st.session_state["history_post"] = None
                    st.rerun()
    elif hist_resp is not None:
        st.error(f"Could not load history: {hist_resp.text}")
