import numpy as np
from scipy.stats import linregress

def is_bullish_pennant(df, slope_threshold=0.02, max_std=0.005, breakout_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    # 1️⃣ İlk 10 mumda güçlü yükseliş
    up_leg = closes[:10]
    slope, _, _, _, _ = linregress(np.arange(len(up_leg)), up_leg)
    initial_surge = slope > slope_threshold

    # 2️⃣ Konsolidasyon (bayrak kısmı)
    flag_part = closes[10:]
    slope_flag, _, _, _, _ = linregress(np.arange(len(flag_part)), flag_part)
    std_flag = np.std(flag_part)
    consolidation = abs(slope_flag) < slope_threshold and std_flag < max_std

    # 3️⃣ Kırılım kontrolü
    breakout_level = max(flag_part)
    confirmed = all(closes[-i] > breakout_level for i in range(1, breakout_confirm_candles + 1))

    return initial_surge and consolidation and confirmed
