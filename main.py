import time
import requests
import pandas as pd
import pandas_ta as ta
import ccxt

# ─── CONFIG ───

TELEGRAM_TOKEN = “8966792559:AAF5GIhI9WkL6SL1nX1_NE8_pIBdPADDRRU” 
CHAT_ID = “1490359174”

SYMBOL = “XRP/USDT”
TIMEFRAMES = [“15m”, “1h”]

# OKX — Railway pe kaam karta hai, no geo-restriction

exchange = ccxt.okx()

print(“USING OKX”)
print(exchange.id)

last_signals = {}

def send_telegram(message):
url = f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage”
try:
requests.post(
url,
json={“chat_id”: CHAT_ID, “text”: message},
timeout=15
)
except Exception as e:
print(f”Telegram error: {e}”)

def get_data(timeframe):
print(f”FETCHING DATA FROM {exchange.id} | {timeframe}”)
ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=timeframe, limit=250)

```
df = pd.DataFrame(
    ohlcv,
    columns=["timestamp", "open", "high", "low", "close", "volume"]
)

df["rsi"] = ta.rsi(df["close"], length=14)
df["ema21"] = ta.ema(df["close"], length=21)

bb = ta.bbands(df["close"], length=20, std=2)
df = pd.concat([df, bb], axis=1)

typical_price = (df["high"] + df["low"] + df["close"]) / 3
df["vwap"] = (
    (typical_price * df["volume"]).cumsum()
    / df["volume"].cumsum()
)

return df
```

def analyze(timeframe):
global last_signals

```
print(f"Checking XRP/USDT {timeframe}")

df = get_data(timeframe)
row = df.iloc[-1]

if pd.isna(row["rsi"]) or pd.isna(row["ema21"]):
    return

price    = float(row["close"])
rsi      = float(row["rsi"])
ema21    = float(row["ema21"])
vwap     = float(row["vwap"])
upper_bb = float(row["BBU_20_2.0"])
lower_bb = float(row["BBL_20_2.0"])

signal = None

# ─── STRONG BUY ───
if (
    rsi < 30
    and price > ema21
    and price > vwap
    and price <= lower_bb * 1.01
):
    signal = "🚀 STRONG BUY"

# ─── STRONG SELL ───
elif (
    rsi > 70
    and price < ema21
    and price < vwap
    and price >= upper_bb * 0.99
):
    signal = "🔻 STRONG SELL"

# ─── BUY ───
elif (
    rsi < 35
    and price > ema21
    and price > vwap
):
    signal = "📈 BUY"

# ─── SELL ───
elif (
    rsi > 65
    and price < ema21
    and price < vwap
):
    signal = "📉 SELL"

if signal:
    unique_key = f"{timeframe}-{signal}-{round(price, 4)}"

    if last_signals.get(timeframe) != unique_key:
        last_signals[timeframe] = unique_key

        message = (
            f"{signal}\n\n"
            f"Coin: XRP/USDT\n"
            f"Exchange: OKX\n"
            f"Timeframe: {timeframe}\n"
            f"Price: {price:.4f}\n"
            f"RSI: {rsi:.2f}\n"
            f"EMA21: {ema21:.4f}\n"
            f"VWAP: {vwap:.4f}\n"
            f"Upper BB: {upper_bb:.4f}\n"
            f"Lower BB: {lower_bb:.4f}"
        )

        print(message)
        send_telegram(message)
```

def main():
send_telegram(
“🤖 XRP Alert Bot STARTED\n\n”
“Exchange: OKX\n”
“Pair: XRP/USDT\n”
“Timeframes: 15m + 1h\n”
“Indicators: RSI + BB + EMA21 + VWAP\n\n”
“✅ Bot is LIVE!”
)

```
print("EXCHANGE =", exchange.id)

while True:
    try:
        for tf in TIMEFRAMES:
            analyze(tf)

    except Exception as e:
        import traceback
        traceback.print_exc()
        send_telegram(f"⚠️ Bot Error:\n{str(e)}")

    time.sleep(60)
```

if **name** == “**main**”:
main()
