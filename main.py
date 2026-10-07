from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.config import Config
from app.database.models import DatabaseManager, Product, PriceHistory
from app.scheduler.job_manager import get_scheduler
from app.scraper.scraper import ProductScraper

# ── Page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Price Tracker Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

logger = logging.getLogger(__name__)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    /* ── Hero gradient header ── */
    .hero-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2.5rem 2rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(130,80,255,0.35), transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.6);
        font-size: 1rem;
        margin-top: 0.4rem;
        font-weight: 300;
    }

    /* ── Metric cards ── */
    .metric-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(130,80,255,0.2);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(130,80,255,0.15);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #a78bfa;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.25rem;
    }

    /* ── Product cards ── */
    .product-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(130,80,255,0.15);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }
    .product-card:hover { border-color: rgba(130,80,255,0.5); }
    .product-name {
        font-size: 1rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    .product-price {
        font-size: 1.5rem;
        font-weight: 700;
        color: #34d399;
        font-family: 'JetBrains Mono', monospace;
    }
    .product-price-na {
        font-size: 1.1rem;
        color: #94a3b8;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-green  { background:#065f46; color:#34d399; }
    .badge-red    { background:#7f1d1d; color:#fca5a5; }
    .badge-yellow { background:#78350f; color:#fbbf24; }
    .site-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        background: rgba(130,80,255,0.15);
        color: #a78bfa;
        margin-right: 6px;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 1.5rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(130,80,255,0.3);
    }

    /* ── Alert cards ── */
    .alert-row {
        background: rgba(255,200,50,0.05);
        border: 1px solid rgba(255,200,50,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: rgba(255,255,255,0.7);
    }

    /* ── Success / error banners ── */
    .banner-success {
        background: rgba(52,211,153,0.1);
        border: 1px solid #34d399;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #34d399;
        margin: 0.5rem 0;
    }
    .banner-error {
        background: rgba(239,68,68,0.1);
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #ef4444;
        margin: 0.5rem 0;
    }

    /* ── Input overrides ── */
    .stTextInput input, .stNumberInput input {
        background: #1e1b4b !important;
        border: 1px solid rgba(130,80,255,0.3) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: opacity 0.2s, transform 0.15s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    /* ── Table styling ── */
    .dataframe { border-radius: 10px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state helpers ─────────────────────────────────────────────────────


def _init_state() -> None:
    """Initialise persistent Streamlit session-state variables."""
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager()
    if "scraper" not in st.session_state:
        st.session_state.scraper = ProductScraper()
    if "scheduler" not in st.session_state:
        st.session_state.scheduler = get_scheduler(st.session_state.db)
    if "refresh_trigger" not in st.session_state:
        st.session_state.refresh_trigger = 0


def _db() -> DatabaseManager:
    return st.session_state.db


def _scraper() -> ProductScraper:
    return st.session_state.scraper


def _scheduler():
    return st.session_state.scheduler


# ── Helpers ───────────────────────────────────────────────────────────────────


def _availability_badge(avail: Optional[str]) -> str:
    if not avail:
        return '<span class="badge badge-yellow">Unknown</span>'
    low = avail.lower()
    if "in stock" in low or "available" in low:
        return '<span class="badge badge-green">✓ In Stock</span>'
    if "out" in low:
        return '<span class="badge badge-red">✗ Out of Stock</span>'
    return f'<span class="badge badge-yellow">{avail[:30]}</span>'


def _fmt_price(price: Optional[float], currency: str = "₹") -> str:
    if price is None:
        return "N/A"
    return f"{currency}{price:,.0f}"


def _price_history_df(product_id: int) -> pd.DataFrame:
    """Return a cleaned pandas DataFrame of price history."""
    records = _db().get_price_history(product_id)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(
        [
            {
                "Date": r.checked_at,
                "Price": r.price,
                "Availability": r.availability,
            }
            for r in records
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.dropna(subset=["Price"]).sort_values("Date")
    return df


# ── Page sections ─────────────────────────────────────────────────────────────


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">📊 Price Tracker Pro</div>
            <div class="hero-subtitle">
                Monitor prices across Amazon, Flipkart & more — get alerted the instant prices drop.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(products: List[Product]) -> None:
    prices = [p.current_price for p in products if p.current_price]
    active_alerts = len(_db().get_active_alerts())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{len(products)}</div>'
            f'<div class="metric-label">Products Tracked</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{active_alerts}</div>'
            f'<div class="metric-label">Active Alerts</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        min_p = f"₹{min(prices):,.0f}" if prices else "—"
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{min_p}</div>'
            f'<div class="metric-label">Lowest Price</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        sched = _scheduler()
        status = "🟢 Running" if sched.is_running else "🔴 Stopped"
        st.markdown(
            f'<div class="metric-card"><div class="metric-value" style="font-size:1.2rem">{status}</div>'
            f'<div class="metric-label">Auto-Checker</div></div>',
            unsafe_allow_html=True,
        )


def render_add_product() -> None:
    """Form to add a new product URL for tracking."""
    st.markdown('<div class="section-header">➕ Track a New Product</div>', unsafe_allow_html=True)

    with st.form("add_product_form", clear_on_submit=True):
        url = st.text_input(
            "Product URL",
            placeholder="https://www.amazon.in/dp/... or https://www.flipkart.com/...",
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            alert_price = st.number_input(
                "Alert me when price drops below (₹) — optional",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )
        with col2:
            alert_email = st.text_input(
                "Email for alerts (optional)",
                placeholder="you@example.com",
            )
        submitted = st.form_submit_button("🔍 Scrape & Track", use_container_width=True)

    if submitted:
        if not url or not url.startswith("http"):
            st.error("Please enter a valid URL starting with http:// or https://")
            return

        with st.spinner("Scraping product details…"):
            result = _scraper().scrape(url)

        if not result.success:
            st.markdown(
                f'<div class="banner-error">❌ Scrape failed: {result.error or "Unknown error"}</div>',
                unsafe_allow_html=True,
            )
            return

        product = _db().add_product(url=url, site=result.site)
        _db().update_product(
            product.id,
            name=result.name,
            current_price=result.price,
            availability=result.availability,
            image_url=result.image_url,
            last_checked=datetime.utcnow(),
        )
        _db().record_price(product.id, result.price, result.availability)

        if alert_price > 0:
            _db().add_alert(product.id, alert_price, alert_email)

        st.markdown(
            f'<div class="banner-success">✅ Now tracking: <strong>{result.name[:80]}</strong>'
            f" — Current price: {_fmt_price(result.price)}</div>",
            unsafe_allow_html=True,
        )
        st.session_state.refresh_trigger += 1
        st.rerun()


def render_product_list(products: List[Product]) -> None:
    """Display tracked products as cards with inline actions."""
    st.markdown('<div class="section-header">🛒 Tracked Products</div>', unsafe_allow_html=True)

    if not products:
        st.info("No products being tracked yet. Add one above!")
        return

    for product in products:
        with st.container():
            site_tag = f'<span class="site-tag">{product.site or "web"}</span>'
            avail_badge = _availability_badge(product.availability)
            price_html = (
                f'<span class="product-price">{_fmt_price(product.current_price)}</span>'
                if product.current_price
                else '<span class="product-price-na">Price unavailable</span>'
            )
            last_checked = (
                product.last_checked.strftime("%d %b %Y, %H:%M")
                if product.last_checked
                else "Never"
            )

            st.markdown(
                f"""
                <div class="product-card">
                    <div>{site_tag}{avail_badge}</div>
                    <div class="product-name">{product.name or product.url}</div>
                    <div style="display:flex;align-items:baseline;gap:1.5rem;margin-top:0.5rem">
                        {price_html}
                        <span style="color:#64748b;font-size:0.8rem">Checked: {last_checked}</span>
                    </div>
                    <div style="font-size:0.75rem;color:#475569;margin-top:0.4rem;
                                overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        🔗 {product.url}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("📈 History", key=f"hist_{product.id}"):
                    st.session_state[f"show_chart_{product.id}"] = (
                        not st.session_state.get(f"show_chart_{product.id}", False)
                    )
            with col2:
                if st.button("🔄 Refresh", key=f"refresh_{product.id}"):
                    with st.spinner("Scraping…"):
                        r = _scraper().scrape(product.url)
                    if r.success:
                        _db().update_product(
                            product.id,
                            name=r.name,
                            current_price=r.price,
                            availability=r.availability,
                            last_checked=datetime.utcnow(),
                        )
                        _db().record_price(product.id, r.price, r.availability)
                        st.success(f"Updated: {_fmt_price(r.price)}")
                        st.rerun()
                    else:
                        st.error(f"Scrape failed: {r.error}")
            with col3:
                if st.button("🔔 Set Alert", key=f"alert_{product.id}"):
                    st.session_state[f"show_alert_{product.id}"] = (
                        not st.session_state.get(f"show_alert_{product.id}", False)
                    )
            with col4:
                if st.button("🗑 Remove", key=f"del_{product.id}"):
                    _db().delete_product(product.id)
                    st.rerun()

            # ── Alert sub-form ────────────────────────────────────────────
            if st.session_state.get(f"show_alert_{product.id}", False):
                with st.form(f"alert_form_{product.id}"):
                    t_price = st.number_input(
                        "Alert threshold (₹)",
                        min_value=1.0,
                        value=float(product.current_price or 1000),
                        key=f"thresh_{product.id}",
                    )
                    t_email = st.text_input("Email (optional)", key=f"email_{product.id}")
                    if st.form_submit_button("Save Alert"):
                        _db().add_alert(product.id, t_price, t_email)
                        st.success("Alert saved!")
                        st.session_state[f"show_alert_{product.id}"] = False
                        st.rerun()

            # ── Price history chart ───────────────────────────────────────
            if st.session_state.get(f"show_chart_{product.id}", False):
                render_price_chart(product)


def render_price_chart(product: Product) -> None:
    """Render an interactive Plotly price-history chart for a single product."""
    df = _price_history_df(product.id)

    if df.empty:
        st.info("No price history yet. Trigger a manual refresh first.")
        return

    fig = go.Figure()

    # Price area
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Price"],
            mode="lines+markers",
            name="Price",
            line=dict(color="#a78bfa", width=2.5),
            marker=dict(size=6, color="#7c3aed"),
            fill="tozeroy",
            fillcolor="rgba(124,58,237,0.08)",
            hovertemplate="<b>%{x|%d %b %Y %H:%M}</b><br>₹%{y:,.0f}<extra></extra>",
        )
    )

    # Min/max annotations
    if len(df) > 1:
        min_row = df.loc[df["Price"].idxmin()]
        max_row = df.loc[df["Price"].idxmax()]
        for row, color, label in [
            (min_row, "#34d399", "Low"),
            (max_row, "#f87171", "High"),
        ]:
            fig.add_annotation(
                x=row["Date"],
                y=row["Price"],
                text=f"{label}: ₹{row['Price']:,.0f}",
                showarrow=True,
                arrowhead=2,
                font=dict(color=color, size=11),
                bgcolor="rgba(0,0,0,0.6)",
                bordercolor=color,
                borderwidth=1,
                borderpad=4,
            )

    fig.update_layout(
        title=dict(
            text=f"Price History — {(product.name or '')[:60]}",
            font=dict(size=14, color="#e2e8f0"),
        ),
        paper_bgcolor="rgba(15,12,41,0.0)",
        plot_bgcolor="rgba(15,12,41,0.0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(130,80,255,0.1)",
            tickformat="%d %b",
        ),
        yaxis=dict(
            title="Price (₹)",
            showgrid=True,
            gridcolor="rgba(130,80,255,0.1)",
            tickformat=",.0f",
        ),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=50, b=0),
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Stats table
    stats = pd.DataFrame(
        {
            "Metric": ["Current", "Minimum", "Maximum", "Average", "Data Points"],
            "Value": [
                _fmt_price(df["Price"].iloc[-1]),
                _fmt_price(df["Price"].min()),
                _fmt_price(df["Price"].max()),
                _fmt_price(df["Price"].mean()),
                str(len(df)),
            ],
        }
    )
    st.dataframe(stats, hide_index=True, use_container_width=True)


def render_alerts_panel() -> None:
    """Show and manage all configured alerts."""
    st.markdown('<div class="section-header">🔔 Price Alerts</div>', unsafe_allow_html=True)
    alerts = _db().get_active_alerts()

    if not alerts:
        st.info("No active alerts. Set an alert from any product card above.")
        return

    for alert in alerts:
        product = _db().get_product_by_id(alert.product_id)
        if not product:
            continue

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""
                <div class="alert-row">
                    <div>
                        <span style="color:#fbbf24;font-weight:600;">🔔</span>
                        <span style="color:#e2e8f0;margin-left:8px;">
                            {(product.name or product.url)[:60]}
                        </span><br>
                        <span style="color:#94a3b8;font-size:0.8rem;">
                            Alert when ≤ <strong style="color:#34d399;">
                            ₹{alert.threshold_price:,.0f}</strong>
                            &nbsp;|&nbsp; Current: <strong>
                            {_fmt_price(product.current_price)}</strong>
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Delete", key=f"del_alert_{alert.id}"):
                _db().delete_alert(alert.id)
                st.rerun()


def render_overview_chart(products: List[Product]) -> None:
    """Bar chart comparing current prices across all tracked products."""
    data = [
        {"Product": (p.name or p.url)[:35], "Price": p.current_price, "Site": p.site}
        for p in products
        if p.current_price
    ]
    if not data:
        return

    df = pd.DataFrame(data).sort_values("Price")
    fig = px.bar(
        df,
        x="Price",
        y="Product",
        orientation="h",
        color="Price",
        color_continuous_scale=["#7c3aed", "#34d399"],
        labels={"Price": "Current Price (₹)"},
        title="Current Prices — All Tracked Products",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=50, b=0),
        height=max(250, len(data) * 45),
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_sidebar() -> None:
    """Sidebar: scheduler controls and app info."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:1rem 0 0.5rem;">
                <span style="font-size:2.5rem;">📊</span>
                <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;margin-top:0.3rem;">
                    Price Tracker Pro
                </div>
                <div style="color:rgba(255,255,255,0.4);font-size:0.75rem;">v1.0.0</div>
            </div>
            <hr style="border-color:rgba(130,80,255,0.2);">
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⏱ Auto Scheduler")
        sched = _scheduler()

        if sched.is_running:
            st.success("Scheduler is running")
            next_r = sched.next_run
            if next_r:
                delta = next_r.replace(tzinfo=None) - datetime.utcnow()
                mins = max(0, int(delta.total_seconds() // 60))
                st.caption(f"Next check in ~{mins} min")
            if st.button("⏸ Stop Scheduler", use_container_width=True):
                sched.stop()
                st.rerun()
        else:
            st.warning("Scheduler is stopped")
            if st.button("▶ Start Scheduler", use_container_width=True):
                sched.start()
                st.rerun()

        interval = st.slider(
            "Check interval (minutes)",
            min_value=5,
            max_value=240,
            value=sched.interval_minutes,
            step=5,
        )
        if interval != sched.interval_minutes:
            sched.update_interval(interval)

        st.markdown("---")
        st.markdown("### 🔄 Manual Check")
        if st.button("Check All Prices Now", use_container_width=True):
            with st.spinner("Checking all products…"):
                summary = sched.run_price_check()
            st.success(
                f"Done! Checked: {summary['checked']} | "
                f"Updated: {summary['updated']} | "
                f"Alerts: {summary['alerts_fired']}"
            )
            st.rerun()

        st.markdown("---")
        st.markdown("### ℹ About")
        st.markdown(
            """
            <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;line-height:1.6;">
            Supported sites:<br>
            🛒 Amazon India<br>
            🛍 Flipkart<br>
            🌐 Generic (OG/JSON-LD)<br><br>
            Data stored in SQLite.<br>
            Set <code>EMAIL_ENABLED=true</code><br>in .env for email alerts.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── App entry point ───────────────────────────────────────────────────────────


def main() -> None:
    _init_state()
    render_sidebar()

    render_hero()

    products = _db().get_all_products()
    render_metrics(products)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🛒 Products", "📈 Price Charts", "🔔 Alerts"])

    with tab1:
        render_add_product()
        st.markdown("---")
        render_product_list(products)

    with tab2:
        if not products:
            st.info("Track some products first to see their price history charts here.")
        else:
            render_overview_chart(products)
            st.markdown("---")
            selected = st.selectbox(
                "Select product for detailed history",
                options=products,
                format_func=lambda p: (p.name or p.url)[:70],
            )
            if selected:
                render_price_chart(selected)

    with tab3:
        render_alerts_panel()


if __name__ == "__main__":
    main()
