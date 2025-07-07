import yfinance as yf
import pandas as pd
import yagmail
from datetime import datetime

# Email credentials (set these on Render as environment variables)
import os
EMAIL_USER = os.getenv("akumaran313@gmail.com")
EMAIL_PASS = os.getenv("lbdk vebu jksi faub")

receiver = EMAIL_USER  # Send to self, or change to your desired email

def calculate_levels(price, signal_type):
    if price < 100:
        t1, t2, sl = 1.0, 2.0, 0.8
    elif price < 250:
        t1, t2, sl = 1.5, 3.0, 1.2
    elif price < 500:
        t1, t2, sl = 2.5, 4.5, 2.0
    elif price < 750:
        t1, t2, sl = 3.5, 6.0, 3.0
    else:
        t1, t2, sl = 5.0, 8.0, 4.0
    if signal_type == 'Buy':
        return round(price + t1, 2), round(price + t2, 2), round(price - sl, 2)
    else:
        return round(price - t1, 2), round(price - t2, 2), round(price + sl, 2)

def calculate_fib_levels(high, low):
    diff = high - low
    return {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.500 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }

def send_email(subject, body):
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
    yag.send(to=receiver, subject=subject, contents=body)

def main():
    symbols = pd.read_csv("ind_nifty500list.csv")["Symbol"].tolist()
    buy_signals, sell_signals = [], []

    for symbol in symbols:
        try:
            data = yf.Ticker(symbol + ".NS").history(period="1d", interval="15m")
            if len(data) < 10 or data["Volume"].mean() < 50000:
                continue
            high = data["High"].max()
            low = data["Low"].min()
            close = data["Close"].iloc[-1]
            open_price = data["Open"].iloc[0]
            if close >= 1000:
                continue

            fib = calculate_fib_levels(high, low)
            near_fib = any(abs(close - fib[level]) < 0.5 for level in ['61.8%', '50.0%'])

            if close > open_price and near_fib:
                t1, t2, sl = calculate_levels(close, 'Buy')
                buy_signals.append(f"{symbol}: Buy at ₹{close:.2f} → T1: ₹{t1}, T2: ₹{t2}, SL: ₹{sl}")
            elif close < open_price and near_fib:
                t1, t2, sl = calculate_levels(close, 'Sell')
                sell_signals.append(f"{symbol}: Short at ₹{close:.2f} → T1: ₹{t1}, T2: ₹{t2}, SL: ₹{sl}")
        except Exception:
            continue

    if not buy_signals and not sell_signals:
        send_email("Fibonacci Signal Bot 📉", "No signals found today.")
    else:
        body = "📘 Buy Signals:\n" + "\n".join(buy_signals) + "\n\n📕 Sell Signals:\n" + "\n".join(sell_signals)
        send_email(f"Fibonacci Signals – {datetime.now().strftime('%d %b %Y')}", body)

if __name__ == "__main__":
    main()
