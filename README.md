# Client-Server Chat Application

A real-time chat app demonstrating the client-server model, provided in
two versions. Deploy **one at a time** — pick whichever fits your target:

- **`flask_socketio_version/`** — Flask + Socket.IO, true WebSocket push.
  Good for Render, Railway, a VPS, or any host that runs a long-lived
  Python process.
- **`streamlit_version/`** — Streamlit app, shares messages through a
  small SQLite file and auto-refreshes to show new ones. Good for
  Streamlit Community Cloud or Hugging Face Spaces (Streamlit SDK).

## Run the Flask + Socket.IO version

```bash
cd flask_socketio_version
pip install -r requirements_flask.txt
python flask_server.py
```
Open `http://localhost:5000`. Open multiple tabs to simulate multiple clients.

## Run the Streamlit version

```bash
cd streamlit_version
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py
```
Open `http://localhost:8501`. Open multiple tabs to simulate multiple clients.

### Deploying the Streamlit version to Streamlit Community Cloud
1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app from the repo.
3. Set **Main file path** to `streamlit_version/streamlit_app.py`.
4. Streamlit Cloud auto-detects `requirements_streamlit.txt` in that same
   folder — no extra config needed. If it doesn't pick it up, set
   **Advanced settings → Requirements file** to
   `streamlit_version/requirements_streamlit.txt` explicitly.

## Repo layout
```
chat-app/
├── README.md
├── flask_socketio_version/
│   ├── flask_server.py
│   ├── requirements_flask.txt
│   ├── templates/index.html
│   └── static/script.js
└── streamlit_version/
    ├── streamlit_app.py
    └── requirements_streamlit.txt
```

## Notes
- Each version is self-contained — only install/run the one you're deploying.
- The Streamlit version creates `chat.db` next to `streamlit_app.py` on
  first run to store messages; delete it to reset the chat history.
- No `.gitignore` is included by request. If you don't want `chat.db`,
  `venv/`, or `__pycache__/` committed, add one later or remove them
  from the repo manually before pushing.
