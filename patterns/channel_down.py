def is_channel_down(df, tolerance=0.005, breakout_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    falling = all(
        highs[i] <= highs[i - 1] * (1 + tolerance) and
        lows[i] <= lows[i - 1] * (1 + tolerance)
        for i in range(1, len(highs))
    )
    
    if not falling:
        return False

    # Breakout kontrolü: son kapanışlar kanalın üstünden çıkmış mı
    max_high = max(highs)
    for i in range(1, breakout_candles + 1):
        if closes[-i] > max_high:
            return False  # Yukarı kırılım varsa short sinyali verilmez

    return True
