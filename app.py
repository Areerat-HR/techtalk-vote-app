import sqlite3
import time
from pathlib import Path
import streamlit as st

APP_TITLE = "TechTalk Vote: Favorite Presenter"
ADMIN_PASSWORD = "22"
SHOW_TOP_N = 3

EMPLOYEES = [
    "Apisit Wisai","Areerat Tippayawong","Athiwat Khamnon","Atthaphon Kajitpongpanich","Aunyamanee Pukkaew",
    "Bussaraporn Daungin","Jirapong Nanta","Kamonrat Sangkeiwrat","Kronpongsakon Kronkum","Nampheung Chuatay",
    "Nattapon Deebang","Nutchaporn Jaengmongkol","Nuttapon Comsoi","Panupong Yodwong","Paradon Saengjam",
    "Peerapan Khanchoom","Piangsit Nualsri","Pipatpon Kessuwan","Pitakpong Chitsutti","Pratpong Muaengwong",
    "Sai Lounge Mine","Saranya Jeenmatchaya","Sasipong Singprom","Sirakrit Sermsuk","Siwakon Sittirin",
    "Songyot Jaichai","Suchonlaphat Suwanaphokin","Sujaree Khumgoen","Supasit Wiriyapap","Suphuruek Somboon",
    "Tawan Chandsri","Teerasak Wichai","Thanabodee Krathu","Thawatchai Sunarat","Theerapan Khanthigul",
    "Thipawan Nanta","Ungkairt Sirivoranankul","Wiriya Jamol","Worachet Baramee"
]

PRESENTERS = [
    " Ansible Athiwat Khamnon",
    " Functional programming Athiwat Khamnon",
    "[Fault tolerance with newjeans] Athiwat Khamnon",
    "[Bold with Tailwind] Bussaraporn Daungin",
    "[Rails 8] Paradon Saengjam",
    "[Generative AI: Evalution and Beyond] Pipatpon Kessuwan",
    "[Cyber security] Ungkairt Sirivoranankul",
    "[PDPA] Ungkairt Sirivoranankul",
    "[Figma MCP] Wiriya Jamol",
    "[Security showcase]Worachet Baramee",
]

DB_PATH = Path("techtalk_votes.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter TEXT NOT NULL UNIQUE,
            presenter TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def has_voted(voter: str) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM votes WHERE voter=? LIMIT 1", (voter,))
    ok = c.fetchone() is not None
    conn.close()
    return ok

def add_vote(voter: str, presenter: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO votes(voter, presenter, created_at) VALUES (?,?,?)",
        (voter, presenter, int(time.time()))
    )
    conn.commit()
    conn.close()

def top_presenters(n: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT presenter, COUNT(*) as cnt
        FROM votes
        GROUP BY presenter
        ORDER BY cnt DESC, presenter ASC
        LIMIT ?
    """, (n,))
    rows = c.fetchall()
    conn.close()
    return rows

def not_voted_yet():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT voter FROM votes")
    voted = {r[0] for r in c.fetchall()}
    conn.close()
    return sorted([e for e in EMPLOYEES if e not in voted])

def reset_votes():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM votes")
    conn.commit()
    conn.close()

st.set_page_config(page_title=APP_TITLE)
init_db()

st.title(APP_TITLE)
st.caption("โหวตได้ 1 ครั้ง / เลือก Presenter ได้ 1 คน (Presenter ไม่มีสิทธิ์โหวต)")

tab_vote, tab_admin = st.tabs(["🗳️ Vote", "🏆 Results (HR)"])

with tab_vote:
    voter = st.selectbox("ชื่อของคุณ", EMPLOYEES)

    if voter in PRESENTERS:
        st.warning("คุณเป็น Presenter จึงไม่มีสิทธิ์โหวตในรอบนี้ 🙏")
        st.stop()

    presenter = st.radio(
        "เลือก Presenter TechTalk ที่คุณชื่นชอบมากที่สุด (เลือกได้ 1 คน)",
        PRESENTERS,
        index=None
    )

    if st.button("Submit Vote"):
        if has_voted(voter):
            st.error("คุณได้โหวตไปแล้ว")
        elif presenter is None:
            st.error("กรุณาเลือก Presenter 1 คนก่อนส่งโหวต")
        else:
            try:
                add_vote(voter, presenter)
                st.success("บันทึกคะแนนเรียบร้อย ขอบคุณค่ะ 💙")
            except sqlite3.IntegrityError:
                st.error("คุณได้โหวตไปแล้ว")

with tab_admin:
    if "reset_done" not in st.session_state:
        st.session_state.reset_done = False

    pw = st.text_input("HR password", type="password")

    if pw == ADMIN_PASSWORD:
        if st.session_state.reset_done:
            st.success("ลบผลโหวตทั้งหมดเรียบร้อยแล้ว ✅")

        st.subheader(f"🏆 Top {SHOW_TOP_N} Presenter")
        rows = top_presenters(SHOW_TOP_N)
        if rows:
            for i, (name, cnt) in enumerate(rows, start=1):
                st.write(f"#{i} {name} — {cnt} votes")
        else:
            st.info("ยังไม่มีคะแนนโหวต")

        st.subheader("📋 คนที่ยังไม่ได้โหวต")
        remaining = not_voted_yet()
        if remaining:
            for name in remaining:
                st.write(f"- {name}")
        else:
            st.success("พนักงานโหวตครบทุกคนแล้ว 🎉")

        st.divider()
        st.subheader("⚠️ HR Only: Reset Votes")
        confirm = st.checkbox("ยืนยันว่าต้องการลบคะแนนโหวตทั้งหมด")

        if st.button("🗑️ Reset all votes"):
            if not confirm:
                st.warning("กรุณาติ๊กยืนยันก่อนลบข้อมูล")
            else:
                reset_votes()
                st.session_state.reset_done = True
                st.rerun()

    elif pw != "":
        st.error("รหัสผ่านไม่ถูกต้อง")

