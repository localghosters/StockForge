# StockForge 📈   &nbsp;   [![SecretShield](https://github.com/localghosters/StockForge/actions/workflows/secretshield.yml/badge.svg)](https://github.com/localghosters/StockForge/actions/workflows/secretshield.yml)

## 🚧 Under Development

> **Note:** We're not trying to build a highly advanced quant trading algorithm right away. StockForge will start as a basic backtesting model, and we'll gradually scale it up over time.


## View in action

![TradingView](images/SDGW.png)


> NOTICE: Go to images folder for full preview details

## Web dashboard

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

Interactive candlestick chart with buy/sell markers and regime shading, equity vs buy & hold,
drawdown, per-ticker diagnostics, trade/action logs and CSV export. Tickers, fees, shorting,
regime thresholds and strategy parameters are adjustable from the sidebar. It runs the same
pipeline as `main.py` (`backtesting/pipeline.py`).

## Dependencies

StockForge uses the following open-source Python libraries:

- [yfinance](https://github.com/ranaroussi/yfinance)
- [pandas](https://github.com/pandas-dev/pandas)
- [matplotlib](https://github.com/matplotlib/matplotlib)

These projects are distributed under their respective licenses.

> for full list check requirements.txt

