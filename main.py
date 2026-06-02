import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import ccxt

# Railway Variables
TELEGRAM_TOKEN = "8966792559:AAF5GIhI9WkL6SL1nX1_NE8_pIBdPADDRRU"
CHAT_ID = "1490359174"

SYMBOL = "XRP/USDT"
TIMEFRAMES = ["15m", "1h"]
exchange = ccxt.kucoin()
print("USING KUCOIN")
print(exchange.id)
last_signals = {}
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=15
    )


def get_data(timeframe):
    print("FETCHING DATA FROM", exchange.id)
    ohlcv = exchange.fetch_ohlcv(
        SYMBOL,
        timeframe=timeframe,
        limit=250
    )

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["rsi"] = ta.rsi(df["close"], length=14)
    df["ema21"] = ta.ema(df["close"], length=21)

    bb = ta.bbands(df["close"], length=20, std=2)
    df = pd.concat([df, bb], axis=1)

    typical_price = (
        df["high"] +
        df["low"] +
        df["close"]
    ) / 3

    df["vwap"] = (
        (typical_price * df["volume"]).cumsum()
        / df["volume"].cumsum()
    )

    return df


def analyze(timeframe):
    global last_signals

    print(f"Checking XRP {timeframe}")

    df = get_data(timeframe)

    row = df.iloc[-1]

    if pd.isna(row["rsi"]) or pd.isna(row["ema21"]):
        return

    price = float(row["close"])
    rsi = float(row["rsi"])
    ema21 = float(row["ema21"])
    vwap = float(row["vwap"])

    upper_bb = float(row["BBU_20_2.0"])
    lower_bb = float(row["BBL_20_2.0"])

    signal = None

    # STRONG BUY
    if (
        rsi < 30
        and price > ema21
        and price > vwap
        and price <= lower_bb * 1.01
    ):
        signal = "🚀 STRONG BUY"

    # STRONG SELL
    elif (
        rsi > 70
        and price < ema21
        and price < vwap
        and price >= upper_bb * 0.99
    ):
        signal = "🔻 STRONG SELL"

    # BUY
    elif (
        rsi < 35
        and price > ema21
        and price > vwap
    ):
        signal = "📈 BUY"

    # SELL
    elif (
        rsi > 65
        and price < ema21
        and price < vwap
    ):
        signal = "📉 SELL"

    if signal:

        unique_key = f"{timeframe}-{signal}-{round(price,4)}"

        if last_signals.get(timeframe) != unique_key:

            last_signals[timeframe] = unique_key

            message = (
                f"{signal}\n\n"
                f"Coin: XRP/USDT\n"
                f"Timeframe: {timeframe}\n"
                f"Price: {price:.4f}\n"
                f"RSI: {rsi:.2f}\n"
                f"EMA21: {ema21:.4f}\n"
                f"VWAP: {vwap:.4f}"
            )

            print(message)
            send_telegram(message)


def main():

    send_telegram("🧪 KUCOIN TEST BUILD")

    while True:

        try:

            for tf in TIMEFRAMES:
                analyze(tf)

        except Exception as e:
            print("ERROR:", e)

        time.sleep(60)


if __name__ == "__main__":
    main()
