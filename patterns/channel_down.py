from scipy.signal import argrelextrema
import numpy as np

def is_channel_down(df, deviation=0.01, breakout_candles=2):
    closes = df['close'].values[-40:]
    highs = df['high'].values[-40:]
    lows = df['low'].values[-40:]

    # Swing highs ve lows bul
    peak_idx = argrelextrema(highs, np.greater)[0]
    trough_idx = argrelextrema(lows, np.less)[0]

    if len(peak_idx) < 2 or len(trough_idx) < 2:
        return False

    # Son 2 swing high ve low al
    high_points = [(i, highs[i]) for i in peak_idx[-2:]]
    low_points = [(i, lows[i]) for i in trough_idx[-2:]]

    # Üst trend çizgisi (highs)
    x_high, y_high = zip(*high_points)
    m_high, b_high = np.polyfit(x_high, y_high, 1)

    # Alt trend çizgisi (lows)
    x_low, y_low = zip(*low_points)
    m_low, b_low = np.polyfit(x_low, y_low, 1)

    # Kanal düşüş yönlü mü?
    if m_high > 0 or m_low > 0:
        return False  # Her iki çizgi negatif eğimli olmalı

    # Fiyatlar bu düşen kanalın dışına çıkmamış mı?
    for i in range(1, breakout_candles + 1):
        expected_high = m_high * (-i) + b_high
        expected_low = m_low * (-i) + b_low
        price = closes[-i]

        if price < expected_low * (1 - deviation) or price > expected_high * (1 + deviation):
            return False

    return True
