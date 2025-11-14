from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import auth_ui
import db
from llm_utils import chat_with_researcher, summarize_text
from news_data import (
    CATEGORIES,
    fake_headlines,
    fake_indices,
    fake_signals,
    fake_watchlists,
    macro_snapshot,
    risk_alerts,
    sentiment_summary,
    trending_topics,
    fake_portfolio_series,
    sector_exposure,
    generate_alert_feed,
    company_snapshot,
    company_price_series,
)

st.set_page_config(page_title="FinNews Portal", layout="wide")


def load_css() -> None:
    css_path = Path(__file__).parent / "static.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def hero_header(user: str) -> None:
    st.markdown(
        f"""
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;'>
          <div>
            <h1 style='margin-bottom:0;'>FinanceAI Command Center</h1>
            <p style='color:#94a3b8;margin:0;'>Welcome, {user}. Live intelligence feed ready.</p>
          </div>
          <div style='display:flex;gap:0.5rem;'>
            <span style='padding:0.4rem 0.9rem;border-radius:999px;background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.4);color:#a7f3d0;font-size:0.8rem;'>LIVE DATA ACTIVE</span>
            <span style='padding:0.4rem 0.9rem;border-radius:999px;border:1px solid rgba(148,163,184,0.3);color:#94a3b8;font-size:0.8rem;'>Last update {datetime.utcnow().strftime('%H:%M UTC')}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def time_ago(iso_ts: str) -> str:
    ts = datetime.fromisoformat(iso_ts)
    diff = datetime.utcnow().replace(tzinfo=timezone.utc) - ts.replace(tzinfo=timezone.utc)
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"


def render_dashboard_tab(headlines, sentiment, alerts, macro, topics):
    counts = sentiment["counts"]
    total = sum(counts.values())
    cols = st.columns(3)
    metrics = [
        ("Total Articles", total, "coverage in last hour"),
        ("Bullish Ratio", f"{counts['buy']/total*100:.1f}%", "share of BUY sentiment"),
        ("Risk Alerts", len(alerts), "active warnings"),
    ]
    for col, (label, value, desc) in zip(cols, metrics):
        with col:
            st.markdown(
                f"<div class='metric-card'><h3>{label}</h3><div class='value'>{value}</div><p>{desc}</p></div>",
                unsafe_allow_html=True,
            )

    left, right = st.columns((2, 1))
    with left:
        st.subheader("Market News Summarizer")
        text = st.text_area("Paste article or transcript", height=220)
        if st.button("Summarize", key="summarize_btn", help="Generate concise research notes"):
            st.markdown(f"<div class='metric-card'>{summarize_text(text)}</div>", unsafe_allow_html=True)
        st.markdown("### Macro Snapshot")
        st.dataframe(pd.DataFrame(macro))
        trending_html = " ".join([f"<span class='badge'>{topic}</span>" for topic in topics])
        st.markdown(f"### Trending Topics: {trending_html}", unsafe_allow_html=True)
    with right:
        st.subheader("Live Flash Headlines")
        for article in headlines[:5]:
            st.markdown(
                f"""
                <div class='metric-card'>
                  <h3>{article['ticker']} · {article['category']}</h3>
                  <div class='value' style='font-size:1rem'>{article['title']}</div>
                  <span style='font-size:0.8rem;color:#94a3b8'>{article['source']} · {time_ago(article['timestamp'])}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.subheader("Risk Alerts")
        for alert in alerts:
            st.markdown(
                f"""
                <div class='metric-card'>
                  <h3>{alert['title']} · {alert['severity']}</h3>
                  <p style='color:#94a3b8'>{alert['description']}</p>
                  <span style='font-size:0.8rem;color:#94a3b8'>{alert['timestamp']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_investments_tab(signals, watchlists, headlines):
    st.subheader("Investment Heatmap")
    buy = sum(1 for c in signals["cards"] if c["direction"] == "BUY")
    hold = sum(1 for c in signals["cards"] if c["direction"] == "HOLD")
    sell = sum(1 for c in signals["cards"] if c["direction"] == "SELL")
    cols = st.columns(3)
    for col, (label, value, desc) in zip(
        cols,
        [
            ("BUY Signals", buy, "Momentum setups detected"),
            ("HOLD Signals", hold, "Mean reversion candidates"),
            ("SELL Signals", sell, "Negative catalysts"),
        ],
    ):
        with col:
            st.markdown(
                f"<div class='metric-card'><h3>{label}</h3><div class='value'>{value}</div><p>{desc}</p></div>",
                unsafe_allow_html=True,
            )
    st.markdown("### Live Recommendations")
    cols = st.columns(3)
    if "selected_card" not in st.session_state:
        st.session_state.selected_card = signals["cards"][0]
    for idx, card in enumerate(signals["cards"]):
        col = cols[idx % 3]
        with col:
            st.markdown(
                f"""
                <div class='metric-card'>
                  <h3>{card['ticker']} · {card['direction']}</h3>
                  <p style='color:#94a3b8'>{card['summary']}</p>
                  <p style='font-size:0.85rem;color:#94a3b8'>Confidence {card['confidence']}% · {card['signals']} signals</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"View {card['ticker']}", key=f"detail_{idx}"):
                st.session_state.selected_card = card
    st.markdown("### Watchlists")
    if "selected_watchlist" not in st.session_state:
        st.session_state.selected_watchlist = watchlists[0]
    watch_cols = st.columns(len(watchlists))
    for col, wl in zip(watch_cols, watchlists):
        with col:
            if st.button(wl["name"], key=f"wl_{wl['name']}"):
                st.session_state.selected_watchlist = wl
            st.markdown(
                f"<div class='metric-card'><h3>{wl['name']}</h3><p style='color:#94a3b8'>{wl['tickers']}</p><p>{wl['signals']} active alerts</p></div>",
                unsafe_allow_html=True,
            )
    st.info(f"Focused watchlist: {st.session_state.selected_watchlist['name']}")
    selected = st.session_state.selected_card
    st.markdown(f"## {selected['ticker']} — Detailed View")
    st.markdown(
        f"""
        <div class='metric-card'>
          <h3>{selected['company']} sentiment</h3>
          <ul>
            <li>Direction: {selected['direction']}</li>
            <li>Confidence: {selected['confidence']}%</li>
            <li>Signals contributing: {selected['signals']}</li>
            <li>Risk level: {selected['risk']}</li>
            <li>Horizon: {selected['horizon']}</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("#### Related Headlines")
    related = [h for h in headlines if h["ticker"] == selected["ticker"]][:5]
    if not related:
        st.info("No recent headlines for this ticker in the synthetic feed.")
    else:
        for article in related:
            st.markdown(
                f"* {article['title']} — {article['source']} ({time_ago(article['timestamp'])})",
                unsafe_allow_html=False,
            )


def render_news_center(headlines):
    st.subheader("News Analysis Center")
    ticker_text = " • ".join(
        f"{article['ticker']} {article['title']}" for article in headlines[:15]
    )
    st.markdown(
        f"<div class='metric-card'><marquee behavior='scroll' direction='left' scrollamount='5'>{ticker_text}</marquee></div>",
        unsafe_allow_html=True,
    )
    category = st.selectbox("Filter category", ["All"] + CATEGORIES)
    search = st.text_input("Search by keyword")
    filtered = headlines if category == "All" else [h for h in headlines if h["category"] == category]
    if search:
        filtered = [h for h in filtered if search.lower() in h["title"].lower()]
    if "selected_news" not in st.session_state and filtered:
        st.session_state.selected_news = filtered[0]
    st.markdown("### Live Headlines")
    for idx, article in enumerate(filtered[:12]):
        cols = st.columns([4, 1])
        with cols[0]:
            st.markdown(
                f"""
                <div class='metric-card'>
                  <h3>{article['ticker']} — {article['title']}</h3>
                  <p style='color:#94a3b8'>{article['summary']}</p>
                  <div style='display:flex;justify-content:space-between;font-size:0.85rem;color:#94a3b8;'>
                    <span>{article['source']}</span>
                    <span>{time_ago(article['timestamp'])}</span>
                    <span>{article['stance'].upper()}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            if st.button("Analyze", key=f"news_btn_{idx}"):
                st.session_state.selected_news = article

    selected = st.session_state.get("selected_news")
    if selected:
        st.markdown(f"## {selected['ticker']} Stock Dashboard")
        snap = company_snapshot(selected["ticker"])
        price_df = pd.DataFrame(company_price_series(selected["ticker"]))
        price_chart = (
            alt.Chart(price_df)
            .mark_line(color="#34d399")
            .encode(x="day:Q", y="price:Q")
            .properties(height=250)
        )
        st.altair_chart(price_chart, use_container_width=True)
        metric_cols = st.columns(3)
        metric_cols[0].metric("Price", f"${snap['price']}", f"{snap['change']:+}")
        metric_cols[1].metric("Volume (M)", f"{snap['volume']}")
        metric_cols[2].metric("Market Cap ($B)", f"{snap['market_cap']}")
        extra_cols = st.columns(3)
        extra_cols[0].metric("P/E", snap["pe"])
        extra_cols[1].metric("Beta", snap["beta"])
        extra_cols[2].metric("Direction", selected["stance"].upper())

    table = pd.DataFrame(filtered[:60])[["ticker", "title", "source", "category", "impact", "stance", "timestamp"]]
    table.rename(
        columns={
            "ticker": "Ticker",
            "title": "Headline",
            "source": "Source",
            "category": "Category",
            "impact": "Tag",
            "stance": "Sentiment",
            "timestamp": "Time",
        },
        inplace=True,
    )
    table["Time"] = table["Time"].apply(time_ago)
    st.markdown("### Feed Table")
    st.dataframe(table)


def render_indices_tab(indices):
    st.subheader("Global Indices Tracker")
    st.dataframe(pd.DataFrame(indices))


def render_portfolio_tab(series, exposures, alert_feed):
    st.subheader("Portfolio Performance (Synthetic)")
    df = pd.DataFrame(series)
    chart = (
        alt.Chart(df)
        .mark_line(color="#60a5fa")
        .encode(x="date:T", y="value:Q")
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Demo equity curve with random drift.")

    st.subheader("Sector Exposure & PnL")
    exp_df = pd.DataFrame(exposures)
    bar = (
        alt.Chart(exp_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(x="sector:N", y="weight:Q", color=alt.Color("pnl:Q", scale=alt.Scale(scheme="redblue")))
    )
    st.altair_chart(bar, use_container_width=True)
    st.dataframe(exp_df)
    st.subheader("Action Items")
    for alert in alert_feed:
        st.markdown(
            f"""
            <div class='metric-card'>
              <h3>{alert['title']}</h3>
              <p style='color:#94a3b8'>{alert['body']}</p>
              <p style='color:#cbd5f5;font-size:0.85rem'>Status: {alert['status']} · Team: {alert['assignee']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_chat_tab():
    st.subheader("Research Copilot Chatbot")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    chat_box = st.container()
    for msg in st.session_state.chat_history:
        role = "🧑‍💼" if msg["role"] == "user" else "🤖"
        bubble_class = "chat-user" if msg["role"] == "user" else "chat-assistant"
        chat_box.markdown(
            f"<div class='chat-bubble {bubble_class}'><strong>{role}</strong>: {msg['content']}</div>",
            unsafe_allow_html=True,
        )
    prompt = st.text_input("Ask about markets, risks, or scenarios")
    if st.button("Send", key="chat_btn"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        reply = chat_with_researcher(st.session_state.chat_history, prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.experimental_rerun()


def main() -> None:
    load_css()
    db.init_db()
    st_autorefresh(interval=5000, key="news-refresh")
    user = auth_ui.auth_section()
    if not user:
        st.stop()
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    hero_header(user)

    st.sidebar.header("Research Copilot")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        role = "🧑‍💼" if msg["role"] == "user" else "🤖"
        st.sidebar.markdown(f"<div class='chat-bubble {'chat-user' if role=='🧑‍💼' else 'chat-assistant'}'><strong>{role}</strong>: {msg['content']}</div>", unsafe_allow_html=True)
    sidebar_prompt = st.sidebar.text_input("Ask anything", key="sidebar_prompt")
    if st.sidebar.button("Send", key="sidebar_chat_btn"):
        st.session_state.chat_history.append({"role": "user", "content": sidebar_prompt})
        reply = chat_with_researcher(st.session_state.chat_history, sidebar_prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.experimental_rerun()

    tabs = st.tabs(["Dashboard", "Investments", "News Center", "Global Indices", "Portfolio & Backtests"])

    headlines = fake_headlines()
    signals = fake_signals()
    watchlists = fake_watchlists()
    indices = fake_indices()
    sentiment = sentiment_summary(headlines)
    alerts = risk_alerts()
    macro = macro_snapshot()
    topics = trending_topics(headlines)
    portfolio_series = fake_portfolio_series()
    exposures = sector_exposure()
    alert_feed = generate_alert_feed()

    with tabs[0]:
        render_dashboard_tab(headlines, sentiment, alerts, macro, topics)
    with tabs[1]:
        render_investments_tab(signals, watchlists, headlines)
    with tabs[2]:
        render_news_center(headlines)
    with tabs[3]:
        render_indices_tab(indices)
    with tabs[4]:
        render_portfolio_tab(portfolio_series, exposures, alert_feed)

st.caption("Deploy via: cloudflared tunnel --url http://localhost:8501")


if __name__ == "__main__":
    main()
