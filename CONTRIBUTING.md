# Contributing to StockForge 📈

Thanks for your interest in contributing to StockForge!

StockForge is an open-source quant finance project focused on experimenting with stock-market strategies, historical data, backtesting, indicators, and performance analysis.

The project is built in Python and currently uses:

* yfinance for market data
* pandas for data handling and analysis
* matplotlib for visualizations

StockForge is also a place to experiment, test ideas, find bugs, and learn from each other. You don't need to be a quant expert to contribute.

## What You Can Contribute

There are many ways to contribute, including:

* Trading strategies
* Backtesting improvements
* Historical-data analysis
* Indicators and signals
* Performance metrics
* Data handling
* Visualizations
* Bug fixes
* Tests
* Documentation
* Code cleanup and improvements
* Ideas for future features

If you have an interesting approach to testing or analyzing a strategy, feel free to share it.

## Before You Start

For larger changes, especially new strategies or changes to the project's overall direction, opening an issue first is recommended so the idea can be discussed before significant work is done.

Small fixes, bug fixes, documentation changes, and other straightforward improvements can usually go directly into a pull request.

## Getting Started

1. Fork the repository.
2. Clone your fork.
3. Create a branch for your changes.
4. Install the project's dependencies.
5. Make your changes.
6. Test your changes with historical data.
7. Run any relevant tests.
8. Open a pull request with a clear description of what you changed and why.

For project setup and dependency installation, see the main `README.md`.

## Pull Requests

When submitting a pull request:

* Keep the code reasonably simple and readable.
* Explain what you changed and why.
* Test your changes before submitting.
* Include relevant results, examples, or screenshots when useful.
* Avoid unrelated changes in the same pull request.

Please avoid submitting strategies that only look good because of accidental overfitting or data leakage. Backtesting results should be interpreted carefully.

## Adding Trading Strategies

When adding a new strategy, try to include:

* A short explanation of how it works
* The data it requires
* The assumptions it makes
* How it is backtested
* Relevant performance results or observations

Strategies should be tested on appropriate historical data and should avoid using information that would not have been available at the time of the simulated trade.

Historical backtest results are **not guarantees of future performance**.

## Issues

Found a bug or have an idea?

Open an issue and include as much useful information as possible, such as:

* What happened
* What you expected to happen
* Steps to reproduce the issue
* Relevant code or output
* Python version and environment, if relevant

For feature ideas, explain what you think the feature would add to StockForge and, if possible, how you think it could work.

## Keep It Practical

StockForge is intended to be an experimental and educational project.

Contributions don't need to be perfect or overly complicated. Simple, understandable implementations are preferred over unnecessary complexity.

Different approaches are welcome, especially when they can be tested and compared using data.

## Code of Conduct

Be respectful, constructive, and open to different approaches.

Criticism of code, results, and strategies is welcome. Personal attacks, harassment, or disrespect toward other contributors are not.

Thanks for helping build StockForge! 🚀
