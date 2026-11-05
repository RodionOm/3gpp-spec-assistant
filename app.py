"""ClauseFinder: ask about 5G NR, get an answer that cites the TS 38.300 clause it came from."""

import base64
import html
import re
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src" / "spec_assistant"))
from answer import Assistant  # noqa: E402
from setup_data import ensure_index  # noqa: E402

APP_NAME = "ClauseFinder"
SPEC = "TS 38.300 V18.11.0"
HERO_PHOTO = ROOT / "assets" / "hero.jpg"  # optional: your own photo, used in black and white
EXAMPLES = [
    "What is the RRC_INACTIVE state?",
    "How does handover between two gNBs work?",
    "Which transmission modes does RLC support?",
    "What is the capital of France?",
]

# Radio waves drawn in SVG: used as the hero background when there is no photo.
WAVES_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='1600' height='520' viewBox='0 0 1600 520'>
<g fill='none' stroke='white' stroke-opacity='0.16'>
<circle cx='1250' cy='560' r='120'/><circle cx='1250' cy='560' r='220'/><circle cx='1250' cy='560' r='320'/>
<circle cx='1250' cy='560' r='420'/><circle cx='1250' cy='560' r='520'/><circle cx='1250' cy='560' r='620'/>
<circle cx='1250' cy='560' r='720'/><circle cx='1250' cy='560' r='820'/></g>
<g stroke='white' stroke-opacity='0.5' stroke-width='2'>
<line x1='1250' y1='300' x2='1210' y2='520'/><line x1='1250' y1='300' x2='1290' y2='520'/>
<line x1='1226' y1='430' x2='1274' y2='430'/><line x1='1238' y1='365' x2='1262' y2='365'/></g>
</svg>"""


def hero_background():
    if HERO_PHOTO.exists():
        data = base64.b64encode(HERO_PHOTO.read_bytes()).decode()
        return (
            "linear-gradient(90deg, rgba(0,0,0,.85) 0%, rgba(0,0,0,.35) 70%),"
            f"url('data:image/jpeg;base64,{data}') center/cover"
        )
    data = base64.b64encode(WAVES_SVG.encode()).decode()
    return f"#000 url('data:image/svg+xml;base64,{data}') right bottom/cover no-repeat"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
html, body, p, div, button, input, h1, h4 { font-family: 'Inter', sans-serif !important; }
header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none; }
.block-container { max-width: 1120px; padding: 0 1rem; }
.bleed { width: 100vw; margin-left: calc(50% - 50vw); }

.nav { background: #000; color: #fff; padding: 14px 0; margin-top: -1rem; }
.nav .in { max-width: 1120px; margin: 0 auto; padding: 0 1rem; display: flex;
           justify-content: space-between; align-items: center; font-size: 14px; }
.nav .mark { font-weight: 600; letter-spacing: .02em; font-size: 17px; }
.nav .spec { color: #9a9a9a; }

.hero { background: HERO_BG; color: #fff; padding: 96px 0 104px; filter: grayscale(1); }
.hero .in { max-width: 1120px; margin: 0 auto; padding: 0 1rem; }
.hero h1 { font-size: 56px; font-weight: 300; line-height: 1.08; margin: 0 0 20px;
           max-width: 720px; color: #fff; letter-spacing: -.01em; }
.hero p { font-size: 19px; font-weight: 300; max-width: 560px; color: #d6d6d6; margin: 0; }

.label { text-transform: uppercase; letter-spacing: .12em; font-size: 12px;
         color: #666; margin: 48px 0 14px; font-weight: 600; }

div.stButton > button { border: 1px solid #000; border-radius: 0; background: #fff;
    color: #000; min-height: 76px; text-align: left; justify-content: flex-start;
    font-size: 15px; padding: 14px 18px; }
div.stButton > button:hover { background: #000; color: #fff; border-color: #000; }
div.stButton > button p { text-align: left; white-space: normal; overflow: visible; text-overflow: clip; }

[data-testid="stTextInput"] input { border-radius: 0; font-size: 20px; padding: 14px 4px;
    background: transparent !important; }
[data-testid="stTextInput"] [data-baseweb="input"] { border: none; border-bottom: 2px solid #000;
    border-radius: 0; background: transparent !important; }

.answer { font-size: 21px; line-height: 1.55; font-weight: 300; max-width: 860px; }
.clause { background: #000; color: #fff; padding: 1px 7px; font-size: .78em;
          font-weight: 600; white-space: nowrap; }

.card { border-top: 2px solid #000; padding-top: 14px; }
.card .num { font-size: 30px; font-weight: 300; }
.card .title { font-weight: 600; margin: 4px 0 8px; }
.card .snip { color: #444; font-size: 14px; line-height: 1.5; }
[data-testid="stExpander"] details { border-radius: 0; border-color: #ddd; }

.foot { background: #000; color: #bdbdbd; padding: 48px 0 40px; margin-top: 72px; font-size: 14px; }
.foot .in { max-width: 1120px; margin: 0 auto; padding: 0 1rem; display: grid;
            grid-template-columns: repeat(3, 1fr); gap: 32px; }
.foot h4 { color: #fff; font-weight: 600; font-size: 14px; margin: 0 0 8px; }
.foot .legal { grid-column: 1 / -1; border-top: 1px solid #333; padding-top: 16px; color: #8a8a8a; }
@media (max-width: 700px) { .hero h1 { font-size: 36px; } .foot .in { grid-template-columns: 1fr; } }
</style>
"""

st.set_page_config(page_title=APP_NAME, layout="wide")
st.markdown(CSS.replace("HERO_BG", hero_background()), unsafe_allow_html=True)


@st.cache_resource(show_spinner="First start: building the index, about 2-3 minutes...")
def get_assistant():
    ensure_index()
    return Assistant()


@st.cache_data(show_spinner=False, max_entries=200)
def ask(question):
    return get_assistant().answer(question)


def set_question(text):
    st.session_state.question = text


def mark_citations(text):
    safe = html.escape(text)
    return re.sub(r"\[(TS [^\]]+)\]", r'<span class="clause">\1</span>', safe)


def snippet(text, words=38):
    parts = text.split()
    return " ".join(parts[:words]) + (" ..." if len(parts) > words else "")


st.markdown(
    f"""
<div class="bleed nav"><div class="in">
  <span class="mark">{APP_NAME}</span><span class="spec">{SPEC}</span>
</div></div>
<div class="bleed hero"><div class="in">
  <h1>Find the clause,<br>not just an answer.</h1>
  <p>Ask a question about 5G NR. Every answer points to the section of the 3GPP
  specification it came from, or says the section was not found.</p>
</div></div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="label">Try a question</div>', unsafe_allow_html=True)
cols = st.columns(len(EXAMPLES))
for col, example in zip(cols, EXAMPLES):
    col.button(example, on_click=set_question, args=(example,), width="stretch")

st.markdown('<div class="label">Or ask your own</div>', unsafe_allow_html=True)
question = st.text_input(
    "Question", key="question", label_visibility="collapsed",
    placeholder="e.g. What does the SDAP layer do?",
)

if question.strip():
    with st.spinner("Searching the specification..."):
        result = ask(question)

    st.markdown('<div class="label">Answer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer">{mark_citations(result["answer"])}</div>', unsafe_allow_html=True)

    st.markdown('<div class="label">Clauses used</div>', unsafe_allow_html=True)
    chunk_cols = st.columns(len(result["chunks"]))
    for col, (_, chunk) in zip(chunk_cols, result["chunks"]):
        with col:
            st.markdown(
                f"""<div class="card"><div class="num">§{html.escape(chunk['section'])}</div>
<div class="title">{html.escape(chunk['title'])}</div>
<div class="snip">{html.escape(snippet(chunk['text']))}</div></div>""",
                unsafe_allow_html=True,
            )
            with st.expander("Full text"):
                st.write(chunk["text"])

st.markdown(
    """
<div class="bleed foot"><div class="in">
  <div><h4>Search</h4>Keyword search (BM25) and semantic search are merged,
  then a cross-encoder reranks the top 20 candidates.</div>
  <div><h4>Answer</h4>The language model sees only the top 3 sections and must cite
  each fact or reply "Not found in the provided sections".</div>
  <div><h4>Measured</h4>On 20 hand-written questions the right section is in the top 3
  for 19 (14 with semantic search alone). Answer quality is not yet measured.</div>
  <div class="legal">Independent student project. Not affiliated with or endorsed by 3GPP
  or any company. 3GPP specifications are used for research and education.</div>
</div></div>
""",
    unsafe_allow_html=True,
)
