def is_sym_triangle_breakout(df, tolerance=0.01, breakout_confirm_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    # Simetrik üçgen yapısı
    lower_highs = all(highs[i] <= highs[i - 1] * (1 + tolerance) for i in range(1, len(highs)))
    higher_lows = all(lows[i] >= lows[i - 1] * (1 - tolerance) for i in range(1, len(lows)))
    
    if not (lower_highs and higher_lows):
        return False

    # Kırılım onayı: son mumlar üçgenin üstünden çıkmış mı
    recent_high = max(highs)
    breakout = all(closes[-i] > recent_high for i in range(1, breakout_confirm_candles + 1))
    
    return breakout
