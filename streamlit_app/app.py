from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

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

st.set_page_config(
    page_title="Financial Command Center",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    css_path = Path("static.css")
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8", errors="ignore")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        
    # Add real-time clock JavaScript
    st.markdown(
        """
        <script>
            function updateAllClocks() {
                const now = new Date();
                const utcTime = now.toUTCString().match(/\\d{2}:\\d{2}:\\d{2}/)[0];
                const elements = document.querySelectorAll('[id^="live-time"]');
                elements.forEach(el => {
                    if (el) {
                        el.textContent = 'Last update ' + utcTime + ' UTC';
                    }
                });
            }
            setInterval(updateAllClocks, 1000);
            updateAllClocks();
            
            // Remove extra boxes and move elements into copilot-panel
            function moveElementsIntoPanel() {
                // First, remove any extra containers/borders
                document.querySelectorAll('.stContainer, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"]').forEach(container => {
                    if (container.querySelector('.copilot-panel')) {
                        container.style.background = 'transparent';
                        container.style.border = 'none';
                        container.style.boxShadow = 'none';
                        container.style.outline = 'none';
                        container.style.padding = '0';
                        container.style.margin = '0';
                    }
                });
                
                const panels = document.querySelectorAll('.copilot-panel');
                panels.forEach(panel => {
                    // Skip if this is a closing tag (empty div)
                    if (panel.children.length > 0 && panel.querySelector('.copilot-header')) {
                        // This is the opening panel, find its parent container
                        const container = panel.closest('[data-testid="stVerticalBlock"]') || panel.parentElement;
                        if (!container) return;
                        
                        // Remove borders/backgrounds from parent
                        container.style.background = 'transparent';
                        container.style.border = 'none';
                        container.style.boxShadow = 'none';
                        
                        // Find all siblings after the opening panel
                        let current = panel.nextSibling;
                        const closingPanel = Array.from(container.children).find(
                            el => el !== panel && el.classList && el.classList.contains('copilot-panel') && el.children.length === 0
                        );
                        
                        while (current && current !== closingPanel) {
                            if (current.nodeType === 1 && current !== closingPanel) {
                                // Remove borders from siblings
                                if (current.style) {
                                    current.style.background = 'transparent';
                                    current.style.border = 'none';
                                    current.style.boxShadow = 'none';
                                }
                                // Move element into panel
                                if (!panel.contains(current)) {
                                    panel.insertBefore(current, closingPanel || null);
                                }
                            }
                            current = current.nextSibling;
                        }
                    }
                });
            }
            
            // Run after page load
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', moveElementsIntoPanel);
            } else {
                moveElementsIntoPanel();
            }
            
            // Use MutationObserver to handle Streamlit's dynamic updates
            const observer = new MutationObserver(() => {
                setTimeout(moveElementsIntoPanel, 50);
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Also run after delays for Streamlit updates
            setTimeout(moveElementsIntoPanel, 100);
            setTimeout(moveElementsIntoPanel, 500);
            setTimeout(moveElementsIntoPanel, 1000);
        </script>
        """,
        unsafe_allow_html=True,
    )


def hero_header(user: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-card__title">
                <p class="eyebrow">Financial Command Center</p>
                <h1>Hello, {user.split('@')[0].title()}.</h1>
                <p>Live intelligence feed ready. Macro, risk, and sentiment streams refresh constantly.</p>
                <div class="hero-pill-row">
                    <span class="pill live">LIVE DATA ACTIVE</span>
                    <span class="pill muted" id="live-time-{user}">Last update {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</span>
                </div>
                <div class="hero-cta-row">
                    <a class="cta-button primary" href="#summarizer">Launch AI Summarizer</a>
                    <a class="cta-button" href="#copilot-panel">Talk to Research Copilot</a>
                </div>
                <p class="hero-disclaimer">For demonstration purposes only. Not financial advice.</p>
            </div>
            <div class="hero-card__stat-grid">
                <div class="mini-stat">
                    <p class="label">Signal Pipelines</p>
                    <h3>4</h3>
                    <span>running now</span>
                </div>
                <div class="mini-stat">
                    <p class="label">Assets Tracked</p>
                    <h3>120+</h3>
                    <span>synthetic universe</span>
                </div>
                <div class="mini-stat">
                    <p class="label">Latency</p>
                    <h3>&lt;1s</h3>
                    <span>refresh cadence</span>
                </div>
                <div class="mini-stat">
                    <p class="label">Equities Covered</p>
                    <h3>2,500+</h3>
                    <span>global listings</span>
                </div>
                <div class="mini-stat">
                    <p class="label">Markets Covered</p>
                    <h3>25</h3>
                    <span>regions monitored</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_stock_chart(price_df: pd.DataFrame, color: str) -> alt.Chart:
    df = price_df.copy()
    df.reset_index(drop=True, inplace=True)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        x_field = "time:T"
        tooltip_time = alt.Tooltip("time:T", title="Time", format="%H:%M")
    else:
        df["step"] = df.index
        x_field = "step:Q"
        tooltip_time = alt.Tooltip("step:Q", title="Step")

    gradient = alt.Gradient(
        gradient="linear",
        stops=[
            alt.GradientStop(color=color, offset=0),
            alt.GradientStop(color="rgba(15,23,42,0)", offset=1),
        ],
        x1=0,
        x2=0,
        y1=0,
        y2=1,
    )
    base_chart = alt.Chart(df).encode(
        x=alt.X(x_field, axis=alt.Axis(title="", grid=False, labelColor="#94a3b8")),
        y=alt.Y("price:Q", axis=alt.Axis(title="", grid=False, labelColor="#94a3b8")),
        tooltip=[tooltip_time, alt.Tooltip("price:Q", title="Price", format="$.2f")],
    )
    area = base_chart.mark_area(color=gradient)
    line = base_chart.mark_line(color=color, strokeWidth=2)

    chart = area + line
    if "prev_close" in df.columns:
        rule = (
            alt.Chart(pd.DataFrame({"value": [df["prev_close"].iloc[0]]}))
            .mark_rule(strokeDash=[4, 4], color="#94a3b8")
            .encode(y="value:Q")
        )
        chart = chart + rule
    return chart.properties(height=200).configure_view(
        strokeWidth=0,
        fill="#1e293b"  # SOLID background for charts
    ).configure(
        background="#1e293b",  # SOLID background
        padding={"left": 10, "top": 10, "right": 10, "bottom": 10}
    ).configure_axis(
        labelColor="#ffffff",  # White labels
        titleColor="#ffffff",  # White titles
        gridColor="#475569",  # Visible grid
        domainColor="#94a3b8"  # Visible axis lines
    )


def handle_copilot_message(prompt: str) -> None:
    if not prompt or not prompt.strip():
        return
    st.session_state.chat_history.append({"role": "user", "content": prompt.strip()})
    reply = chat_with_researcher(st.session_state.chat_history, prompt.strip())
    st.session_state.chat_history.append({"role": "assistant", "content": reply})


def render_inline_copilot() -> None:
    st.markdown("<div id='copilot-panel'></div>", unsafe_allow_html=True)
    st.markdown("<div class='copilot-panel'>", unsafe_allow_html=True)
    
    # Header section
    st.markdown(
        """
        <div class="copilot-header">
            <div>
                <p class="eyebrow">LLM Analyst</p>
                <h3>Research Copilot</h3>
                <p class="copilot-subtitle">Synthesizes macro, news, and positioning context in seconds.</p>
            </div>
            <div class="copilot-status">
                <span class="pill live">COPILOT ONLINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Metrics section
    metric_cols = st.columns(3)
    metrics = [
        ("Latency", "<700ms", "avg response"),
        ("Sources", "300+", "curated feeds"),
        ("Context Window", "128k", "tokens"),
    ]
    for col, (label, value, hint) in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class='copilot-metric'>
                    <p class='label'>{label}</p>
                    <h4>{value}</h4>
                    <span>{hint}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    # Suggestions section
    suggestions = [
        "Summarize today's semiconductor catalysts",
        "What macro risks should I watch this week?",
        "Compare AI infrastructure names with most inflows",
    ]
    chips = "".join([f"<span class='copilot-chip'>{text}</span>" for text in suggestions])
    st.markdown(f"<div class='copilot-suggestions'><p>Popular prompts</p>{chips}</div>", unsafe_allow_html=True)
    
    # Input section
    prompt = st.text_input(
        "Ask anything",
        key="inline_copilot_prompt",
        placeholder="e.g., Give me a 3-bullet brief on EV demand trends",
    )
    send = st.button("Send", key="inline_copilot_send")
    
    if send:
        handle_copilot_message(prompt)
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)


def time_ago(iso_ts: str) -> str:
    ts = datetime.fromisoformat(iso_ts)
    diff = datetime.now(timezone.utc) - ts.replace(tzinfo=timezone.utc)
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
    total = max(sum(counts.values()), 1)
    cols = st.columns(3)
    metrics = [
        ("Total Articles", total, "coverage last hour"),
        ("Bullish Ratio", f"{counts['buy']/total*100:.1f}%", "share of BUY sentiment"),
        ("Risk Alerts", len(alerts), "active warnings"),
    ]
    for col, (label, value, desc) in zip(cols, metrics):
        with col:
            st.markdown(
                f"<div class='metric-card'><h3>{label}</h3><div class='value'>{value}</div><p>{desc}</p></div>",
                unsafe_allow_html=True,
            )

    left, right = st.columns((2.2, 1))
    with left:
        with st.container():
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown("<div id='summarizer'></div>", unsafe_allow_html=True)
            st.subheader("Market News Summarizer")
            text = st.text_area("Paste article or transcript", height=200, label_visibility="collapsed")
            if st.button("Summarize", key="summarize_btn", help="Generate concise research notes"):
                st.markdown(f"<div class='llm-response'>{summarize_text(text)}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #ffffff !important; font-weight: 700 !important; margin-bottom: 1rem; font-size: 1.5rem;'>Macro Snapshot</h3>", unsafe_allow_html=True)
            macro_df = pd.DataFrame(macro)
            
            # Create a simple, visible table with HTML for better control
            table_html = "<table style='width: 100%; border-collapse: collapse; background: #1e293b;'>"
            table_html += "<thead><tr style='background: #0f172a; border-bottom: 2px solid rgba(148, 163, 184, 0.6);'>"
            for col in macro_df.columns:
                table_html += f"<th style='color: #ffffff !important; font-weight: 700 !important; padding: 0.75rem; text-align: left; border: 1px solid rgba(148, 163, 184, 0.4);'>{col.upper()}</th>"
            table_html += "</tr></thead><tbody>"
            
            for idx, row in macro_df.iterrows():
                change_val_str = str(row['change'])
                # Parse the change value correctly - format is like "+0.33%" or "-0.66%"
                try:
                    # Remove % sign and convert to float (handles both + and - signs)
                    change_val = float(change_val_str.replace('%', '').strip())
                    is_positive = change_val > 0  # Increasing = Green
                    is_negative = change_val < 0  # Decreasing = Red
                except (ValueError, AttributeError):
                    # Fallback: check for + or - in string
                    is_positive = '+' in change_val_str and '-' not in change_val_str.replace('+', '')
                    is_negative = '-' in change_val_str and not is_positive
                
                # Green for positive (increasing), Red for negative (decreasing)
                if is_positive:
                    change_bg = 'rgba(34, 197, 94, 0.4)'
                    change_color = '#22c55e'
                elif is_negative:
                    change_bg = 'rgba(248, 113, 113, 0.4)'
                    change_color = '#ef4444'
                else:
                    change_bg = '#1e293b'
                    change_color = '#ffffff'
                
                table_html += f"<tr style='border-bottom: 1px solid rgba(148, 163, 184, 0.3);'>"
                table_html += f"<td style='color: #ffffff !important; font-weight: 600 !important; padding: 0.75rem; background: #1e293b; border: 1px solid rgba(148, 163, 184, 0.4);'>{row['asset']}</td>"
                table_html += f"<td style='color: #ffffff !important; font-weight: 600 !important; padding: 0.75rem; background: #1e293b; border: 1px solid rgba(148, 163, 184, 0.4);'>{row['value']}</td>"
                table_html += f"<td style='color: {change_color} !important; font-weight: 700 !important; padding: 0.75rem; background: {change_bg} !important; border: 1px solid rgba(148, 163, 184, 0.4);'>{row['change']}</td>"
                table_html += "</tr>"
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        trending_html = " ".join([f"<span class='badge'>{topic}</span>" for topic in topics])
        st.markdown(f"<div class='glass-panel'><h4>Trending Topics</h4>{trending_html}</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-panel'><h4>Spotlight Stories</h4>", unsafe_allow_html=True)
        spot_cols = st.columns(3)
        for col, article in zip(spot_cols, headlines[:3]):
            series = pd.DataFrame(company_price_series(article["ticker"], bias=article.get("stance")))
            change = series["price"].iloc[-1] - series["price"].iloc[0]
            line_color = "#22c55e" if change >= 0 else "#f87171"
            chart = build_stock_chart(series, line_color).properties(height=150)
            with col:
                st.markdown(
                    f"""
                    <div class='spotlight-card'>
                        <p class='eyebrow'>{article['category']}</p>
                        <h4>{article['title']}</h4>
                        <p class='spotlight-meta'>{article['source']} · {time_ago(article['timestamp'])}</p>
                    """,
                    unsafe_allow_html=True,
                )
                st.altair_chart(chart, use_container_width=True)
                st.markdown(
                    f"""
                        <p class='spotlight-trend {"bullish" if change >= 0 else "bearish"}'>
                            {change:+.2f} ({(change/ max(series['price'].iloc[0],1))*100:+.2f}%)
                        </p>
                        <p class='spotlight-summary'>{article['summary']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        with st.container():
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #ffffff !important; font-weight: 700 !important; margin-bottom: 1rem; font-size: 1.5rem;'>Live Flash Headlines</h3>", unsafe_allow_html=True)
            for idx, article in enumerate(headlines[:5]):
                # Determine sentiment color
                sentiment = article.get('sentiment', 'neutral').lower()
                sentiment_color = '#22c55e' if sentiment == 'positive' else ('#ef4444' if sentiment == 'negative' else '#94a3b8')
                sentiment_bg = 'rgba(34, 197, 94, 0.15)' if sentiment == 'positive' else ('rgba(248, 113, 113, 0.15)' if sentiment == 'negative' else 'rgba(148, 163, 184, 0.1)')
                
                st.markdown(
                    f"""
                    <div class='flash-headline-card' style='border-left: 4px solid {sentiment_color};'>
                      <div class='flash-headline-header'>
                        <span class='flash-live-indicator'>🔴 LIVE</span>
                        <span class='flash-ticker'>{article['ticker']}</span>
                        <span class='flash-category'>{article['category']}</span>
                        <span class='flash-time'>{time_ago(article['timestamp'])}</span>
                      </div>
                      <div class='flash-headline-title'>{article['title']}</div>
                      <div class='flash-headline-footer'>
                        <span class='flash-source'>{article['source']}</span>
                        <span class='flash-sentiment' style='background: {sentiment_bg}; color: {sentiment_color};'>{sentiment.upper()}</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
            st.subheader("Risk Alerts")
            for alert in alerts:
                # Determine if alert is good or bad news based on keywords
                bad_keywords = ['risk', 'stress', 'dislocation', 'volatility', 'hawkish', 'shortage', 'blowout', 'dispersion', 'regulatory']
                good_keywords = ['upside', 'growth', 'positive', 'bullish', 'rally', 'surge', 'gain']
                
                alert_text = (alert.get('title', '') + ' ' + alert.get('description', '')).lower()
                is_bad_news = any(keyword in alert_text for keyword in bad_keywords)
                is_good_news = any(keyword in alert_text for keyword in good_keywords) and not is_bad_news
                
                border_class = 'alert-bad' if is_bad_news else ('alert-good' if is_good_news else 'alert-neutral')
                severity_class = f"alert-severity {alert['severity'].lower()}"
                
                st.markdown(
                    f"""
                    <div class='headline-card alert-card {border_class}'>
                      <p class='{severity_class}'>{alert['severity']} alert</p>
                      <div class='headline-title'>{alert['title']}</div>
                      <span class='headline-meta'>{alert['description']}</span>
                      <span class='headline-meta'>{alert['timestamp']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)


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
    st.markdown(f"## {selected['ticker']} — Live Signal Card")
    analysis_cols = st.columns((2.5, 1.5))

    with analysis_cols[0]:
        price_df = pd.DataFrame(company_price_series(selected["ticker"], bias=selected["direction"]))
        change = price_df["price"].iloc[-1] - price_df["price"].iloc[0]
        chart = build_stock_chart(price_df, "#22c55e" if change >= 0 else "#f87171")
        st.altair_chart(chart, use_container_width=True)
        st.caption(f"{selected['ticker']} {change:+.2f} over the sampled window.")

    with analysis_cols[1]:
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
        price_df = pd.DataFrame(company_price_series(selected["ticker"], bias=selected.get("stance")))
        line_color = "#22c55e" if selected.get("stance", "buy").lower() == "buy" else "#f87171"
        price_chart = build_stock_chart(price_df, line_color)
        st.altair_chart(price_chart, use_container_width=True)
        metric_cols = st.columns(3)
        metric_cols[0].metric("Price", f"${snap['price']}", f"{snap['change']:+}")
        metric_cols[1].metric("Volume (M)", f"{snap['volume']}")
        metric_cols[2].metric("Market Cap ($B)", f"{snap['market_cap']}")
        extra_cols = st.columns(3)
        extra_cols[0].metric("P/E", snap["pe"])
        extra_cols[1].metric("Beta", snap["beta"])
        extra_cols[2].metric("Direction", selected["stance"].upper())

    expected_cols = ["ticker", "title", "source", "category", "impact", "stance", "timestamp"]
    table = pd.DataFrame(filtered[:60])
    for col in expected_cols:
        if col not in table.columns:
            table[col] = ""
    table = table[expected_cols]
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
    st.subheader("Global Indices Pulse")
    df = pd.DataFrame(indices)
    bullish = df[df["change"] >= 0].shape[0]
    bearish = df[df["change"] < 0].shape[0]
    avg_change = df["change_pct"].mean()

    summary_cols = st.columns(3)
    for col, (title, value, meta) in zip(
        summary_cols,
        [
            ("Bullish", bullish, "trending higher"),
            ("Bearish", bearish, "trending lower"),
            ("Avg Move", f"{avg_change:+.2f}%", "across basket"),
        ],
    ):
        with col:
            st.markdown(
                f"<div class='metric-card'><h3>{title}</h3><div class='value'>{value}</div><p>{meta}</p></div>",
                unsafe_allow_html=True,
            )

    regions = ["All"] + sorted(df["region"].unique())
    selected_region = st.selectbox("Filter region", regions)
    filtered = df if selected_region == "All" else df[df["region"] == selected_region]

    for row in range(0, len(filtered), 3):
        cols = st.columns(3)
        for col, idx in zip(cols, filtered.iloc[row : row + 3].to_dict("records")):
            trend_class = "bullish" if idx["trend"] == "Bullish" else "bearish"
            sign = "+" if idx["change"] >= 0 else ""
            with col:
                st.markdown(
                    f"""
                    <div class='index-card {trend_class}'>
                        <div class='index-card__header'>
                            <div>
                                <p class='eyebrow'>{idx['region']} · {idx['trend']}</p>
                                <h3>{idx['name']}</h3>
                            </div>
                            <div class='index-chip'>{sign}{idx['change']:.2f} ({sign}{idx['change_pct']:.2f}%)</div>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                spark = (
                    alt.Chart(pd.DataFrame(idx["series"]))
                    .mark_area(
                        line={"color": "#22c55e" if idx["trend"] == "Bullish" else "#f87171"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(
                                    color="#22c55e" if idx["trend"] == "Bullish" else "#f87171",
                                    offset=0,
                                ),
                                alt.GradientStop(color="rgba(15,23,42,0)", offset=1),
                            ],
                        ),
                    )
                    .encode(x=alt.X("step:Q", axis=None), y=alt.Y("value:Q", axis=None))
                    .properties(height=110)
                    .configure_view(strokeWidth=0, fill="#1e293b")
                    .configure(background="#1e293b")
                )
                st.altair_chart(spark, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Movers & Laggards")
    movers_cols = st.columns(2)
    gainers = filtered.sort_values("change_pct", ascending=False).head(5)
    laggards = filtered.sort_values("change_pct").head(5)
    with movers_cols[0]:
        st.markdown("**Top Gainers**")
        for _, row in gainers.iterrows():
            st.markdown(
                f"<div class='mover-row bullish'>{row['name']} · {row['region']} · {row['change_pct']:+.2f}%</div>",
                unsafe_allow_html=True,
            )
    with movers_cols[1]:
        st.markdown("**Top Laggards**")
        for _, row in laggards.iterrows():
            st.markdown(
                f"<div class='mover-row bearish'>{row['name']} · {row['region']} · {row['change_pct']:+.2f}%</div>",
                unsafe_allow_html=True,
            )

    st.markdown("### Region Breakdown")
    region_cols = st.columns(3)
    for col, region in zip(region_cols, df["region"].unique()):
        subset = df[df["region"] == region][["name", "value", "change_pct", "trend"]]
        table_html = subset.to_html(
            classes="indices-table",
            index=False,
            justify="center",
            formatters={
                "value": lambda v: f"{v:,.2f}",
                "change_pct": lambda v: f"{v:+.2f}%",
            },
        )
        with col:
            st.markdown(f"**{region}**", unsafe_allow_html=True)
            st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("### Change Distribution")
    hist = (
        alt.Chart(filtered)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("change_pct:Q", bin=alt.Bin(maxbins=20), title="Change %"),
            y=alt.Y("count()", title="Count"),
            color=alt.condition(
                alt.datum.change_pct > 0,
                alt.value("#10b981"),
                alt.value("#ef4444"),
            ),
        )
        .configure(background="#1e293b")
        .configure_axis(labelColor="#ffffff", titleColor="#ffffff", gridColor="#475569", domainColor="#94a3b8")
    )
    st.altair_chart(hist, use_container_width=True)


def render_portfolio_tab(series, exposures, alert_feed):
    st.subheader("Portfolio Performance (Synthetic)")
    df = pd.DataFrame(series)
    chart = (
        alt.Chart(df)
        .mark_line(color="#60a5fa")
        .encode(x="date:T", y="value:Q")
        .properties(height=300)
        .configure(background="#1e293b")
        .configure_axis(labelColor="#ffffff", titleColor="#ffffff", gridColor="#475569", domainColor="#94a3b8")
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Demo equity curve with random drift.")

    st.subheader("Sector Exposure & PnL")
    exp_df = pd.DataFrame(exposures)
    bar = (
        alt.Chart(exp_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(x="sector:N", y="weight:Q", color=alt.Color("pnl:Q", scale=alt.Scale(scheme="redblue")))
        .configure(background="#1e293b")
        .configure_axis(labelColor="#ffffff", titleColor="#ffffff", gridColor="#475569", domainColor="#94a3b8")
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
        st.rerun()


def main() -> None:
    load_css()
    db.init_db()
    st_autorefresh(interval=5000, key="news-refresh")
    
    # Add page title at the very top
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
            <h1 style="color: #ffffff; font-size: 2.5rem; font-weight: 800; margin: 0;">
                Financial Command Center
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    user = auth_ui.auth_section()
    if not user:
        st.stop()
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    hero_header(user)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    render_inline_copilot()

    st.sidebar.header("Research Copilot")
    for msg in st.session_state.chat_history:
        role = "🧑‍💼" if msg["role"] == "user" else "🤖"
        st.sidebar.markdown(f"<div class='chat-bubble {'chat-user' if role=='🧑‍💼' else 'chat-assistant'}'><strong>{role}</strong>: {msg['content']}</div>", unsafe_allow_html=True)
    sidebar_prompt = st.sidebar.text_input("Ask anything", key="sidebar_prompt")
    if st.sidebar.button("Send", key="sidebar_chat_btn"):
        st.session_state.chat_history.append({"role": "user", "content": sidebar_prompt})
        reply = chat_with_researcher(st.session_state.chat_history, sidebar_prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

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
