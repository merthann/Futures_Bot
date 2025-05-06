import numpy as np
from scipy.stats import linregress

def is_bearish_flag(df, slope_threshold=0.02, max_std=0.005, breakdown_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    # İlk 10 mumda güçlü düşüş var mı?
    down_leg = closes[:10]
    slope, _, _, _, _ = linregress(np.arange(len(down_leg)), down_leg)
    initial_drop = slope < -slope_threshold

    # Sonraki 20 mumda konsolidasyon: eğim yatay ve volatilite düşük
    flag_part = closes[10:]
    slope_flag, _, _, _, _ = linregress(np.arange(len(flag_part)), flag_part)
    std_flag = np.std(flag_part)

    consolidation = abs(slope_flag) < slope_threshold and std_flag < max_std

    if initial_drop and consolidation:
        breakdown_level = min(flag_part)
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > breakdown_level:
                return False
        return True

    return False
