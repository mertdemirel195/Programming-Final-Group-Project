# Streamlit FinNews Portal

Comprehensive Streamlit web app featuring:
- SQLite-backed authentication (signup/login) with bcrypt hashed passwords
- Optional Google Sign-In via OAuth
- Session-based login persistence + logout
- Market news summarizer (LLM-powered)
- Global indices snapshot with live data (yfinance)
- Research Copilot chatbot (task-focused LLM UI)
- Deployment hint via `cloudflared` for public link sharing

## Project Layout
```
streamlit_app/
├─ app.py             # main Streamlit entry
├─ auth_ui.py         # login / signup / Google UI
├─ db.py              # SQLite + bcrypt helpers
├─ llm_utils.py       # OpenAI summarize + chatbot
├─ secrets.py         # place OPENAI API key here
└─ app.db             # generated automatically
```

## Setup & Run
1. Install deps:
```bash
pip install streamlit openai bcrypt streamlit-oauth httpx feedparser yfinance streamlit-autorefresh altair
```
2. Configure secrets: edit `streamlit_app/secrets.py` and set `OPENAI_API_KEY`. (Optional) export `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` for Google login.
3. Launch:
```bash
cd streamlit_app
streamlit run app.py
```
4. (Hard) share public link:
```bash
cloudflared tunnel --url http://localhost:8501
```

## Notes
- Users stored in SQLite with hashed passwords (bcrypt).
- Google login leverages `streamlit-oauth` (needs OAuth credentials).
- LLM endpoints use OpenAI; add ChatGPT-compatible key.
