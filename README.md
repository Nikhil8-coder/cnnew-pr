# Client-Server Chat Application (Streamlit version)

A Streamlit rebuild of the chat demo. Streamlit doesn't expose raw
WebSocket handlers like Flask-SocketIO, so this version shares chat
messages through a small SQLite file (`chat.db`, created automatically)
and refreshes the page every few seconds to pick up new messages —
giving a "multi-client" experience across browser tabs/devices.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```

4. Open the URL Streamlit prints (default `http://localhost:8501`).
   Open it in multiple browser tabs, or from another device using
   `http://<your-lan-ip>:8501`, to simulate multiple clients chatting.

## Notes
- `chat.db` is created next to `streamlit_app.py` on first run — it's
  git-ignored so it won't get committed with old messages.
- Messages persist across restarts; use the "Clear chat history"
  button in the app to wipe them.
- Refresh interval is set to 3 seconds (`REFRESH_MS` in `streamlit_app.py`);
  lower it for snappier updates at the cost of more frequent re-runs.
