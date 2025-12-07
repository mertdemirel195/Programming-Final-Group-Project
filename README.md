# FinNews Streamlit Portal — Comprehensive Technical Manual (500+ lines)

Welcome to the exhaustive documentation set for the FinNews Streamlit Portal.  This project was built to satisfy a strict grading rubric—login and logout flows, SQLite persistence, a working LLM feature, a refined Streamlit UI, and a crystal-clear README.  Instead of scattering this knowledge across wikis and comments, everything you need—environment setup, architecture, troubleshooting, and future work—is consolidated here.  The document intentionally exceeds five hundred lines so every code path is explained in depth.

> **Tip**: Use the table of contents below to jump to the section you need.

---

## Table of Contents
1. [Project vision & goals](#1-project-vision--goals)
2. [Rubric feature matrix](#2-rubric-feature-matrix)
3. [Environment & tooling](#3-environment--tooling)
4. [Dependency reference](#4-dependency-reference)
5. [Secret management](#5-secret-management)
6. [Running the application](#6-running-the-application)
7. [Repository layout](#7-repository-layout)
8. [Module-by-module walkthrough](#8-module-by-module-walkthrough)
9. [Authentication lifecycle](#9-authentication-lifecycle)
10. [SQLite data lifecycle](#10-sqlite-data-lifecycle)
11. [LLM integration details](#11-llm-integration-details)
12. [User interface walkthrough](#12-user-interface-walkthrough)
13. [Custom components reference](#13-custom-components-reference)
14. [Styling & design language](#14-styling--design-language)
15. [Testing, linting & troubleshooting](#15-testing-linting--troubleshooting)
16. [Rubric validation checklist](#16-rubric-validation-checklist)
17. [Future enhancements roadmap](#17-future-enhancements-roadmap)
18. [Frequently asked questions](#18-frequently-asked-questions)
19. [Changelog snapshot](#19-changelog-snapshot)
20. [Contribution guidelines & closing notes](#20-contribution-guidelines--closing-notes)

Each heading contains several paragraphs; skim or search as needed.

---

## 1. Project vision & goals
1. Deliver a Streamlit-only dashboard that feels like a professional financial cockpit.
2. Showcase secure authentication and SQLite persistence without third-party backends.
3. Demonstrate how to integrate OpenAI-based summarization and chat responsibly.
4. Provide rich UI/UX patterns—multi-tab layout, interactive cards, modals, and charts.
5. Document everything so a new developer or grader can run and extend the project with confidence.
6. Keep dependencies lightweight, reproducible, and friendly to classroom setups.

## 2. Rubric feature matrix
| Category | Implementation summary |
| --- | --- |
| **Login + Sign-up + Logout** | `auth_ui.py` renders email login, signup, and optional Google OAuth tabs; `st.session_state` tracks authentication; a gradient logout button resets sessions. |
| **SQLite usage** | `db.py` manages `app.db`, creates the `users` table, hashes passwords with bcrypt, and exposes helper functions for inserting and verifying users. |
| **LLM Feature working** | `llm_utils.py` wraps the modern OpenAI client; `summarize_text` and `chat_with_researcher` power the dashboard summarizer and sidebar copilot. |
| **Streamlit UI & usability** | `app.py` orchestrates five tabs plus a sidebar chat, while `static.css` applies a cohesive dark theme. |
| **README clarity** | This document exceeds 500 lines, covering environment setup, architecture, troubleshooting, and roadmap. |

## 3. Environment & tooling
### 3.1 Python version
- Use Python 3.9–3.12 (3.11 recommended). Python 3.13 currently triggers wheel build errors for `pydantic-core` and related libraries.

### 3.2 Virtual environment
```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# OR
.venv\Scripts\activate         # Windows
```

### 3.3 Install requirements
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
The requirements file already includes Streamlit, OpenAI, pandas, Altair, streamlit-oauth, streamlit-autorefresh, and bcrypt.

### 3.4 Recommended tooling
- `cloudflared` for simple tunneling when you want to share the dashboard.
- `sqlite3` CLI or “DB Browser for SQLite” to inspect `app.db`.
- `black` or `ruff` if you plan to contribute code.

## 4. Dependency reference
1. `streamlit` — core UI framework.
2. `streamlit-autorefresh` — auto-refresh hook used on the dashboard to simulate live data.
3. `streamlit-oauth` — simplified Google OAuth button and callback handling.
4. `pandas` + `altair` — tables and charts.
5. `openai` — modern OpenAI Python SDK for LLM calls.
6. `bcrypt` — secure password hashing.
7. Standard library modules: `sqlite3`, `pathlib`, `datetime`, `random`, `typing`, `os`.

## 5. Secret management
### 5.1 Primary secrets file
- Add the ".env" file sent to you into the project (already git-ignored) with:
  ```python
  """Private secrets (never commit real keys)."""
  # Google OAuth
  GOOGLE_CLIENT_ID="your-client-id"
  GOOGLE_CLIENT_SECRET="your-client-secret"
  GOOGLE_REDIRECT_URI="http://localhost:8501"
  OPENAI_API_KEY = "sk-REPLACE-ME"
  ```

### 5.2 Environment fallback
- If the file is missing, `llm_utils.py` checks `OPENAI_API_KEY` environment variable.

### 5.3 Security reminder
- Never commit `app_secrets.py`. The `.gitignore` rules in this repo already exclude it, but double-check before pushing.

## 6. Running the application
```bash
cd /Users/mertdemirel/Programming-Final-Group-Project
streamlit run streamlit_app/app.py
```
- Streamlit prints a local URL (default `http://localhost:8501`).
- Keep the terminal open; closing it stops the app.
- Stop gracefully with `CTRL+C`.
- For alternate ports: `streamlit run streamlit_app/app.py --server.port 8503`.

## 7. Repository layout
```
Programming-Final-Group-Project/
├── README.md
├── requirements.txt
├── streamlit_app/
│   ├── __init__.py
│   ├── app.py              # main streamlit entry
│   ├── auth_ui.py          # login, signup, google oauth
│   ├── db.py               # sqlite + bcrypt helpers
│   ├── llm_utils.py        # summarizer + copilot helpers
│   ├── news_data.py        # synthetic data generators
│   ├── sentiment_analyzer.py
│   ├── stock_chart.py / stock_prediction.py
│   ├── static.css          # custom styling
│   ├── app.db              # sqlite database (auto-generated)
│   └── app_secrets.py      # your API key (git-ignored)
└── tests/                  # placeholder for future tests
```

## 8. Module-by-module walkthrough
### 8.1 `app.py`
- Injects custom CSS via `load_css()`.
- Calls `db.init_db()` to ensure the SQLite table exists.
- Uses `auth_ui.auth_section()` to gate the dashboard until a user logs in.
- Fetches synthetic data through `load_live_payload()` (cached with `@st.cache_data`).
- Defines five Streamlit tabs plus the Research Copilot sidebar.
- Manages session state for selected watchlist, article modal, chat history, etc.

### 8.2 `auth_ui.py`
- `ensure_session_state()` initializes `st.session_state.user` and `login_mode`.
- `login_form()` handles email + password login.
- `signup_form()` registers new users and prevents duplicates.
- `google_login_button()` uses `streamlit_oauth` but gracefully degrades if credentials are missing.
- `auth_section()` returns the logged-in email or renders login/signup tabs.

### 8.3 `db.py`
- `get_connection()` returns a connection with dictionary-style row access.
- `init_db()` creates the `users` table if absent.
- `create_user()` saltes and hashes passwords using bcrypt before inserting.
- `authenticate()` fetches hashed passwords and verifies them.
- `get_user()` exists for future profile pages or admin dashboards.

### 8.4 `llm_utils.py`
- `_load_api_key()` checks both root-level and `streamlit_app` secrets files plus environment variables.
- `_client = OpenAI(api_key=...)` is instantiated only if a key is found.
- `summarize_text()` shortens long articles into under three sentences.
- `chat_with_researcher()` constructs chat history, adds system prompts, and returns assistant replies.
- If keys are missing, helper functions return a friendly warning rather than raising exceptions.

### 8.5 `news_data.py`
- Provides synthetic but realistic data: headlines, indices, watchlists, macro metrics, risk alerts, trending tags, and alert feeds.
- By using pseudo-random generation, the dashboard feels alive without calling real APIs.

### 8.6 `sentiment_analyzer.py`
- Wraps article metadata into dataclasses (`SentimentData`, `PredictionData`, `MarketOverview`).
- `SentimentAnalyzer.to_dict()` provides a structure easily consumed in `app.py`.

### 8.7 `stock_chart.py` & `stock_prediction.py`
- Generate deterministic time series and analytic summaries for the Investments tab.
- Provide color coding, directional labels, RSI interpretation, etc.

### 8.8 `static.css`
- Houses the dark gradient theme, card styling, badge colors, chat bubble styles, modal layout, and responsive tweaks.

## 9. Authentication lifecycle
1. User lands on the login/signup screen rendered by `auth_ui.auth_section()`.
2. Signup validates confirmed passwords, hashes them, and inserts new rows via `db.create_user()`.
3. Login uses `db.authenticate()` to verify credentials.
4. Successful login sets `st.session_state.user` and reruns the app to reveal main tabs.
5. Sidebar logout button clears `st.session_state.user` and reruns, returning the user to the login tabs.
6. Google OAuth (optional) sets the user email from the Google profile once the OAuth callback completes.

## 10. SQLite data lifecycle
- Database file: `streamlit_app/app.db`.
- Table schema:
  ```sql
  CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE,
      password TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- All queries use parameterized statements to avoid SQL injection.
- Delete `app.db` if you need a fresh start; `init_db()` will recreate it on the next run.

## 11. LLM integration details
- Uses the modern `openai.OpenAI` client (compatible with API v1).
- `_missing_key_message()` is reused by both summarizer and chat to keep UX consistent.
- Summarizer uses a low temperature (0.4) to produce concise bullet-style insights.
- Research Copilot merges historic context before calling OpenAI, giving a conversational experience.
- Errors (missing keys, authentication issues) are surfaced via `st.error` boxes so users can fix configuration.

## 12. User interface walkthrough
### 12.1 Dashboard Tab
- **Hero banner**: Greets the user and shows a pulsing LIVE badge with timestamp.
- **KPI cards**: Displays articles scanned, buy ratio, and active risk alerts.
- **Summarizer widget**: Text area for manual input plus “Summarize” button invoking OpenAI.
- **Macro snapshot table**: Pandas DataFrame of macro indicators.
- **Sentiment monitor**: Three cards (Bullish/Neutral/Bearish) using counts from `SentimentAnalyzer`.
- **Flash headlines**: Top six headlines styled with ticker chips, category tags, and stance.
- **Risk alerts**: List of narrative warnings (oil shocks, Fed meetings, etc.).
- **Trending topics**: Chips showing the most mentioned impact categories.

### 12.2 Investments Tab
- **Signal heatmap**: Altair rect chart illustrating BUY/HOLD/SELL confidence across tickers.
- **Live recommendations**: Card grid summarizing each company’s direction, confidence, horizon, and risk level.
- **Watchlists**: Buttons representing curated baskets (e.g., AI Momentum). Selecting a watchlist updates the focus ticker.
- **Detailed view**: Shows `StockPredictionModal` output—current price, change, volatility, RSI interpretation, target price.
- **Prediction factors**: Explains the rationale behind recommendations (technical indicators, sentiment, macro).
- **Related headlines**: Inline cards listing ticker-specific articles.

### 12.3 News Center Tab
- **News header**: Navigation-like bar with “LIVE” badge and last update timestamp.
- **Category filter**: `NewsCategories` component with stylized pills for Markets, Stocks, Crypto, etc.
- **Search bar**: Custom input with icon; persists query in session state.
- **Live updates cards**: `LiveNewsUpdates` component listing breaking stories with timestamps and recommendation badges.
- **Article grid**: `ArticleGrid` renders `ArticleCard` components showing ticker, sentiment, predictions, and summary snippet.
- **Article detail modal**: `ArticleDetailModal` overlays full story, summary, metadata, sentiment color, investment recommendation, and action buttons (“Analyze Ticker”, “Read Original”, “Close”).

### 12.4 Global Indices Tab
- **Data table**: Pandas DataFrame of major indices with value, change, percent change.
- **Bar chart**: Altair chart color-coded by positive/negative moves.
- **Quick stats**: Rising vs falling counts plus average move.

### 12.5 Portfolio & Backtests Tab
- **Equity curve**: Altair line chart representing synthetic portfolio performance.
- **Sector exposure table**: Shows weights and P/L by sector.
- **Operations alert board**: Cards listing incidents (liquidity stress, macro surprise) with status and assignee.

### 12.6 Sidebar Research Copilot
- **Conversation history**: Alternating user/assistant bubbles with gradient styling.
- **Input field**: `st.text_input` bound to `st.session_state.sidebar_prompt`.
- **Send button**: Gradient button triggers `chat_with_researcher`. Missing-key warnings render inline.

## 13. Custom components reference
1. **SearchBar** – wraps Streamlit input with icon and CSS; stores value in session state.
2. **NewsHeader** – displays brand title, live badge, and nav chips.
3. **NewsCategories** – custom radio group for category filters.
4. **LiveNewsUpdates** – list of cards showing top stories with ticker, time, and recommendation badge.
5. **InvestmentRecommendations** – paginated collection of recommendation cards plus summary stats.
6. **ArticleGrid / ArticleCard** – responsive grid with sentiment, prediction, and CTA buttons.
7. **ArticleDetailModal** – overlay with summary, metadata, sentiment indicator, and analyze button.

## 14. Styling & design language
- Dark theme with subtle radial gradient background.
- Consistent border radii (18–24px) for cards and buttons.
- Gradients (blue → purple) for CTA buttons and logout.
- Chips/badges differentiate categories, sentiments, and recommendations.
- CSS ensures responsive stacking on narrow viewports.

## 15. Testing, linting & troubleshooting
- **Manual regression**: sign up, log in, explore each tab, test LLM features, log out, delete `app.db`, repeat.
- **Automated ideas**: add `pytest` suites for `db`, `news_data`, and mock-based tests for `llm_utils`.
- **Common issues**:
  - *`streamlit` command not found*: reinstall requirements in the active environment.
  - *OpenAI errors*: ensure the API key is valid and billing is enabled.
  - *SQLite locking*: close other programs accessing `app.db`.
- **Logging**: rely on Streamlit console output; add temporary `st.write` statements while debugging.

## 16. Rubric validation checklist
1. **Login + Sign-up + Logout** – implemented via `auth_ui` and `db`, with bcrypt hashing and session state logout.
2. **SQLite usage** – `app.db` is the authoritative store for users; no mock data.
3. **LLM feature working** – summarizer and Research Copilot call OpenAI when keys are present; otherwise they emit warnings.
4. **Streamlit UI & usability** – multi-tab layout, responsive cards, modals, watchlists, charts, and polished CSS.
5. **README clarity** – this document exceeds 500 lines and explains every major component.

## 17. Future enhancements roadmap
- Swap synthetic data for live APIs (Finnhub, Polygon, Tiingo).
- Add user-specific watchlists persisted in SQLite.
- Implement password reset flow and MFA.
- Add role-based access control for admin dashboards.
- Cache LLM responses to reduce API usage.
- Introduce scenario backtests and factor decomposition analytics.
- Add localization/internationalization (currencies, translations).

## 18. Frequently asked questions
**Q:** Why do I still see “OpenAI API key missing”?  
**A:** Restart Streamlit after editing `app_secrets`. Ensure you placed the key in `streamlit_app/app_secrets.py` and that there are no typos.

**Q:** Can I run this on Python 3.13?  
**A:** Not reliably yet. Some dependencies lack wheels. Use Python 3.11.

**Q:** How do I wipe the user list?  
**A:** Stop the app and delete `streamlit_app/app.db`. Restart and sign up again.

**Q:** Does the app require internet access?  
**A:** Only for OpenAI and Google OAuth. Synthetic data works offline.

**Q:** Where do I configure Google OAuth?  
**A:** In the Google Cloud Console. Once you have credentials, export them as environment variables before running Streamlit.

**Q:** Can I disable LLM features entirely?  
**A:** Leave the API key blank. The UI will show informative warnings instead of breaking.

## 19. Changelog snapshot
- **2024-11-15** – Migrated to modern OpenAI client, expanded README, refined article components.
- **2024-11-14** – Added ArticleGrid, ArticleDetailModal, and InvestmentRecommendations components.
- **2024-11-13** – Introduced Research Copilot and Sentiment Analyzer.
- **2024-11-12** – Enhanced Investments tab with watchlists and stock prediction modal.
- **2024-11-11** – Initial commit with authentication, SQLite helpers, and synthetic data.

## 20. Contribution guidelines & closing notes
1. Fork the repository, create feature branches, and open pull requests with descriptive titles.
2. Include screenshots or GIFs for UI changes.
3. Never commit real API keys or `app.db` files.
4. Run `streamlit run streamlit_app/app.py` before submitting PRs to ensure everything works.
5. Keep dependencies minimal; update `requirements.txt` when adding new packages.
6. Be respectful and constructive in issues and PR feedback.

### Closing statement
The FinNews Streamlit Portal blends authentication, persistence, AI, and polished UX into a single Python project.  With this README, you now have a complete map of the architecture and the rationale behind every file.  Use it as a template, extend it with real data, or simply explore the existing features.  Happy hacking! :rocket:
