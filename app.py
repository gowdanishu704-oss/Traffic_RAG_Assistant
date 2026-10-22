"""Traffic Law & Challan Assistant: Pixel-perfect UI matching the design screens.

    streamlit run app.py

Pages: Ask, Quick Guides, Fine Lookup, About.
"""

import base64
import html
import os
from pathlib import Path

import pandas as pd
import streamlit as st

import rag
import scan
from eval import TESTS, run_tests

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="Traffic Law & Challan Assistant",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Colors
BLUE, GREEN, RED, PURPLE = "#1F5FE0", "#1F9D55", "#E5484D", "#7C3AED"
ORANGE, TEAL, PINK, AMBER = "#F2711C", "#0E9F9A", "#D6336C", "#E6A700"

# (material icon, colour, tint, question)
EXAMPLES = [
    ("sports_motorsports", BLUE, "#E6EEFF", "What is the fine for not wearing a helmet?"),
    ("description", GREEN, "#E6F6EC", "How to renew my driving licence?"),
    ("directions_car", RED, "#FDEBEC", "What to do after an accident?"),
    ("receipt_long", PURPLE, "#F1EAFE", "How to pay an e-challant?"),
]

# (material icon, colour, card tint, title, description, preset question)
GUIDES = [
    ("car_crash", RED, "#FFF3F3", "After an Accident",
     "What to do, Good Samaritan protection, hospital duties",
     "What should I do after a road accident, and what protection does a Good Samaritan get?"),
    ("badge", GREEN, "#F0FAF4", "Renew My Licence",
     "Validity, renewal window, documents required",
     "How do I renew my driving licence, when can I apply, and what documents do I need?"),
    ("receipt_long", BLUE, "#F0F5FF", "E-Challan Process",
     "How to pay, contest, virtual court, unpaid challans",
     "How do I pay an e-challan, how long do I have, and what happens if I do not pay?"),
    ("menu_book", PURPLE, "#F6F1FF", "Traffic Rules & Fines",
     "Common offences and penalties under the 2019 Act", None),
    ("sports_motorsports", ORANGE, "#FFF6EE", "Helmet & Safety Gear",
     "Rules, fines and requirements",
     "What are the helmet rules for two-wheeler riders, and what is the fine for not wearing a helmet or for triple riding?"),
    ("airline_seat_recline_normal", TEAL, "#EEFAF9", "Seat Belt Rules",
     "When required and penalties",
     "When is a seat belt required, what are the rules for children, and what is the fine?"),
    ("wine_bar", PINK, "#FFF1F5", "Drunken Driving",
     "Fines under Section 185 and legal limits",
     "What is the penalty for drunk driving under Section 185, and what is the legal alcohol limit?"),
    ("no_crash", AMBER, "#FFFAEB", "Driving without Licence",
     "Penalties and consequences",
     "What is the penalty for driving without a licence, and what happens if the owner lets an unlicensed person or a minor drive?"),
]

# Central-law amounts exactly matching the design screen table
FINES = [
    ("Not wearing helmet", "194D", "1,000", "3 months licence disqualification"),
    ("Drunken driving", "185", "10,000", "(old penalty ₹2,000)"),
    ("Driving without licence", "181", "5,000", "May be higher for repeat offence"),
    ("Without insurance", "196", "2,000", "/"),
    ("Using mobile phone while driving", "184", "1,000", "/"),
    ("Not wearing seat belt", "194B", "1,000", "/"),
    ("Overspeeding (light motor vehicle)", "183", "1,000 – 2,000", "Licence impounded on repeat"),
    ("Racing or speed trials", "189", "5,000", "Repeat: ₹10,000 and/or 1 year"),
    ("Not giving way to emergency vehicles", "194E", "10,000", "And/or up to 6 months' jail"),
    ("Two-wheeler with more than one pillion", "194C", "1,000", "3 months licence disqualification"),
]

ABOUT_CARDS = [
    ("menu_book", PURPLE, "#F1EAFE", "Knowledge Base",
     "4 documents, ~37 chunks from trusted web sources"),
    ("database", GREEN, "#E6F6EC", "Retrieval Method",
     "Hybrid search: BM25 + FAISS with embeddings"),
    ("verified_user", ORANGE, "#FFEFE3", "Answerability Check",
     "Only answers when documents cover the question"),
    ("format_quote", BLUE, "#E6EEFF", "Cited Sources",
     "Shows exact passages with file and section"),
]

ABOUT_STEPS = [
    ("description", BLUE, "#E6EEFF", "1. Ingest", "Split by heading"),
    ("search", GREEN, "#E6F6EC", "2. Retrieve", "BM25 + FAISS"),
    ("check_box", ORANGE, "#FFEFE3", "3. Check Coverage", "Call LLM only if covered"),
    ("article", PURPLE, "#F1EAFE", "4. Generate & Cite", "Answer with sources"),
]

# Cache RAG Index
@st.cache_resource
def get_index() -> rag.BM25Index:
    return rag.BM25Index(rag.load_chunks())

@st.cache_data
def hero_b64() -> str:
    data = (ASSETS / "hero.jpg").read_bytes()
    return base64.b64encode(data).decode()

def api_key() -> str | None:
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")

# Session state setup
if "page" not in st.session_state:
    st.session_state.page = "ask"
if "states" not in st.session_state:
    st.session_state.states = ["Tamil Nadu"]
if "q_input" not in st.session_state:
    st.session_state.q_input = ""

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0" />

<style>
/* Reset & Fonts */
html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
}
.stApp {
  background-color: #F5F8FC !important;
}

/* Hide Streamlit Default Header and Chrome */
header[data-testid="stHeader"] {
  display: none !important;
}
footer {
  display: none !important;
}
[data-testid="stSidebar"] {
  display: none !important;
}
[data-testid="collapsedControl"] {
  display: none !important;
}

/* Main Container Max-Width & Padding */
[data-testid="stMainBlockContainer"] {
  max-width: 1220px !important;
  padding-top: 1.2rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  padding-bottom: 4rem !important;
}

/* Custom Top Navbar */
.top-navbar-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0 20px;
  border-bottom: 1px solid rgba(227, 234, 245, 0.8);
  margin-bottom: 24px;
}

.brand-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.traffic-light-pill {
  width: 22px;
  height: 46px;
  background: #111827;
  border-radius: 11px;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  align-items: center;
  padding: 3px 0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.25);
}

.light-bulb {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}
.light-red { background: #EF4444; box-shadow: 0 0 5px #EF4444; }
.light-yellow { background: #F59E0B; box-shadow: 0 0 5px #F59E0B; }
.light-green { background: #10B981; box-shadow: 0 0 6px #10B981; }

.brand-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: #14213D;
  letter-spacing: -0.02em;
}

/* Nav Button States */
div[data-testid*="nav_"] button {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  padding: 0.4rem 0.9rem !important;
  transition: all 0.18s ease !important;
}

/* Active Nav Tab */
.st-key-nav_active_btn button {
  background-color: #1F5FE0 !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  box-shadow: 0 2px 10px rgba(31, 95, 224, 0.3) !important;
}
.st-key-nav_active_btn button p,
.st-key-nav_active_btn button span {
  color: #FFFFFF !important;
  font-weight: 700 !important;
}

/* Inactive Nav Tab */
.st-key-btn_nav_ask button,
.st-key-btn_nav_guides button,
.st-key-btn_nav_fines button,
.st-key-btn_nav_pdf button,
.st-key-btn_nav_about button {
  background: transparent !important;
  color: #33415C !important;
  border: none !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
.st-key-btn_nav_ask button:hover,
.st-key-btn_nav_guides button:hover,
.st-key-btn_nav_fines button:hover,
.st-key-btn_nav_pdf button:hover,
.st-key-btn_nav_about button:hover {
  background: #E8EEF8 !important;
  color: #14213D !important;
}

/* Secondary PDF button inside Ask card */
.st-key-btn_goto_pdf button {
  background-color: #FFFFFF !important;
  color: #1F5FE0 !important;
  border: 1px solid #C9D9FF !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 0.6rem 1.6rem !important;
  box-shadow: 0 1px 4px rgba(20,40,80,0.04) !important;
}
.st-key-btn_goto_pdf button:hover {
  background-color: #F0F5FF !important;
  border-color: #1F5FE0 !important;
}

/* States Popover Button */
div[data-testid="stPopover"] button {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 8px !important;
  color: #14213D !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  padding: 0.35rem 0.85rem !important;
  box-shadow: 0 1px 4px rgba(20,40,80,0.04) !important;
}

/* Hero Typography */
.eyebrow-badge {
  color: #1F5FE0;
  font-weight: 700;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.hero-head {
  font-size: 3.1rem;
  font-weight: 800;
  line-height: 1.1;
  color: #14213D;
  letter-spacing: -0.03em;
  margin-bottom: 12px;
}
.hero-blue {
  color: #1F5FE0;
}
.hero-desc {
  font-size: 1.05rem;
  line-height: 1.5;
  color: #33415C;
  max-width: 600px;
  margin-bottom: 22px;
}

/* Ask Card */
.st-key-card_ask_wrap {
  background: #FFFFFF;
  border: 1px solid #E3EAF5;
  border-radius: 16px;
  padding: 1.4rem 1.6rem 1.6rem;
  box-shadow: 0 4px 18px rgba(20, 40, 80, 0.05);
  margin-bottom: 22px;
}

/* Text Input Styling inside Ask Card */
[data-testid="stTextInput"] input {
  background-color: #FFFFFF !important;
  border: 1px solid #D9E2EC !important;
  border-radius: 10px !important;
  font-size: 0.92rem !important;
  color: #14213D !important;
  padding: 0.55rem 0.9rem !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: #1F5FE0 !important;
  box-shadow: 0 0 0 3px rgba(31, 95, 224, 0.12) !important;
}

/* Submit Button Get Answer */
.st-key-btn_get_answer button,
.st-key-btn_fine_search button {
  background-color: #1F5FE0 !important;
  color: #FFFFFF !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 0.6rem 2.8rem !important;
  border: none !important;
  box-shadow: 0 2px 10px rgba(31, 95, 224, 0.28) !important;
}
.st-key-btn_get_answer button:hover,
.st-key-btn_fine_search button:hover {
  background-color: #184cc0 !important;
  transform: translateY(-1px);
}
.st-key-btn_get_answer button p,
.st-key-btn_get_answer button span,
.st-key-btn_fine_search button p,
.st-key-btn_fine_search button span {
  color: #FFFFFF !important;
  font-weight: 700 !important;
}

/* Examples Grid */
[class*="st-key-ex_btn_"] button {
  background: #FFFFFF !important;
  border: 1px solid #E3EAF5 !important;
  border-radius: 12px !important;
  height: 4.4rem !important;
  text-align: left !important;
  box-shadow: 0 2px 8px rgba(20,40,80,.04) !important;
  transition: all 0.2s ease !important;
}
[class*="st-key-ex_btn_"] button:hover {
  border-color: #BDD3F5 !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 14px rgba(20,40,80,.08) !important;
}
[class*="st-key-ex_btn_"] button p {
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  color: #14213D !important;
  line-height: 1.35 !important;
}
[class*="st-key-ex_btn_"] [data-testid="stIconMaterial"] {
  font-size: 1.35rem !important;
  padding: 0.45rem !important;
  border-radius: 10px !important;
  margin-right: 0.5rem !important;
}
.st-key-ex_btn_0 [data-testid="stIconMaterial"] { background: #E6EEFF !important; color: #1F5FE0 !important; }
.st-key-ex_btn_1 [data-testid="stIconMaterial"] { background: #E6F6EC !important; color: #1F9D55 !important; }
.st-key-ex_btn_2 [data-testid="stIconMaterial"] { background: #FDEBEC !important; color: #E5484D !important; }
.st-key-ex_btn_3 [data-testid="stIconMaterial"] { background: #F1EAFE !important; color: #7C3AED !important; }

/* Showing Filter Chips */
.central-chip {
  background: #E6EEFF;
  color: #1F5FE0;
  font-weight: 700;
  border: 1px solid #C9D9FF;
  border-radius: 8px;
  padding: 0.28rem 0.85rem;
  font-size: 0.84rem;
  display: inline-block;
}
.state-chip-btn button {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 8px !important;
  color: #14213D !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  padding: 0.28rem 0.85rem !important;
}

/* Page Header Banner */
.page-header-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.circle-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #1F5FE0;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  box-shadow: 0 4px 12px rgba(31,95,224,0.25);
  flex-shrink: 0;
}
.page-head-title {
  font-size: 1.65rem;
  font-weight: 800;
  color: #14213D;
  letter-spacing: -0.02em;
  margin: 0;
}
.page-head-sub {
  font-size: 0.94rem;
  color: #64748B;
  margin: 0;
}

/* Quick Guide Cards */
[class*="st-key-guide_card_"] {
  background: #FFFFFF;
  border: 1px solid #E3EAF5;
  border-radius: 16px;
  padding: 1.4rem 1.1rem 1.1rem;
  text-align: center;
  box-shadow: 0 4px 18px rgba(20, 40, 80, 0.05);
  transition: all 0.2s ease;
}
[class*="st-key-guide_card_"]:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(20, 40, 80, 0.08);
  border-color: #BDD3F5;
}
.guide-card-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: 1.65rem;
}
.guide-card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #14213D;
  margin-bottom: 6px;
}
.guide-card-desc {
  font-size: 0.86rem;
  color: #64748B;
  min-height: 46px;
  line-height: 1.4;
  margin-bottom: 12px;
}
[class*="st-key-guide_act_"] button {
  width: 100% !important;
  background: #FFFFFF !important;
  border: 1px solid #C9D9FF !important;
  border-radius: 8px !important;
  color: #1F5FE0 !important;
  font-weight: 700 !important;
  font-size: 0.86rem !important;
}
[class*="st-key-guide_act_"] button:hover {
  background: #F0F5FF !important;
  border-color: #1F5FE0 !important;
}

/* Fines Table */
.fine-table {
  width: 100%;
  border-collapse: collapse;
  background: #FFFFFF;
  border: 1px solid #E3EAF5;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 18px rgba(20, 40, 80, 0.05);
  font-size: 0.92rem;
}
.fine-table th {
  background: #F8FAFC;
  padding: 12px 18px;
  color: #14213D;
  font-weight: 700;
  border-bottom: 1px solid #E2E8F0;
  text-align: left;
}
.fine-table td {
  padding: 13px 18px;
  border-bottom: 1px solid #F1F5F9;
  vertical-align: middle;
}
.fine-table tr:hover td {
  background: #F8FAFD;
}
.fine-table td:nth-child(1) { font-weight: 600; color: #94A3B8; }
.fine-table td:nth-child(2) { font-weight: 600; color: #14213D; }
.fine-table td:nth-child(3) { font-weight: 700; color: #1F5FE0; }
.fine-table td:nth-child(4) { font-weight: 700; color: #14213D; }

/* About Cards */
[class*="st-key-about_card_"] {
  background: #FFFFFF;
  border: 1px solid #E3EAF5;
  border-radius: 16px;
  padding: 1.4rem 1.2rem;
  box-shadow: 0 4px 18px rgba(20, 40, 80, 0.05);
}
.about-tile {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  font-size: 1.45rem;
}

/* Pipeline Step Cards */
[class*="st-key-pipe_step_"] {
  background: #FFFFFF;
  border: 1px solid #E3EAF5;
  border-radius: 14px;
  padding: 14px 14px;
  box-shadow: 0 4px 18px rgba(20, 40, 80, 0.05);
}
.step-arrow-sign {
  font-size: 1.4rem;
  color: #94A3B8;
  font-weight: bold;
  text-align: center;
  padding-top: 1.2rem;
}

/* Hero image wrapper */
.hero-img-box {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(20, 40, 80, 0.08);
  background: #FFFFFF;
}
.hero-img-box img {
  width: 100%;
  height: auto;
  display: block;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- Navigation Header
def render_navbar():
    curr = st.session_state.page
    n_states = len(st.session_state.states)

    col_brand, col_ask, col_guides, col_fines, col_pdf, col_about, col_space, col_states = st.columns(
        [3.3, 0.9, 1.4, 1.3, 1.4, 1.0, 0.2, 1.4], vertical_alignment="center"
    )

    with col_brand:
        st.markdown(
            """
            <div class="brand-wrap">
              <div class="traffic-light-pill">
                <span class="light-bulb light-red"></span>
                <span class="light-bulb light-yellow"></span>
                <span class="light-bulb light-green"></span>
              </div>
              <span class="brand-title">Traffic Law &amp; Challan Assistant</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Nav Tabs
    with col_ask:
        k = "nav_active_btn" if curr == "ask" else "btn_nav_ask"
        if st.button("⌂  Ask", key=k, use_container_width=True):
            st.session_state.page = "ask"
            st.rerun()

    with col_guides:
        k = "nav_active_btn" if curr == "guides" else "btn_nav_guides"
        if st.button("📖 Quick Guides", key=k, use_container_width=True):
            st.session_state.page = "guides"
            st.rerun()

    with col_fines:
        k = "nav_active_btn" if curr == "fines" else "btn_nav_fines"
        if st.button("🔍 Fine Lookup", key=k, use_container_width=True):
            st.session_state.page = "fines"
            st.rerun()

    with col_pdf:
        k = "nav_active_btn" if curr == "pdf" else "btn_nav_pdf"
        if st.button("📄 Upload PDF", key=k, use_container_width=True):
            st.session_state.page = "pdf"
            st.rerun()

    with col_about:
        k = "nav_active_btn" if curr == "about" else "btn_nav_about"
        if st.button("ⓘ About", key=k, use_container_width=True):
            st.session_state.page = "about"
            st.rerun()

    with col_states:
        lbl = f"States ({n_states}) ⌵" if n_states else "States ⌵"
        with st.popover(f"📖 {lbl}"):
            st.markdown("**Include State Fines for:**")
            st.multiselect(
                "States",
                rag.ALL_STATES + rag.ALL_UNION_TERRITORIES,
                default=st.session_state.states,
                key="states_multiselect",
                label_visibility="collapsed",
                on_change=lambda: st.session_state.update(states=st.session_state.states_multiselect)
            )

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- Common Page Banner
def render_page_banner(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="page-header-wrap">
          <div class="circle-icon">{icon}</div>
          <div>
            <h2 class="page-head-title">{title}</h2>
            <div class="page-head-sub">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- RAG Run Helper
def run_rag_question(q: str):
    q = (q or "").strip()
    if not q:
        return
    st.session_state.q_input = q
    with st.spinner("Searching official legal documents..."):
        try:
            res = rag.answer(q, get_index(), state=st.session_state.states, api_key=api_key())
            st.session_state.last_result = res
            st.session_state.last_question = q
        except Exception:
            st.error("Error retrieving answer. Please try again.")


# ---------------------------------------------------------------- SCREEN 1: ASK
def show_screen_ask():
    col_left, col_right = st.columns([1.75, 1], gap="large")

    with col_left:
        # Hero text
        st.markdown(
            """
            <div class="eyebrow-badge">🛡️ Your Traffic Law Assistant</div>
            <div class="hero-head">Your <span class="hero-blue">Traffic Law</span><br>Assistant</div>
            <div class="hero-desc">Clear answers on traffic fines, licence renewal, e-challans and what to do after an accident, based on official and trusted documents.</div>
            """,
            unsafe_allow_html=True,
        )

        # Search Card
        with st.container(key="card_ask_wrap"):
            c_icon, c_in, c_mic = st.columns([0.08, 0.84, 0.08], vertical_alignment="center")
            with c_icon:
                st.markdown(
                    """
                    <div style="width:32px;height:32px;border-radius:50%;background:#1F5FE0;color:#fff;display:flex;align-items:center;justify-content:center;font-size:16px;">
                      💬
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_in:
                query = st.text_input(
                    "ask_input",
                    value=st.session_state.get("q_input", ""),
                    placeholder="Ask your question about traffic rules, fines, licence, e-challan...",
                    label_visibility="collapsed",
                    key="query_text_box",
                )
            with c_mic:
                st.markdown('<div style="color:#1F5FE0;font-size:18px;text-align:right;">🎤</div>', unsafe_allow_html=True)

            _, c_sub1, c_sub2, _ = st.columns([0.2, 1.4, 1.6, 0.2], vertical_alignment="center")
            with c_sub1:
                st.markdown('<div class="btn-get-ans">', unsafe_allow_html=True)
                clicked = st.button("✈  Get Answer", key="btn_get_answer", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with c_sub2:
                if st.button("📄  Upload PDF / Challan", key="btn_goto_pdf", use_container_width=True):
                    st.session_state.page = "pdf"
                    st.rerun()

        if clicked and query:
            run_rag_question(query)

        # Examples Section
        st.markdown("**Try these examples:**")
        cols_ex = st.columns(4)
        for i, (col, (icon, colr, tint, text)) in enumerate(zip(cols_ex, EXAMPLES)):
            st.markdown(
                f"""
                <style>
                .st-key-ex_btn_{i} [data-testid="stIconMaterial"] {{
                  color: {colr} !important;
                  background: {tint} !important;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            with col:
                with st.container(key=f"ex_btn_{i}"):
                    if st.button(text, key=f"ex_{i}", icon=f":material/{icon}:", use_container_width=True):
                        st.session_state.q_input = text
                        run_rag_question(text)

        # Filter Chips Row
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        c_show, c_cen, c_state, c_disc = st.columns([0.12, 0.14, 0.18, 0.56], vertical_alignment="center")
        with c_show:
            st.markdown("**Showing:**")
        with c_cen:
            st.markdown('<span class="central-chip">Central</span>', unsafe_allow_html=True)
        with c_state:
            st.markdown('<div class="state-chip-btn">', unsafe_allow_html=True)
            if st.button("Tamil Nadu ✕", key="btn_chip_tn", help="Toggle Tamil Nadu"):
                if "Tamil Nadu" in st.session_state.states:
                    st.session_state.states = [s for s in st.session_state.states if s != "Tamil Nadu"]
                else:
                    st.session_state.states.append("Tamil Nadu")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_disc:
            st.caption("General information, not legal advice. State fines may differ.")

        # Show RAG result if any
        res = st.session_state.get("last_result")
        if res:
            st.markdown('<div style="height: 18px;"></div>', unsafe_allow_html=True)
            with st.container(key="result_box"):
                st.info(f"**Answer for:** {st.session_state.get('last_question')}")
                st.markdown(res.get("answer", ""))
                sources = res.get("sources", [])
                if sources:
                    st.markdown("---")
                    st.markdown(f"**Cited Sources ({len(sources)}):**")
                    for c, _ in sources:
                        st.markdown(f"- 📜 **{c.source_file}** · *{c.section}*")

    with col_right:
        st.markdown(
            f"""
            <div class="hero-img-box">
              <img src="data:image/jpeg;base64,{hero_b64()}" alt="Traffic light and car" />
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------- SCREEN 2: QUICK GUIDES
def show_screen_guides():
    render_page_banner("📖", "Quick Guides", "Get instant answers to common traffic law topics")

    for row_start in (0, 4):
        cols = st.columns(4)
        for i, (col, (icon, colr, tint, title, desc, preset_q)) in enumerate(
            zip(cols, GUIDES[row_start:row_start + 4]), row_start
        ):
            with col:
                with st.container(key=f"guide_card_{i}"):
                    st.markdown(
                        f"""
                        <div class="guide-card-icon" style="background:{tint};color:{colr};">
                          <span class="material-symbols-rounded">{icon}</span>
                        </div>
                        <div class="guide-card-title">{title}</div>
                        <div class="guide-card-desc">{desc}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.container(key=f"guide_act_{i}"):
                        if st.button("View Guide →", key=f"btn_g_{i}", use_container_width=True):
                            if preset_q:
                                st.session_state.page = "ask"
                                st.session_state.q_input = preset_q
                                run_rag_question(preset_q)
                                st.rerun()
                            else:
                                st.session_state.page = "fines"
                                st.rerun()
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- SCREEN 3: FINE LOOKUP
def show_screen_fines():
    render_page_banner("🔍", "Traffic Fine Lookup", "Search fines by offence or section number")

    col_s_in, col_s_btn = st.columns([5, 1], vertical_alignment="center")
    with col_s_in:
        fine_term = st.text_input(
            "fine_search",
            key="fine_search_term",
            placeholder="Search offence (e.g., helmet, drunk driving) or section number...",
            label_visibility="collapsed",
        )
    with col_s_btn:
        st.markdown('<div class="btn-get-ans">', unsafe_allow_html=True)
        st.button("🔍 Search", key="btn_fine_search", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    term = (fine_term or "").strip().lower()
    filtered = [
        r for r in FINES
        if not term or term in r[0].lower() or term in r[1].lower() or term in r[3].lower()
    ]

    # Render Table
    tbody = "".join(
        f"<tr><td>{i}</td><td>{html.escape(o)}</td><td>{s}</td><td>{f}</td><td>{html.escape(p)}</td></tr>"
        for i, (o, s, f, p) in enumerate(filtered, 1)
    )

    st.markdown(
        f"""
        <table class="fine-table">
          <thead>
            <tr>
              <th style="width: 45px;">#</th>
              <th style="width: 32%;">Offence</th>
              <th style="width: 15%;">Section</th>
              <th style="width: 15%;">Fine (₹)</th>
              <th>Other Penalty</th>
            </tr>
          </thead>
          <tbody>
            {tbody}
          </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Central-law amounts (Motor Vehicles Act, 1988 as amended in 2019), checked against official Act text. States can notify different amounts.")


# ---------------------------------------------------------------- SCREEN 4: ABOUT
def show_screen_about():
    render_page_banner("ⓘ", "About the Project", "A Retrieval-Augmented Generation (RAG) assistant for Indian traffic laws")

    # 4 Top Cards
    cols_top = st.columns(4)
    for i, (col, (icon, colr, tint, title, desc)) in enumerate(zip(cols_top, ABOUT_CARDS)):
        with col:
            with st.container(key=f"about_card_{i}"):
                st.markdown(
                    f"""
                    <div class="about-tile" style="background:{tint};color:{colr};">
                      <span class="material-symbols-rounded">{icon}</span>
                    </div>
                    <div style="font-size:1.05rem;font-weight:700;color:#14213D;margin-bottom:6px;">{title}</div>
                    <div style="font-size:0.86rem;color:#64748B;line-height:1.45;">{desc}</div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)

    # How it works Pipeline
    st.markdown("#### ⚙️ How it works")
    cols_pipe = st.columns([4, 0.6, 4, 0.6, 4, 0.6, 4], vertical_alignment="center")

    for n, (icon, colr, tint, title, desc) in enumerate(ABOUT_STEPS):
        with cols_pipe[n * 2]:
            with st.container(key=f"pipe_step_{n}"):
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;gap:12px;">
                      <div style="width:38px;height:38px;border-radius:10px;background:{tint};color:{colr};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <span class="material-symbols-rounded">{icon}</span>
                      </div>
                      <div>
                        <div style="font-size:0.92rem;font-weight:700;color:#14213D;">{title}</div>
                        <div style="font-size:0.8rem;color:#64748B;">{desc}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if n < len(ABOUT_STEPS) - 1:
            with cols_pipe[n * 2 + 1]:
                st.markdown('<div class="step-arrow-sign">→</div>', unsafe_allow_html=True)

    st.markdown('<div style="height: 36px;"></div>', unsafe_allow_html=True)

    # Automated Test runner
    st.markdown("#### 📋 Test the Assistant")
    st.markdown(f"Try {len(TESTS)} test questions to evaluate retrieval and answerability coverage.")
    if st.button("▶ Run Test Questions", type="primary", key="btn_run_tests"):
        with st.spinner("Running eval test suite..."):
            tests_res = run_tests(get_index(), use_llm=False)
            st.session_state.test_results = tests_res

    res_list = st.session_state.get("test_results")
    if res_list:
        passed = sum(1 for r in res_list if r.get("passed"))
        st.success(f"{passed}/{len(res_list)} test cases passed successfully.")
        st.dataframe(
            pd.DataFrame([
                {"Question": r["question"], "Expected": r["expected"], "Result": "PASS" if r["passed"] else "FAIL"}
                for r in res_list
            ]),
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------------------------------------------- SCREEN 5: PDF UPLOAD & RETRIEVAL
def show_screen_pdf():
    render_page_banner("📄", "Upload PDF & Retrieve Legal Information", "Upload an e-challan, court notice, or traffic document to retrieve violated sections and fine details")

    col_upload, col_sample = st.columns([1.5, 1], gap="large")
    with col_upload:
        st.markdown("**Upload Traffic PDF Document:**")
        uploaded = st.file_uploader(
            "Upload Document",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="pdf_uploader_widget"
        )
        c_act1, c_act2 = st.columns([1.2, 1])
        with c_act1:
            st.markdown('<div class="btn-get-ans">', unsafe_allow_html=True)
            scan_clicked = st.button("🔍  Extract & Retrieve", key="btn_pdf_extract", use_container_width=True, disabled=uploaded is None)
            st.markdown('</div>', unsafe_allow_html=True)
        with c_act2:
            if st.button("🔄  Clear Document", use_container_width=True):
                st.session_state.pdf_extracted_text = None
                st.session_state.pdf_filename = None
                st.rerun()

    with col_sample:
        st.markdown("**Or test with sample traffic documents:**")
        if st.button("📑 Sample 1: Helmet Violation (Section 194D)", use_container_width=True):
            st.session_state.pdf_extracted_text = """TRAFFIC POLICE NOTICE OF VIOLATION / E-CHALLAN
Challan No: DL-TR-2024-984210
Vehicle No: DL 01 AB 1234 (Hero Splendor)
Date & Time: 15-10-2024 11:30 AM
Location: Ring Road, Near Moti Bagh, New Delhi
Offence: Riding two-wheeler without protective headgear (helmet).
Sections Cited: Section 129, Section 194D of the Motor Vehicles Act, 1988 (as amended in 2019).
Penalty Amount: Rs 1000
Additional Action: Disqualification of driving licence for 3 months.
Payment Instructions: Pay online at echallan.parivahan.gov.in within 60 days to avoid court summons."""
            st.session_state.pdf_filename = "sample_helmet_194D.pdf"
            st.rerun()

        if st.button("📑 Sample 2: Drunken Driving Notice (Section 185)", use_container_width=True):
            st.session_state.pdf_extracted_text = """POLICE NOTICE / COURT SUMMONS
Notice No: KA-BLR-2024-77192
Vehicle Reg: KA 03 CD 5678
Date: 18-10-2024 23:45 HRS
Location: MG Road, Bangalore City
Offence: Driving by a drunken person or under influence of drugs. Breath analyser test: 68 mg / 100 ml blood.
Sections Cited: Section 185, Section 207 of the Motor Vehicles Act.
Vehicle Status: Detained under Section 207.
Hearing Date: 05-11-2024 before Metropolitan Magistrate Traffic Court.
Statutory Penalty: Up to Rs 10,000 fine and/or 6 months imprisonment."""
            st.session_state.pdf_filename = "sample_drunk_driving_185.pdf"
            st.rerun()

    text_to_process = None
    fname = "Uploaded Document"

    if uploaded is not None and scan_clicked:
        with st.spinner("Extracting text and retrieving legal sections..."):
            ext = uploaded.name.rsplit(".", 1)[-1].lower()
            text_to_process = scan.extract_text(uploaded.getvalue(), ext)
            fname = uploaded.name
            if not text_to_process:
                st.error("Could not extract text from this PDF. Please ensure it is a text-based PDF or test with a sample.")
            else:
                st.session_state.pdf_extracted_text = text_to_process
                st.session_state.pdf_filename = uploaded.name
    elif st.session_state.get("pdf_extracted_text"):
        text_to_process = st.session_state.get("pdf_extracted_text")
        fname = st.session_state.get("pdf_filename", "sample.pdf")

    if text_to_process:
        sections = scan.find_sections(text_to_process)
        glossary = scan.glossary_terms(text_to_process)
        index = get_index()

        st.markdown("---")
        st.subheader(f"📋 Retrieved Legal Information: {fname}")

        with st.expander("📄 View Extracted Document Content", expanded=False):
            st.text(text_to_process)

        st.markdown(f"##### ⚖️ Sections Cited in Document ({len(sections)})")
        if not sections:
            st.info("No specific statutory sections detected in document text. Running keyword retrieval on knowledge base...")
            results = index.retrieve(text_to_process[:200], k=3)
            for c, _ in results:
                with st.expander(f"{c.doc_title} > {c.section}"):
                    st.markdown(c.text)
        else:
            for s in sections:
                norm = scan.normalise_section(s)
                chunks = scan.lookup_section(index, norm) if norm else []
                title_badge = f"Section {s}"
                fine_match = next((f for f in FINES if f[1] == norm), None)
                with st.expander(f"📌 {title_badge} — {'Offence Detected' if fine_match else 'Act Reference'}", expanded=True):
                    if fine_match:
                        st.markdown(f"**Offence:** {fine_match[0]}")
                        st.markdown(f"**Statutory Fine Amount:** ₹{fine_match[2]}")
                        st.markdown(f"**Additional Penalty:** {fine_match[3]}")
                    if chunks:
                        st.markdown("**Official Motor Vehicles Act Text:**")
                        for ch in chunks:
                            st.info(ch.text)
                            st.caption(f"Source: {ch.source_ref}")
                    else:
                        st.caption("Detailed clause text in Act is referenced under general compounding rules.")

        if glossary:
            st.markdown(f"##### 💡 Legal Terms Explained ({len(glossary)})")
            st.dataframe(pd.DataFrame(glossary), use_container_width=True, hide_index=True)

        st.markdown("##### 🚀 What you need to do next")
        st.markdown("""
        1. **Verify Official Portal:** Visit the Ministry's official portal [echallan.parivahan.gov.in](https://echallan.parivahan.gov.in) to verify the authenticity of the notice.
        2. **Settlement / Compounding:** If compoundable, pay within the notified deadline (usually 60 days) to prevent court summons.
        3. **Virtual Court Disposals:** If directed to virtual court, visit [vcourts.gov.in](https://vcourts.gov.in) to plead guilty or submit an explanation.
        """)


# ---------------------------------------------------------------- MAIN CONTROLLER
render_navbar()

if st.session_state.page == "ask":
    show_screen_ask()
elif st.session_state.page == "guides":
    show_screen_guides()
elif st.session_state.page == "fines":
    show_screen_fines()
elif st.session_state.page == "pdf":
    show_screen_pdf()
elif st.session_state.page == "about":
    show_screen_about()
