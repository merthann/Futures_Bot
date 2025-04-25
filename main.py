import threading
import time
import os
from binance.client import Client
import pandas as pd
import ta

# === Binance API Bilgileri ===
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)
client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'

# === Ayarlar ===
SYMBOLS = [
    "ETHUSDT", "BTCUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LTCUSDT", "DOGEUSDT"
]
LEVERAGE = 30
INITIAL_SL_PERCENT = 0.08
stepwise_tp = [
    {"trigger": 0.08, "take": 0.05},
    {"trigger": 0.18, "take": 0.15},
    {"trigger": 0.28, "take": 0.25},
    {"trigger": 0.38, "take": 0.35},
    {"trigger": 0.48, "take": 0.45},
    {"trigger": 0.58, "take": 0.55}
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

        # 💥 Yeni: pozisyon büyüklüğü = (balance * portion)
        position_size_usdt = balance * portion  # Örn: 50 USDT

        # 💥 Gerçek miktar = pozisyon büyüklüğü / fiyat / kaldıraç
        qty = position_size_usdt * LEVERAGE / price

        # 🔍 Binance hassasiyetini alalım
        exchange_info = client.futures_exchange_info()
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                for f in symbol_info['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        step_size = float(f['stepSize'])
                        precision = abs(int(round(-1 * (step_size).as_integer_ratio()[1].bit_length() - 1)))
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


def monitor_position(symbol, direction, qty, entry_price):
    try:
        for level in stepwise_tp:
            while is_position_open(symbol):
                price = float(client.get_symbol_ticker(symbol=symbol)['price'])
                change = (price - entry_price) / entry_price if direction == "BUY" else (entry_price - price) / entry_price

                if change >= level["trigger"]:
                    take_price = round(entry_price * (1 + level["take"]), 2) if direction == "BUY" else round(entry_price * (1 - level["take"]), 2)

                    print(f"🎯 {symbol} → {int(level['take']*100)}% TP hedefi geldi! Emir gönderiliyor → {take_price}")

                    client.futures_create_order(
                        symbol=symbol,
                        side="SELL" if direction == "BUY" else "BUY",
                        type="TAKE_PROFIT_MARKET",
                        stopPrice=str(take_price),
                        closePosition=True,
                        reduceOnly=True
                    )
                    return
                time.sleep(15)
    except Exception as e:
        print(f"❌ {symbol} için TP izleme hatası: {e}")


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

        sl_price = round(entry * (1 - 0.08), 2) if side == "BUY" else round(entry * (1 + 0.08), 2)
        client.futures_create_order(
            symbol=symbol,
            side="SELL" if side == "BUY" else "BUY",
            type="STOP_MARKET",
            stopPrice=str(sl_price),
            closePosition=True,
            reduceOnly=True
        )
        print(f"🛡️ {symbol}: SL kuruldu → {sl_price}")

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

# === Coin Tarayıcı ===
def scan_symbol(symbol):
    while True:
        try:
            if is_position_open(symbol):
                print(f"⚠️ {symbol} pozisyonu zaten açık.")
                time.sleep(60)
                continue

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
                (is_channel_up, "SELL", "short", "Channel Up")
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


