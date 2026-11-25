"""StockForge web dashboard (Streamlit + Plotly).

    pip install -r requirements.txt
    streamlit run dashboard.py

Uses the same pipeline as main.py, so numbers match the CLI.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import config
from backtesting.pipeline import run_pipeline
from data.fetch import download_prices
from database.db import create_tables, save_prices, load_prices

st.set_page_config(page_title="StockForge", page_icon="📈", layout="wide")

BUY_ACTIONS = {"BUY", "COVER and BUY", "COVER"}
SELL_ACTIONS = {"SELL", "SHORT", "SELL and SHORT"}
REGIME_COLORS = {"TREND": "rgba(46,160,67,0.10)", "RANGE": "rgba(56,139,253,0.10)",
                 "CRISIS": "rgba(248,81,73,0.15)"}
PCT_KEYS_EXCLUDED = {"sharpe"}


# ---------------------------------------------------------------- data/run
@st.cache_data(show_spinner=False, ttl=3600)
def load_ticker(ticker, start, end):
    create_tables()
    raw = download_prices(ticker, start, end)
    if raw.empty:
        return None
    save_prices(ticker, raw)
    return load_prices(ticker)


@st.cache_data(show_spinner=False)
def run_one(ticker, eval_start, capital, fee, borrow, short,
            adx_trend, adx_range, vol_cap, strategy_params):
    # regime.py reads config.X at call time, so these overrides take effect.
    config.ADX_TREND, config.ADX_RANGE, config.VOL_CAP = adx_trend, adx_range, vol_cap
    prices = load_ticker(ticker, config.START_DATE, config.END_DATE)
    if prices is None:
        return None
    return run_pipeline(prices, eval_start, capital, fee, borrow, short, strategy_params)


def fmt(key, value):
    return f"{value:.2f}" if key in PCT_KEYS_EXCLUDED else f"{value:.2%}"


# ----------------------------------------------------------------- figures
def regime_spans(regime):
    runs = (regime != regime.shift()).cumsum()
    for _, chunk in regime.groupby(runs):
        if chunk.iloc[0] in REGIME_COLORS:
            yield chunk.index[0], chunk.index[-1], chunk.iloc[0]


def detail_figure(res, actions, show_regimes):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.55, 0.28, 0.17],
                        subplot_titles=("Price & actions", "Equity vs buy & hold", "Drawdown"))
    fig.add_trace(go.Candlestick(x=res.index, open=res["open"], high=res["high"],
                                 low=res["low"], close=res["close"], name="Price",
                                 showlegend=False), row=1, col=1)
    if len(actions):
        for names, symbol, color, label in (
                (BUY_ACTIONS, "triangle-up", "#2ea043", "Buy / cover"),
                (SELL_ACTIONS, "triangle-down", "#f85149", "Sell / short")):
            a = actions[actions["action"].isin(names)]
            fig.add_trace(go.Scatter(
                x=a["date"], y=a["price"], mode="markers", name=label,
                marker=dict(symbol=symbol, size=11, color=color, line=dict(width=1, color="white")),
                text=a["action"] + " (" + a["regime"].astype(str) + ")",
                hovertemplate="%{x|%Y-%m-%d}<br>%{text}<br>%{y:.2f}<extra></extra>"),
                row=1, col=1)
    fig.add_trace(go.Scatter(x=res.index, y=res["equity"], name="Strategy"), row=2, col=1)
    fig.add_trace(go.Scatter(x=res.index, y=res["buy_hold"], name="Buy & hold",
                             line=dict(dash="dot")), row=2, col=1)
    for col, name in (("equity", "Strategy"), ("buy_hold", "Buy & hold")):
        dd = res[col] / res[col].cummax() - 1
        fig.add_trace(go.Scatter(x=res.index, y=dd, name=f"{name} DD", fill="tozeroy",
                                 showlegend=False, opacity=0.5), row=3, col=1)
    if show_regimes:
        for x0, x1, reg in regime_spans(res["regime"]):
            fig.add_vrect(x0=x0, x1=x1, fillcolor=REGIME_COLORS[reg], line_width=0,
                          layer="below", row=1, col=1)
    fig.update_layout(height=820, hovermode="x unified", xaxis_rangeslider_visible=False,
                      margin=dict(t=40, b=10), legend=dict(orientation="h", y=1.04))
    fig.update_yaxes(tickformat=".0%", row=3, col=1)
    return fig


def overview_figure(out):
    fig = go.Figure()
    for t, o in out.items():
        s = o["result"]["equity"]
        fig.add_trace(go.Scatter(x=s.index, y=100 * s / s.iloc[0], name=t))
    fig.update_layout(height=430, hovermode="x unified", yaxis_title="Strategy equity, rebased to 100")
    return fig


def compare_figure(out):
    tickers = list(out)
    fig = go.Figure([
        go.Bar(name="Strategy", x=tickers, y=[out[t]["summary"]["total_return"] for t in tickers]),
        go.Bar(name="Buy & hold", x=tickers, y=[out[t]["summary"]["buy_hold_return"] for t in tickers]),
    ])
    fig.update_layout(barmode="group", height=340, yaxis_tickformat=".0%")
    return fig


# ----------------------------------------------------------------- sidebar
st.sidebar.title("📈 StockForge")
picked = st.sidebar.multiselect("Tickers", config.TICKERS, default=config.TICKERS)
extra = st.sidebar.text_input("Extra tickers (comma separated)", placeholder="TCS.NS, NVDA")
tickers = picked + [t.strip().upper() for t in extra.split(",")
                    if t.strip() and t.strip().upper() not in picked]

eval_start = st.sidebar.date_input("Scored from", pd.to_datetime(config.EVAL_START).date()).isoformat()
capital = st.sidebar.number_input("Starting capital", 1000.0, value=float(config.INITIAL_CAPITAL), step=1000.0)
fee = st.sidebar.number_input("Fee rate", 0.0, 0.05, float(config.FEE_RATE), step=0.0005, format="%.4f")
short = st.sidebar.toggle("Allow shorting", bool(config.ALLOW_SHORT))
borrow = st.sidebar.number_input("Short borrow rate", 0.0, 1.0, float(config.SHORT_BORROW_RATE),
                                 step=0.005, format="%.3f", disabled=not short)

with st.sidebar.expander("Regime thresholds"):
    adx_trend = st.slider("ADX trend", 10, 50, int(config.ADX_TREND))
    adx_range = st.slider("ADX range", 5, 40, int(config.ADX_RANGE))
    vol_cap = st.slider("Volatility cap (percentile)", 0.5, 1.0, float(config.VOL_CAP), 0.01)
with st.sidebar.expander("Strategy parameters"):
    entry_w = st.slider("Breakout entry window", 5, 100, 20)
    exit_w = st.slider("Breakout exit window", 3, 60, 10)
    rsi_entry = st.slider("Mean-reversion RSI entry", 1, 30, 10)
    mr_exit = st.slider("Mean-reversion exit window", 2, 20, 5)
strategy_params = {"trend_breakout": {"entry_window": entry_w, "exit_window": exit_w},
                   "mean_reversion": {"rsi_entry": rsi_entry, "exit_window": mr_exit}}
run = st.sidebar.button("Run backtest", type="primary", use_container_width=True)

# --------------------------------------------------------------------- run
st.title("StockForge Dashboard")
if run or "out" not in st.session_state:
    out = {}
    with st.spinner("Running backtests..."):
        for t in tickers:
            try:
                r = run_one(t, eval_start, capital, fee, borrow, short,
                            adx_trend, adx_range, vol_cap, strategy_params)
                if r is None:
                    st.warning(f"{t}: no data found, skipped.")
                else:
                    out[t] = r
            except Exception as e:
                st.error(f"{t}: {e}")
    st.session_state["out"] = out
out = st.session_state["out"]

if not out:
    st.info("Pick tickers in the sidebar and press **Run backtest**.")
    st.stop()

tab_over, tab_detail, tab_trades = st.tabs(["Overview", "Ticker detail", "Trades & export"])

with tab_over:
    st.subheader("Summary")
    st.dataframe(pd.DataFrame({t: {k: fmt(k, v) for k, v in o["summary"].items()}
                               for t, o in out.items()}).T, use_container_width=True)
    left, right = st.columns(2)
    left.plotly_chart(overview_figure(out), use_container_width=True)
    right.plotly_chart(compare_figure(out), use_container_width=True)

with tab_detail:
    t = st.selectbox("Ticker", list(out))
    o = out[t]
    for c, (k, v) in zip(st.columns(len(o["summary"])), o["summary"].items()):
        c.metric(k.replace("_", " "), fmt(k, v))
    show_regimes = st.checkbox("Shade regimes (green trend, blue range, red crisis)", True)
    st.plotly_chart(detail_figure(o["result"], o["actions"], show_regimes), use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.markdown("**Strategy return before fees**")
        contrib = pd.Series(o["contrib"])
        st.plotly_chart(go.Figure(go.Bar(x=contrib.index, y=contrib.values))
                        .update_layout(height=280, yaxis_tickformat=".0%"), use_container_width=True)
        st.markdown("**Trade statistics**")
        st.dataframe(pd.Series(o["stats"]).round(3).rename("value"), use_container_width=True)
    with right:
        st.markdown("**Regime table** (stock = what the stock did on those days)")
        st.dataframe(o["regimes"].round(4), use_container_width=True)
        st.markdown("**Year by year**")
        st.dataframe(o["yearly"].round(3), use_container_width=True)

with tab_trades:
    t = st.selectbox("Ticker ", list(out), key="trade_ticker")
    o = out[t]
    trades = o["trades"]
    if len(trades):
        st.markdown("**By side (return per trade)**")
        st.dataframe(trades.groupby("side")["return"]
                     .agg(trades="count", avg="mean", best="max", worst="min").round(4),
                     use_container_width=True)
    st.markdown("**Trade log**")
    st.dataframe(trades, use_container_width=True, hide_index=True)
    st.markdown("**Action log**")
    st.dataframe(o["actions"], use_container_width=True, hide_index=True)
    d1, d2 = st.columns(2)
    d1.download_button("Download trades CSV", trades.to_csv(index=False), f"{t}_trades.csv", "text/csv")
    d2.download_button("Download daily CSV", o["result"].to_csv(), f"{t}_daily.csv", "text/csv")
