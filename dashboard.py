"""StockForge web dashboard.

Run from the repo root:
    pip install streamlit plotly
    streamlit run dashboard.py

It reuses the same pipeline as main.py (download -> save/load -> signals ->
backtest -> diagnostics), so results match the CLI.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from data.fetch import download_prices
from database.db import create_tables, save_prices, load_prices
from strategies.selector import build_signal
from backtesting.engine import run_backtest
from portfolio.metrics import summary
from portfolio.diagnostics import (
    trade_log, action_log, trade_stats, regime_table,
    strategy_contribution, yearly_table,
)

st.set_page_config(page_title="StockForge", page_icon="📈", layout="wide")


# ---------------------------------------------------------------- pipeline
@st.cache_data(show_spinner=False)
def run_one(ticker, start, end, eval_start, capital, fee, borrow, short,
            adx_trend, adx_range, vol_cap):
    # Thresholds live in config; these overrides only take effect if the
    # strategy modules read config.X at call time (not `from config import X`).
    config.ADX_TREND, config.ADX_RANGE, config.VOL_CAP = adx_trend, adx_range, vol_cap

    create_tables()
    raw = download_prices(ticker, start, end)
    if raw.empty:
        return None
    save_prices(ticker, raw)
    prices = load_prices(ticker)

    signals = build_signal(prices, allow_short=short).loc[eval_start:]
    result = run_backtest(signals, capital, fee, borrow)
    trades = trade_log(result)
    return {
        "result": result,
        "trades": trades,
        "actions": action_log(result),
        "summary": summary(result),
        "stats": trade_stats(trades, result, fee),
        "regimes": regime_table(result, fee),
        "contrib": strategy_contribution(result),
        "yearly": yearly_table(result),
    }


def fmt_summary(d):
    return {k: (f"{v:.2f}" if k == "sharpe" else f"{v:.2%}") for k, v in d.items()}


def equity_columns(result):
    """Best-effort: find equity-curve columns without knowing the engine's schema."""
    hits = [c for c in result.columns
            if any(w in str(c).lower() for w in ("equity", "cumulative", "cum_", "portfolio"))]
    return hits or list(result.select_dtypes("number").columns)


# ----------------------------------------------------------------- sidebar
st.sidebar.title("📈 StockForge")
tickers = st.sidebar.multiselect(
    "Tickers", sorted(set(config.TICKERS) | set(st.session_state.get("extra", []))),
    default=list(config.TICKERS))
extra = st.sidebar.text_input("Add ticker", placeholder="e.g. RELIANCE.NS").strip().upper()
if extra:
    st.session_state.setdefault("extra", [])
    if extra not in st.session_state["extra"] and extra not in tickers:
        tickers.append(extra)

eval_start = st.sidebar.date_input(
    "Scored from", pd.to_datetime(config.EVAL_START).date()).isoformat()
capital = st.sidebar.number_input("Starting capital", 1000.0, value=float(config.INITIAL_CAPITAL), step=1000.0)
fee = st.sidebar.number_input("Fee rate", 0.0, 0.05, float(config.FEE_RATE), step=0.0005, format="%.4f")
short = st.sidebar.toggle("Allow shorting", bool(config.ALLOW_SHORT))
borrow = st.sidebar.number_input("Short borrow rate", 0.0, 1.0, float(config.SHORT_BORROW_RATE), step=0.005,
                                 format="%.3f", disabled=not short)
with st.sidebar.expander("Strategy thresholds"):
    adx_trend = st.slider("ADX trend", 10.0, 50.0, float(config.ADX_TREND))
    adx_range = st.slider("ADX range", 5.0, 40.0, float(config.ADX_RANGE))
    vol_cap = st.number_input("Volatility cap", 0.0, 10.0, float(config.VOL_CAP), step=0.05)
run = st.sidebar.button("Run backtest", type="primary", use_container_width=True)

# --------------------------------------------------------------------- run
st.title("StockForge Dashboard")
if run or "out" not in st.session_state:
    out = {}
    with st.spinner("Running backtests..."):
        for t in tickers:
            try:
                r = run_one(t, config.START_DATE, config.END_DATE, eval_start, capital, fee,
                            borrow, short, adx_trend, adx_range, vol_cap)
                if r is None:
                    st.warning(f"{t}: no data found, skipped.")
                else:
                    out[t] = r
            except Exception as e:  # keep one bad ticker from killing the page
                st.error(f"{t}: {e}")
    st.session_state["out"] = out
out = st.session_state["out"]

if not out:
    st.info("Pick tickers in the sidebar and press **Run backtest**.")
    st.stop()

tab_over, tab_detail, tab_trades = st.tabs(["Overview", "Ticker detail", "Trades & export"])

# ---------------------------------------------------------------- overview
with tab_over:
    st.subheader("Summary")
    st.dataframe(pd.DataFrame({t: fmt_summary(o["summary"]) for t, o in out.items()}).T,
                 use_container_width=True)

    st.subheader("Equity curves (rebased to 100)")
    fig = go.Figure()
    for t, o in out.items():
        res = o["result"]
        col = equity_columns(res)[0]
        s = res[col].dropna()
        fig.add_trace(go.Scatter(x=s.index, y=100 * s / s.iloc[0], name=f"{t} ({col})"))
    fig.update_layout(height=450, hovermode="x unified", yaxis_title="Rebased")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------ detail
with tab_detail:
    t = st.selectbox("Ticker", list(out))
    o = out[t]
    res = o["result"]

    cols = st.columns(len(o["summary"]))
    for c, (k, v) in zip(cols, fmt_summary(o["summary"]).items()):
        c.metric(k, v)

    chosen = st.multiselect("Series to plot", list(res.select_dtypes("number").columns),
                            default=equity_columns(res)[:3])
    fig = go.Figure([go.Scatter(x=res.index, y=res[c], name=str(c)) for c in chosen])
    fig.update_layout(height=420, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.markdown("**Strategy return before fees**")
        contrib = pd.Series(o["contrib"])
        st.plotly_chart(go.Figure(go.Bar(x=contrib.index, y=contrib.values)).update_layout(height=300),
                        use_container_width=True)
        st.markdown("**Trade statistics**")
        st.dataframe(pd.Series(o["stats"]).round(3).rename("value"), use_container_width=True)
    with right:
        st.markdown("**Regime table**")
        st.dataframe(o["regimes"].round(4), use_container_width=True)
        st.markdown("**Year by year**")
        st.dataframe(o["yearly"].round(3), use_container_width=True)

    st.markdown("**Latest actions**")
    st.dataframe(o["actions"].tail(20), use_container_width=True, hide_index=True)

# ------------------------------------------------------------------ trades
with tab_trades:
    t = st.selectbox("Ticker ", list(out), key="trade_ticker")
    o = out[t]
    trades = o["trades"]
    if len(trades) and "side" in trades:
        st.markdown("**By side (return per trade)**")
        st.dataframe(trades.groupby("side")["return"]
                     .agg(trades="count", avg="mean", best="max", worst="min").round(4),
                     use_container_width=True)
    st.markdown("**Trade log**")
    st.dataframe(trades, use_container_width=True, hide_index=True)

    d1, d2 = st.columns(2)
    d1.download_button("Download trades CSV", trades.to_csv(index=False),
                       f"{t}_trades.csv", "text/csv")
    d2.download_button("Download daily CSV", o["result"].to_csv(),
                       f"{t}_daily.csv", "text/csv")
