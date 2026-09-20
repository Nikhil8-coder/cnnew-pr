"""
Client-Server Chat Application (Streamlit version)

Streamlit apps don't keep a persistent per-client socket the way
Flask-SocketIO does -- each browser tab is its own session that
re-runs the script on every interaction. To still get a shared,
"multi-client" chat, all messages are stored in a small SQLite
database on disk that every session reads from, and the page
auto-refreshes on a timer so new messages from other users appear.
"""

import sqlite3
import socket
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

DB_PATH = Path(__file__).parent / "chat.db"
REFRESH_MS = 3000  # poll for new messages every 3 seconds


# ---------- storage layer ----------

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
    return conn


def add_message(conn, username, text):
    conn.execute(
        "INSERT INTO messages (username, text, created_at) VALUES (?, ?, ?)",
        (username, text, datetime.now().strftime("%H:%M:%S")),
    )
    conn.commit()


def get_messages(conn, limit=200):
    rows = conn.execute(
        "SELECT username, text, created_at FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return list(reversed(rows))


def clear_messages(conn):
    conn.execute("DELETE FROM messages")
    conn.commit()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# ---------- app ----------

st.set_page_config(page_title="Client-Server Chat", page_icon="💬", layout="centered")

st_autorefresh(interval=REFRESH_MS, key="chat_autorefresh")

conn = get_connection()

st.title("💬 Client-Server Chat Application")
st.caption("Streamlit version — shared state via SQLite, polling instead of WebSockets")

with st.expander("Networking concepts", expanded=False):
    st.markdown(
        f"""
        - **Server IP:** `{get_local_ip()}`
        - **Port:** `8501` (Streamlit default)
        - **Protocol:** HTTP long-polling / WebSocket (used internally by
          Streamlit for UI updates); this app's *chat* data is shared via a
          polling read from a SQLite file every {REFRESH_MS // 1000}s, which
          mimics a broadcast without a dedicated chat socket.
        - **Connected clients:** each browser tab/session is a separate client
          re-running this script and reading the same shared message store.
        """
    )

if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.username:
    name = st.text_input("Choose a display name to join the chat:")
    if st.button("Join") and name.strip():
        st.session_state.username = name.strip()
        st.rerun()
    st.stop()

st.success(f"Connected as **{st.session_state.username}**")

# chat history
messages = get_messages(conn)
chat_container = st.container(height=350)
with chat_container:
    if not messages:
        st.caption("No messages yet. Say hello!")
    for username, text, created_at in messages:
        is_me = username == st.session_state.username
        with st.chat_message("user" if is_me else "assistant"):
            st.markdown(f"**{username}** · _{created_at}_")
            st.write(text)

# composer
prompt = st.chat_input("Type a message...")
if prompt:
    add_message(conn, st.session_state.username, prompt)
    st.rerun()

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Leave chat"):
        st.session_state.username = ""
        st.rerun()
with col2:
    if st.button("Clear chat history"):
        clear_messages(conn)
        st.rerun()
