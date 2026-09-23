"""
Client-Server Chat Application (Streamlit version)

Built to make the client-server networking model visible, not just
functional: every client is a separate Streamlit session (a separate
browser "connection" to one shared server process); the server is the
single source of truth (a SQLite database on disk); and "real-time"
here means the server-side truth is polled and pushed to each client's
UI on a short timer via st.fragment(run_every=...), instead of a full
page reload. That's the same request/response + polling idea real
networked chat systems use before they upgrade to a push protocol like
WebSockets (see the Flask-SocketIO version of this project for that).
"""

import socket
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "chat.db"
REFRESH_SECONDS = 2          # how often the live area polls the "server"
PRESENCE_TIMEOUT = 8         # seconds of silence before a client is "offline"
MAX_MESSAGES_SHOWN = 300

st.set_page_config(
    page_title="Client-Server Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stChatMessage { border-radius: 14px; }
      .server-pill {
          display:inline-block; padding:2px 10px; border-radius:999px;
          background:#16a34a1a; color:#16a34a; font-weight:600; font-size:12px;
          border:1px solid #16a34a55;
      }
      .server-pill.off {
          background:#ef44441a; color:#ef4444; border:1px solid #ef444455;
      }
      .concept-box {
          background: rgba(127,127,127,0.08);
          border: 1px solid rgba(127,127,127,0.25);
          border-radius: 10px;
          padding: 12px 14px;
          font-size: 13px;
          line-height: 1.55;
      }
      code.arch { font-size: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# "Server": a single SQLite database every client session reads/writes.
# This plays the role of the server's shared state in the client-server
# model — every client talks to the same store, never to each other
# directly.
# --------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS presence (
            session_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            last_seen TEXT NOT NULL
        )
        """
    )
    return conn


def add_message(conn: sqlite3.Connection, username: str, text: str) -> None:
    conn.execute(
        "INSERT INTO messages (username, text, created_at) VALUES (?, ?, ?)",
        (username, text, datetime.now().strftime("%H:%M:%S")),
    )
    conn.commit()


def get_messages(conn: sqlite3.Connection, limit: int = MAX_MESSAGES_SHOWN):
    rows = conn.execute(
        "SELECT username, text, created_at FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return list(reversed(rows))


def clear_messages(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM messages")
    conn.commit()


def touch_presence(conn: sqlite3.Connection, session_id: str, username: str) -> None:
    """Heartbeat: tell the server 'this client is still connected'."""
    conn.execute(
        """
        INSERT INTO presence (session_id, username, last_seen)
        VALUES (?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            username = excluded.username,
            last_seen = excluded.last_seen
        """,
        (session_id, username, datetime.utcnow().isoformat()),
    )
    conn.commit()


def remove_presence(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("DELETE FROM presence WHERE session_id = ?", (session_id,))
    conn.commit()


def get_active_clients(conn: sqlite3.Connection):
    cutoff = (datetime.utcnow() - timedelta(seconds=PRESENCE_TIMEOUT)).isoformat()
    rows = conn.execute(
        "SELECT username FROM presence WHERE last_seen >= ? ORDER BY username",
        (cutoff,),
    ).fetchall()
    return [r[0] for r in rows]


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


conn = get_connection()

# --------------------------------------------------------------------------
# Each browser tab = one client = one session_id. This is the clearest
# hook for the "client" half of client-server: it's a separate identity
# talking to the same server, exactly like a separate socket connection
# would be in the Flask-SocketIO version.
# --------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "username" not in st.session_state:
    st.session_state.username = ""

# --------------------------------------------------------------------------
# Sidebar — the concept panel. This is what turns a working chat app into
# a *teaching* one: it names each moving part and maps it onto what the
# student sees on screen.
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("📡 Client–Server Model")
    st.markdown(
        f"""
<div class="concept-box">

**Server** — one Python process holding the single source of truth
(<code>chat.db</code>). It never talks to clients directly; clients read
and write to it.

**Client** — this browser tab. Every tab that opens this app gets its
own random <code>session_id</code> and is a separate client, even on
the same machine.

**Request / response** — sending a message is: client writes a row →
server (the DB) accepts it → every client's next poll reads it back.

**Polling ≈ real-time** — every client fragment re-queries the server
every **{REFRESH_SECONDS}s** and repaints only the chat area, not the
whole page. This is the same idea as long-polling; the Flask-SocketIO
version instead holds a live WebSocket open so the server can *push*
the instant a message arrives, with no polling delay.

</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Architecture**")
    st.code(
        """
   Client A ─┐
   Client B ─┼──►  SERVER  ──►  chat.db
   Client C ─┘   (this app)   (shared state)

   every client polls the server
   on a timer and re-renders
        """,
        language="text",
    )

    st.markdown("**This server, right now**")
    st.markdown(
        f"- IP: `{get_local_ip()}`  \n"
        f"- Port: `8501` (Streamlit default, local dev)  \n"
        f"- Protocol: HTTP polling (chat data) + Streamlit's own WebSocket (UI)"
    )

# --------------------------------------------------------------------------
# Join screen
# --------------------------------------------------------------------------
if not st.session_state.username:
    st.title("💬 Client-Server Chat Application")
    st.caption("A live demo of one server, many independent clients.")
    st.write("")
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        st.subheader("Connect to the server")
        name = st.text_input("Display name", placeholder="e.g. Asha")
        if st.button("🔌 Connect", type="primary", use_container_width=True):
            if name.strip():
                st.session_state.username = name.strip()
                touch_presence(conn, st.session_state.session_id, st.session_state.username)
                st.rerun()
            else:
                st.warning("Enter a name to connect.")
    st.stop()

# --------------------------------------------------------------------------
# Connected header
# --------------------------------------------------------------------------
header_l, header_r = st.columns([4, 1])
with header_l:
    st.title("💬 Client-Server Chat Application")
    st.markdown(
        f'<span class="server-pill">● connected as {st.session_state.username}</span>',
        unsafe_allow_html=True,
    )
with header_r:
    if st.button("🚪 Disconnect", use_container_width=True):
        remove_presence(conn, st.session_state.session_id)
        st.session_state.username = ""
        st.rerun()

st.write("")


# --------------------------------------------------------------------------
# Live area: the only part that reruns on a timer. Everything else on
# the page (header, composer, buttons) stays put — this is the
# "partial update" behaviour real-time UIs aim for.
# --------------------------------------------------------------------------
@st.fragment(run_every=REFRESH_SECONDS)
def live_chat_area():
    touch_presence(conn, st.session_state.session_id, st.session_state.username)
    active_clients = get_active_clients(conn)
    messages = get_messages(conn)

    m1, m2, m3 = st.columns(3)
    m1.metric("🟢 Active clients", len(active_clients))
    m2.metric("💬 Messages", len(messages))
    m3.metric("🔄 Last synced", datetime.now().strftime("%H:%M:%S"))

    others = [u for u in active_clients if u != st.session_state.username]
    if others:
        st.caption("Also online: " + ", ".join(others))
    else:
        st.caption("You're the only client connected right now.")

    chat_box = st.container(height=420)
    with chat_box:
        if not messages:
            st.caption("No messages yet — say hello 👋")
        for username, text, created_at in messages:
            is_me = username == st.session_state.username
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(f"**{username}**  ⋅  _{created_at}_")
                st.write(text)


live_chat_area()

# --------------------------------------------------------------------------
# Composer — a normal (full-app) rerun on submit, same as any Streamlit
# widget outside a fragment. Kept outside the fragment so typing never
# gets interrupted by the polling refresh.
# --------------------------------------------------------------------------
prompt = st.chat_input("Type a message and press Enter...")
if prompt:
    add_message(conn, st.session_state.username, prompt)
    st.rerun()

if st.button("🗑️ Clear chat history for everyone"):
    clear_messages(conn)
    st.rerun()
