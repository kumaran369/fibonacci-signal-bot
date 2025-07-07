import yfinance as yf
import pandas as pd
import yagmail
from datetime import datetime
import os

def send_email(subject, body):
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ Email credentials not found.")
        return

    yag = yagmail.SMTP(user=EMAIL_USER, password=EMAIL_PASS, host='smtp.gmail.com')
    yag.send(to=EMAIL_USER, subject=subject, contents=body)
    print("✅ Email sent successfully.")

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

def main():
    try:
        df = pd.read_csv("ind_nifty500list.csv")
        symbols = df['Symbol'].dropna().tolist()
    except Exception as e:
        print("❌ Error loading symbol list:", e)
        return

    buy_signals = []
    sell_signals = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol + ".NS")
            hist = ticker.history(period='1d', interval="15m")

            if hist.empty or len(hist) < 10 or hist['Volume'].mean() < 50000:
                continue

            high = hist['High'].max()
            low = hist['Low'].min()
            close = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]

            if close >= 1000:
                continue

            fib = calculate_fib_levels(high, low)
            near_fib = any(abs(close - fib[level]) < 0.5 for level in ['61.8%', '50.0%'])

            if close > open_price and near_fib:
                t1, t2, sl = calculate_levels(close, 'Buy')
                buy_signals.append((symbol, close, t1, t2, sl))

            elif close < open_price and near_fib:
                t1, t2, sl = calculate_levels(close, 'Sell')
                sell_signals.append((symbol, close, t1, t2, sl))

        except Exception as e:
            print(f"Skipping {symbol}: {e}")
            continue

    if not buy_signals and not sell_signals:
        print("❌ No signals today.")
        return

    body = ""
    if buy_signals:
        body += "📘 BUY SIGNALS:\n"
        for symbol, entry, t1, t2, sl in buy_signals[:3]:
            body += f"{symbol}: Entry ₹{entry}, T1 ₹{t1}, T2 ₹{t2}, SL ₹{sl}\n"
        body += "\n"

    if sell_signals:
        body += "📕 SHORT SIGNALS:\n"
        for symbol, entry, t1, t2, sl in sell_signals[:3]:
            body += f"{symbol}: Entry ₹{entry}, T1 ₹{t1}, T2 ₹{t2}, SL ₹{sl}\n"

    subject = f"Fibonacci Signals – {datetime.now().strftime('%d %b %Y')}"
    send_email(subject, body)

if __name__ == "__main__":
    main()
