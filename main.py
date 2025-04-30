import threading
import time
import os
import math
from binance.client import Client
import pandas as pd
import ta
from dotenv import load_dotenv

load_dotenv()

# === Binance API Bilgileri ===
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)

# === Ayarlar ===
SYMBOLS = [
    "ETHUSDT", "BTCUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LTCUSDT", "DOGEUSDT"
]
LEVERAGE = 30

# === Stepwise SL tablosu ===
stepwise_sl = [
    {"trigger": 0.015, "sl": 0.0134},
    {"trigger": 0.0183, "sl": 0.0167},
    {"trigger": 0.0215, "sl": 0.0200},
    {"trigger": 0.025, "sl": 0.0234},
    {"trigger": 0.0283, "sl": 0.0267},
    {"trigger": 0.0315, "sl": 0.0300},
    {"trigger": 0.035, "sl": 0.0334},
    {"trigger": 0.0383, "sl": 0.0367},
    {"trigger": 0.0415, "sl": 0.0400},
    {"trigger": 0.045, "sl": 0.0434},
    {"trigger": 0.0484, "sl": 0.0470},
    {"trigger": 0.0516, "sl": 0.0500},
]

# === Yardımcı Fonksiyonlar ===
def round_step_size(price, step_size):
    return round(round(price / step_size) * step_size, 8)

def get_usdt_balance():
    try:
        balances = client.futures_account_balance()
        for b in balances:
            if b['asset'] == 'USDT':
                return float(b['balance'])
    except Exception as e:
        print(f"⚠️ Bakiye alınamadı: {e}")
    return 0

def calculate_dynamic_quantity(symbol, rsi, direction):
    try:
        balance = get_usdt_balance()
        price = float(client.get_symbol_ticker(symbol=symbol)['price'])

        if direction == "long":
            if rsi < 10:
                portion = 0.12
            elif rsi < 20:
                portion = 0.1
            elif rsi < 30:
                portion = 0.08
            else:
                return 0
        elif direction == "short":
            if rsi > 90:
                portion = 0.12
            elif rsi > 80:
                portion = 0.1
            elif rsi > 70:
                portion = 0.08
            else:
                return 0
        else:
            return 0

        position_size_usdt = balance * portion
        qty = position_size_usdt * LEVERAGE / price

        exchange_info = client.futures_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for f in s['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        step_size = float(f['stepSize'])
                        precision = int(round(-math.log(step_size, 10)))
                        qty = round(qty, precision)
                        return qty

        return round(qty, 3)
    except Exception as e:
        print(f"⚠️ {symbol} miktar hesaplama hatası: {e}")
        return 0

def set_leverage(symbol):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=LEVERAGE)
    except Exception as e:
        print(f"⚠️ Leverage ayarlanamadı ({symbol}): {e}")

def is_position_open(symbol):
    retries = 3
    while retries > 0:
        try:
            positions = client.futures_position_information(symbol=symbol)
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    return True
            return False
        except Exception as e:
            print(f"⚠️ Pozisyon kontrol hatası ({symbol}): {e}")
            retries -= 1
            time.sleep(10)
    return False

# === Stop Loss Fonksiyonları ===
def create_initial_stop_loss(symbol, entry_price, qty, direction):
    try:
        print(f"🛡️ {symbol}: İlk Stop-Loss hesaplanıyor")
        price_move_pct = 0.0085  # %0.85 düşüş

        if direction == "BUY":
            sl_price = entry_price * (1 - price_move_pct)
        else:
            sl_price = entry_price * (1 + price_move_pct)

        exchange_info = client.futures_exchange_info()
        tick_size = 0.01
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for f in s['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        tick_size = float(f['tickSize'])
                        break

        corrected_sl_price = round_step_size(sl_price, tick_size)

        client.futures_create_order(
            symbol=symbol,
            side="SELL" if direction == "BUY" else "BUY",
            type="STOP_MARKET",
            stopPrice=str(corrected_sl_price),
            closePosition=True,
        )
        print(f"✅ {symbol}: İlk Stop-Loss kuruldu → {corrected_sl_price}")

    except Exception as e:
        print(f"❌ {symbol}: İlk Stop-Loss kurulamadı: {e}")

def update_stop_loss(symbol, new_sl_price, direction):
    try:
        orders = client.futures_get_open_orders(symbol=symbol)
        for order in orders:
            if order['type'] == 'STOP_MARKET' and order['closePosition']:
                client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
                print(f"❌ {symbol}: Eski SL iptal edildi.")

        # İptal ettikten sonra 2-3 saniye bekle
        time.sleep(2)

        exchange_info = client.futures_exchange_info()
        tick_size = 0.01
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for f in s['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        tick_size = float(f['tickSize'])
                        break

        corrected_sl_price = round_step_size(new_sl_price, tick_size)

        client.futures_create_order(
            symbol=symbol,
            side="SELL" if direction == "BUY" else "BUY",
            type="STOP_MARKET",
            stopPrice=str(corrected_sl_price),
            closePosition=True,
        )
        print(f"✅ {symbol}: Yeni SL kuruldu → {corrected_sl_price}")
    except Exception as e:
        print(f"❌ {symbol}: SL güncelleme hatası: {e}")

def monitor_position(symbol, direction, qty, entry_price):
    try:
        next_level = 0
        while is_position_open(symbol) and next_level < len(stepwise_sl):
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            level = stepwise_sl[next_level]

            trigger = level["trigger"]
            sl = level["sl"]

            if direction == "BUY":
                if price >= entry_price * (1 + trigger):
                    sl_price = entry_price * (1 + sl)
                    update_stop_loss(symbol, sl_price, direction)
                    next_level += 1
            else:
                if price <= entry_price * (1 - trigger):
                    sl_price = entry_price * (1 - sl)
                    update_stop_loss(symbol, sl_price, direction)
                    next_level += 1

            time.sleep(10)
    except Exception as e:
        print(f"❌ {symbol}: SL izleme hatası: {e}")

# === Pozisyon Açılışı ===
def open_position(symbol, side, direction):
    try:
        if is_position_open(symbol):
            print(f"⚠️ {symbol}: Zaten açık pozisyon var.")
            return

        df = get_data(symbol)
        rsi = df['rsi'].iloc[-1]
        qty = calculate_dynamic_quantity(symbol, rsi, direction)
        if qty == 0:
            print(f"⛔ {symbol}: RSI uygun değil veya bakiye yetersiz.")
            return

        set_leverage(symbol)
        entry_price = float(client.get_symbol_ticker(symbol=symbol)['price'])

        client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty
        )
        print(f"🚀 {symbol}: {side} pozisyon açıldı — Miktar: {qty}")

        time.sleep(2)
        create_initial_stop_loss(symbol, entry_price, qty, side)
        threading.Thread(target=monitor_position, args=(symbol, side, qty, entry_price)).start()
    except Exception as e:
        print(f"❌ {symbol}: Pozisyon açma hatası: {e}")

# === Data ve Tarama Fonksiyonları ===
def get_data(symbol, interval="15m", limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'time','open','high','low','close','volume',
            '_','__','___','____','_____','______'
        ])
        df = df[['open','high','low','close','volume']].astype(float)
        df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
        return df
    except Exception as e:
        print(f"❌ {symbol}: Veri alınamadı: {e}")
        return None

def rsi_confirmed(df, direction="long"):
    rsi = df['rsi'].iloc[-1]
    return (direction == "long" and rsi < 30) or (direction == "short" and rsi > 70)

def close_all_positions():
    for symbol in SYMBOLS:
        try:
            # Cancel all open SL/TP orders
            client.futures_cancel_all_open_orders(symbol=symbol)
            print(f"❌ {symbol}: Tüm açık emirler iptal edildi.")

            # Close open position (if any)
            positions = client.futures_position_information(symbol=symbol)
            for pos in positions:
                qty = float(pos['positionAmt'])
                if qty != 0:
                    side = "SELL" if qty > 0 else "BUY"
                    client.futures_create_order(
                        symbol=symbol,
                        side=side,
                        type="MARKET",
                        quantity=abs(qty),
                        reduceOnly=True
                    )
                    print(f"🔒 {symbol}: Pozisyon kapatıldı → {side} {abs(qty)}")
        except Exception as e:
            print(f"⚠️ {symbol}: Kapatma hatası: {e}")


# === Formasyon Fonksiyonları Import ===
from patterns.double_bottom import is_double_bottom
from patterns.double_top import is_double_top
from patterns.head_shoulders import is_head_shoulders
from patterns.inverse_head_shoulders import is_inverse_head_shoulders
from patterns.triangle_sym import is_sym_triangle
from patterns.triangle_desc import is_desc_triangle
from patterns.triangle_asc import is_asc_triangle
from patterns.channel_down import is_channel_down
from patterns.channel_up import is_channel_up
from patterns.rising_wedge import is_rising_wedge
from patterns.falling_wedge import is_falling_wedge
from patterns.bullish_flag import is_bullish_flag
from patterns.bearish_flag import is_bearish_flag
from patterns.bullish_pennant import is_bullish_pennant
from patterns.bearish_pennant import is_bearish_pennant

# === Tarama Fonksiyonu ===
def scan_symbol(symbol):
    position_open_printed = False

    patterns = [
        (is_double_bottom, "BUY", "long", "Double Bottom"),
        (is_double_top, "SELL", "short", "Double Top"),
        (is_inverse_head_shoulders, "BUY", "long", "Inverse H&S"),
        (is_head_shoulders, "SELL", "short", "Head & Shoulders"),
        (is_asc_triangle, "BUY", "long", "Ascending Triangle"),
        (is_desc_triangle, "SELL", "short", "Descending Triangle"),
        (is_channel_down, "SELL", "short", "Channel Down"),
        (is_channel_up, "BUY", "long", "Channel Up"),
        (is_rising_wedge, "SELL", "short", "Rising Wedge"),
        (is_falling_wedge, "BUY", "long", "Falling Wedge"),
        (is_bullish_flag, "BUY", "long", "Bullish Flag"),
        (is_bearish_flag, "SELL", "short", "Bearish Flag"),
        (is_bullish_pennant, "BUY", "long", "Bullish Pennant"),
        (is_bearish_pennant, "SELL", "short", "Bearish Pennant")
    ]

    while True:
        try:
            if is_position_open(symbol):
                if not position_open_printed:
                    print(f"⚠️ {symbol}: Pozisyon zaten açık.")
                    position_open_printed = True
                time.sleep(60)
                continue
            else:
                position_open_printed = False

            df = get_data(symbol)
            if df is None:
                time.sleep(60)
                continue

            rsi = df['rsi'].iloc[-1]

            # Bütün formasyonları sırayla tarıyoruz
            for func, side, direction, name in patterns:
                if func(df) and rsi_confirmed(df, direction):
                    print(f"📌 {symbol}: {name} + RSI onayı → {side}")
                    open_position(symbol, side, direction)
                    break

            # Symmetrical Triangle özel case
            if is_sym_triangle(df):
                if rsi < 30:
                    print(f"📌 {symbol}: Symmetrical Triangle + Low RSI → BUY")
                    open_position(symbol, "BUY", "long")
                elif rsi > 70:
                    print(f"📌 {symbol}: Symmetrical Triangle + High RSI → SELL")
                    open_position(symbol, "SELL", "short")

            time.sleep(60)

        except Exception as e:
            print(f"❌ {symbol}: Taramada hata: {e}")
            time.sleep(10)

# === Bot Başlangıcı ===
def main():
    print("🚀 Bot Başlatıldı...")
    for symbol in SYMBOLS:
        threading.Thread(target=scan_symbol, args=(symbol,), daemon=True).start()

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n🛑 Bot manuel olarak durduruldu. Pozisyonlar kapatılıyor...")
        close_all_positions()
        print("✅ Tüm pozisyonlar kapatıldı. Bot kapandı.")
        time.sleep(2)
        print("💰 Son bakiyen:", round(get_usdt_balance(), 2))

        

if __name__ == "__main__":
    main()
