# Client-Server Chat Application

A simple real-time chat app demonstrating the client-server model, provided
in two implementations:

| Folder | Stack | Real-time mechanism |
|---|---|---|
| [`flask_socketio_version/`](flask_socketio_version) | Flask + Socket.IO | True WebSocket push |
| [`streamlit_version/`](streamlit_version) | Streamlit | SQLite-backed polling |

Both show connection status, server IP/port/protocol, usernames, and
timestamps. Pick whichever fits your assignment/deployment target —
each folder is self-contained with its own `requirements.txt` and
`README.md`.

## Quick start

```bash
# Flask + Socket.IO version
cd flask_socketio_version
pip install -r requirements.txt
python server.py            # http://localhost:5000

# Streamlit version
cd streamlit_version
pip install -r requirements.txt
streamlit run streamlit_app.py   # http://localhost:8501
```

## Repo layout
```
chat-app/
├── README.md
├── .gitignore
├── flask_socketio_version/
│   ├── server.py
│   ├── requirements.txt
│   ├── README.md
│   ├── templates/index.html
│   └── static/script.js
└── streamlit_version/
    ├── streamlit_app.py
    ├── requirements.txt
    └── README.md
```
