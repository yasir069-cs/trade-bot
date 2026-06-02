import time
import requests
import pandas as pd
import pandas_ta as ta
import ccxt
from datetime import datetime

# ─── CONFIG ───
TELEGRAM_TOKEN = "8966792559:AAF5GIhI9WkL6SL1nX1_NE8_pIBdPADDRRU"
CHAT_ID = "1490359174"

SYMBOL = "XRP/USDT"
TIMEFRAMES = ["15m", "1h"]

exchange = ccxt.okx()
print("USING OKX")
print(exchange.id)

last_signals = {}
last_hourly_update = 0


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            json={"chat_id": CHAT_ID, "text": message},
            timeout=15
        )
    except Exception as e:
        print(f"Telegram error: {e}")


def get_data(timeframe):
    print(f"FETCHING DATA FROM {exchange.id} | {timeframe}")
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=timeframe, limit=250)

    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    df["rsi"] = ta.rsi(df["close"], length=14)
    df["ema21"] = ta.ema(df["close"], length=21)

    bb = ta.bbands(df["close"], length=20, std=2)
    upper_col = [c for c in bb.columns if "BBU" in c][0]
    lower_col = [c for c in bb.columns if "BBL" in c][0]
    df["bb_upper"] = bb[upper_col]
    df["bb_lower"] = bb[lower_col]

    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (
        (typical_price * df["volume"]).cumsum()
        / df["volume"].cumsum()
    )

    return df


def rsi_emoji(rsi):
    if rsi < 30:
        return "🔴 Oversold"
    elif rsi < 45:
        return "🟡 Low"
    elif rsi < 55:
        return "⚪ Neutral"
    elif rsi < 70:
        return "🟢 High"
    else:
        return "🔴 Overbought"


def trend_emoji(price, ema21, vwap):
    if price > ema21 and price > vwap:
        return "📈 Bullish"
    elif price < ema21 and price < vwap:
        return "📉 Bearish"
    else:
        return "➡️ Sideways"


def send_hourly_update():
    """Har 1 ghante mein market status — bina condition ke"""
    global last_hourly_update

    if time.time() - last_hourly_update < 3600:
        return

    try:
        df = get_data("1h")
        row = df.iloc[-1]

        if pd.isna(row["rsi"]) or pd.isna(row["ema21"]):
            return

        price    = float(row["close"])
        rsi      = float(row["rsi"])
        ema21    = float(row["ema21"])
        vwap     = float(row["vwap"])
        upper_bb = float(row["bb_upper"])
        lower_bb = float(row["bb_lower"])
        now      = datetime.now().strftime("%d %b %I:%M %p")

        bb_position = ""
        if price >= upper_bb:
            bb_position = "⬆️ Above Upper BB"
        elif price <= lower_bb:
            bb_position = "⬇️ Below Lower BB"
        else:
            bb_position = "↔️ Inside BB"

        message = (
            f"📊 XRP/USDT — Hourly Update\n"
            f"⏰ {now}\n\n"
            f"💰 Price: {price:.4f} USDT\n\n"
            f"RSI: {rsi:.1f} — {rsi_emoji(rsi)}\n"
            f"Trend: {trend_emoji(price, ema21, vwap)}\n"
            f"BB: {bb_position}\n\n"
            f"EMA21: {ema21:.4f}\n"
            f"VWAP:  {vwap:.4f}\n"
            f"Upper BB: {upper_bb:.4f}\n"
            f"Lower BB: {lower_bb:.4f}\n\n"
            f"🔄 Next update in 1 hour"
        )

        send_telegram(message)
        last_hourly_update = time.time()
        print(f"Hourly update sent — {now}")

    except Exception as e:
        print(f"Hourly update error: {e}")


def analyze(timeframe):
    global last_signals

    print(f"Checking XRP/USDT {timeframe}")

    df = get_data(timeframe)
    row = df.iloc[-1]

    if pd.isna(row["rsi"]) or pd.isna(row["ema21"]):
        return

    price    = float(row["close"])
    rsi      = float(row["rsi"])
    ema21    = float(row["ema21"])
    vwap     = float(row["vwap"])
    upper_bb = float(row["bb_upper"])
    lower_bb = float(row["bb_lower"])

    signal = None

    # STRONG BUY
    if (
        rsi < 40
        and price > ema21
        and price > vwap
        and price <= lower_bb * 1.02
    ):
        signal = "🚀 STRONG BUY"

    # STRONG SELL
    elif (
        rsi > 65
        and price < ema21
        and price < vwap
        and price >= upper_bb * 0.98
    ):
        signal = "🔻 STRONG SELL"

    # BUY
    elif (
        rsi < 45
        and price > ema21
        and price > vwap
    ):
        signal = "📈 BUY"

    # SELL
    elif (
        rsi > 60
        and price < ema21
        and price < vwap
    ):
        signal = "📉 SELL"

    if signal:
        unique_key = f"{timeframe}-{signal}-{round(price, 3)}"

        if last_signals.get(timeframe) != unique_key:
            last_signals[timeframe] = unique_key

            now = datetime.now().strftime("%d %b %I:%M %p")

            message = (
                f"{signal}\n\n"
                f"Coin: XRP/USDT\n"
                f"Timeframe: {timeframe}\n"
                f"Price: {price:.4f}\n"
                f"RSI: {rsi:.1f} — {rsi_emoji(rsi)}\n"
                f"Trend: {trend_emoji(price, ema21, vwap)}\n"
                f"EMA21: {ema21:.4f}\n"
                f"VWAP: {vwap:.4f}\n"
                f"Time: {now}\n\n"
                f"⚠️ DYOR — Ye sirf alert hai!"
            )

            print(message)
            send_telegram(message)


def main():
    send_telegram(
        "🤖 XRP Alert Bot STARTED\n\n"
        "Exchange: OKX\n"
        "Pair: XRP/USDT\n"
        "Timeframes: 15m + 1h\n"
        "Indicators: RSI + BB + EMA21 + VWAP\n\n"
        "📊 Hourly market update ON\n"
        "🚨 Signal alerts ON\n\n"
        "✅ Bot is LIVE!"
    )

    print("EXCHANGE =", exchange.id)

    # Turant pehla hourly update bhejo
    last_hourly_update = 0

    while True:
        try:
            # Har ghante market status
            send_hourly_update()

            # Signal check
            for tf in TIMEFRAMES:
                analyze(tf)

        except Exception as e:
            import traceback
            traceback.print_exc()
            send_telegram(f"⚠️ Bot Error:\n{str(e)}")

        time.sleep(60)


if __name__ == "__main__":
    main()
