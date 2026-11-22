import matplotlib.pyplot as plt

STYLES = {
    "BUY": ("green", "^"),
    "SELL": ("orange", "v"),
    "SHORT": ("red", "v"),
    "COVER": ("blue", "^"),
}


def plot_overview(results, save_path=None):
    n = len(results)
    cols = 2 if n <= 4 else 4
    rows = -(-n // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 3.2 * rows), squeeze=False)

    for ax, (ticker, df) in zip(axes.flat, results.items()):
        ax.plot(df.index, df["equity"], label="Strategy")
        ax.plot(df.index, df["buy_hold"], label="Buy and hold")
        ax.set_title(ticker)
        ax.tick_params(labelsize=8)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")

    axes.flat[0].legend(fontsize=8)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path)
    return fig


def plot_detail(df, ticker, actions):
    fig, (top, bottom) = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True,
        gridspec_kw={"height_ratios": [3, 2]},
    )

    top.plot(df.index, df["close"], color="grey", linewidth=1)
    seen = set()
    for _, row in actions.iterrows():
        for part in row["action"].split(" and "):
            if part in STYLES:
                color, marker = STYLES[part]
                top.scatter(row["date"], row["price"], color=color, marker=marker,
                            s=45, zorder=3, label=part if part not in seen else None)
                seen.add(part)
    top.set_title(f"{ticker}: price and decisions")
    if seen:
        top.legend(fontsize=8)

    bottom.plot(df.index, df["equity"], label="Strategy")
    bottom.plot(df.index, df["buy_hold"], label="Buy and hold")
    bottom.set_title("Portfolio value")
    bottom.legend(fontsize=8)

    fig.tight_layout()
    return fig