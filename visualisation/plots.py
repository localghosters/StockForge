import matplotlib.pyplot as plt


def plot_equity(df, ticker, save_path=None):
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df["equity"], label="Strategy")
    plt.plot(df.index, df["buy_hold"], label="Buy and hold")
    plt.title(f"{ticker}: strategy vs buy and hold")
    plt.xlabel("Date")
    plt.ylabel("Portfolio value")
    plt.legend()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()