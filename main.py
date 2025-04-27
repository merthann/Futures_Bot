import threading
import time
import os
import math
from binance.client import Client
import pandas as pd
import ta

# === Binance API Bilgileri ===
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)
# client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'

# === Ayarlar ===
SYMBOLS = [
    "ETHUSDT", "BTCUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LTCUSDT", "DOGEUSDT"
]
LEVERAGE = 30
INITIAL_SL_PERCENT = 0.2

stepwise_sl = [
    {"trigger": 0.45, "sl": 0.40},
    {"trigger": 0.55, "sl": 0.45},
    {"trigger": 0.65, "sl": 0.55},
    {"trigger": 0.75, "sl": 0.65},
    {"trigger": 0.85, "sl": 0.75},
    {"trigger": 0.95, "sl": 0.85},
    {"trigger": 1.05, "sl": 0.95},
    {"trigger": 1.15, "sl": 1.05},
    {"trigger": 1.25, "sl": 1.15},
    {"trigger": 1.35, "sl": 1.25},
    {"trigger": 1.45, "sl": 1.35},
    {"trigger": 1.55, "sl": 1.45},
    {"trigger": 1.65, "sl": 1.55},
]

# === Dinamik Miktar Hesaplama ===
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
                portion = 0.10
            elif rsi < 20:
                portion = 0.08
            elif rsi < 30:
                portion = 0.05
            else:
                return 0
        elif direction == "short":
            if rsi > 90:
                portion = 0.10
            elif rsi > 80:
                portion = 0.08
            elif rsi > 70:
                portion = 0.05
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
            print(f"🔁 {symbol}: {retries} tekrar hakkı kaldı, 10 saniye bekleniyor...")
            time.sleep(10)
    return False

def rsi_confirmed(df, direction="long"):
    rsi = df['rsi'].iloc[-1]
    if direction == "long" and rsi < 30:
        return True
    elif direction == "short" and rsi > 70:
        return True
    return False

def get_data(symbol, interval="15m", limit=100):
    retries = 3
    while retries > 0:
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
            print(f"🔁 {symbol} verisi alınamadı: {e}")
            retries -= 1
            print(f"🔁 {symbol}: {retries} tekrar hakkı kaldı, 10 saniye bekleniyor...")
            time.sleep(10)
    print(f"❌ {symbol}: Veri alınamadı, fonksiyon boş döndü.")
    return None

def create_initial_stop_loss(symbol, entry_price, qty, direction):
    try:
        print(f"🛡️ {symbol}: İlk Stop-Loss hesaplanıyor")

        position_value = entry_price * qty
        margin = position_value / LEVERAGE
        max_loss_amount = margin * INITIAL_SL_PERCENT
        price_move_needed = max_loss_amount / qty

        if direction == "BUY":
            sl_price = entry_price - price_move_needed
        else:
            sl_price = entry_price + price_move_needed

        # Coin'in tick size'ını çek
        exchange_info = client.futures_exchange_info()
        tick_size = 0.01  # Default
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




def round_step_size(price, step_size):
    return round(round(price / step_size) * step_size, 8)

def update_stop_loss(symbol, new_sl_price, direction):
    try:
        # Önce eski STOP_MARKET emrini iptal et
        orders = client.futures_get_open_orders(symbol=symbol)
        for order in orders:
            if order['type'] == 'STOP_MARKET' and order['closePosition']:
                client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
                print(f"❌ {symbol}: Eski Stop-Loss iptal edildi.")

        # Şimdi yeni STOP_MARKET emrini kur
        print(f"🛡️ {symbol}: Yeni Stop-Loss kuruluyor → {new_sl_price}")

        # Coin'in tick size'ını çek
        exchange_info = client.futures_exchange_info()
        tick_size = 0.01  # Default
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
    except Exception as e:
        print(f"❌ {symbol}: Stop-Loss güncelleme hatası: {e}")

def monitor_position(symbol, direction, qty, entry_price):
    try:
        next_level = 0
        initial_position_value = entry_price * qty  # Pozisyonu açtığımızdaki USDT değeri

        while is_position_open(symbol) and next_level < len(stepwise_sl):
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            current_position_value = price * qty  # Şu anki pozisyonun değeri

            # Gerçekleşen kâr (USDT cinsinden)
            profit_usdt = current_position_value - initial_position_value if direction == "BUY" else initial_position_value - current_position_value

            # Kâr yüzdesi
            profit_percentage = profit_usdt / initial_position_value

            level = stepwise_sl[next_level]

            if profit_percentage >= level["trigger"]:
                # Yeni Stop-Loss seviyesi (kârın belli yüzdesine göre)
                target_usdt_value = initial_position_value * (1 + level["sl"]) if direction == "BUY" else initial_position_value * (1 - level["sl"])
                new_sl_price = target_usdt_value / qty

                update_stop_loss(symbol, new_sl_price, direction)
                next_level += 1  # Sonraki kademeye geç
            time.sleep(10)

    except Exception as e:
        print(f"❌ {symbol} için SL izleme hatası: {e}")

def open_position(symbol, side, direction):
    try:
        df = get_data(symbol)
        rsi = df['rsi'].iloc[-1]
        qty = calculate_dynamic_quantity(symbol, rsi, direction)
        if qty == 0:
            print(f"⛔ {symbol}: RSI uygun değil veya bakiye yetersiz.")
            return

        set_leverage(symbol)
        entry = float(client.get_symbol_ticker(symbol=symbol)['price'])

        client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty
        )
        print(f"🚀 {symbol}: {side} pozisyon açıldı — Miktar: {qty}")

        time.sleep(3)

        # Başlangıçta %20 zarar için initial Stop-Loss koy
        create_initial_stop_loss(symbol, entry, qty, side)

        # Pozisyonu kâr için izlemeye başla
        threading.Thread(target=monitor_position, args=(symbol, side, qty, entry)).start()
    except Exception as e:
        print(f"❌ {symbol} için pozisyon açma hatası: {e}")

# === Formasyonlar ===
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


# === Coin Tarayıcı ===
def scan_symbol(symbol):
    position_open_printed = False
    while True:
        try:
            if is_position_open(symbol):
                if not position_open_printed:
                    print(f"⚠️ {symbol} pozisyonu zaten açık.")
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

            patterns = [
                (is_double_bottom, "BUY", "long", "Double Bottom"),
                (is_double_top, "SELL", "short", "Double Top"),
                (is_inverse_head_shoulders, "BUY", "long", "Inverse H&S"),
                (is_head_shoulders, "SELL", "short", "H&S"),
                (is_asc_triangle, "BUY", "long", "Ascending Triangle"),
                (is_desc_triangle, "SELL", "short", "Descending Triangle"),
                (is_channel_down, "BUY", "long", "Channel Down"),
                (is_channel_up, "SELL", "short", "Channel Up"),
                (is_rising_wedge, "SELL", "short", "Rising Wedge"),
                (is_falling_wedge, "BUY", "long", "Falling Wedge"),
                (is_bullish_flag, "BUY", "long", "Bullish Flag"),
                (is_bearish_flag, "SELL", "short", "Bearish Flag"),
                (is_bullish_pennant, "BUY", "long", "Bullish Pennant"),
                (is_bearish_pennant, "SELL", "short", "Bearish Pennant")
            ]

            for func, side, direction, name in patterns:
                if func(df) and rsi_confirmed(df, direction):
                    print(f"📌 {symbol}: {name} + RSI → {side}")
                    open_position(symbol, side, direction)
                    break

            if is_sym_triangle(df):
                if rsi < 30:
                    open_position(symbol, "BUY", "long")
                elif rsi > 70:
                    open_position(symbol, "SELL", "short")

            time.sleep(60)
        except Exception as e:
            print(f"❌ {symbol} için genel tarama hatası: {e}")
            time.sleep(10)

# === Ana Başlatıcı ===
def main():
    print("🚀 Çoklu Coin Bot Başlatıldı...")
    for symbol in SYMBOLS:
        threading.Thread(target=scan_symbol, args=(symbol,), daemon=True).start()

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
