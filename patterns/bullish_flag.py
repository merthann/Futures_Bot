import numpy as np
from scipy.stats import linregress

def is_bullish_flag(df, slope_threshold=0.02, max_std=0.005, breakout_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    # İlk 10 mumda güçlü yükseliş var mı? (lineer regresyon eğimi)
    up_leg = closes[:10]
    slope, _, _, _, _ = linregress(np.arange(len(up_leg)), up_leg)
    initial_surge = slope > slope_threshold

    # Sonraki 20 mumda konsolidasyon: eğim yatay ve volatilite düşük
    flag_part = closes[10:]
    slope_flag, _, _, _, _ = linregress(np.arange(len(flag_part)), flag_part)
    std_flag = np.std(flag_part)

    consolidation = abs(slope_flag) < slope_threshold and std_flag < max_std

    if initial_surge and consolidation:
        breakout_level = max(flag_part)
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < breakout_level:
                return False
        return True

    return False
