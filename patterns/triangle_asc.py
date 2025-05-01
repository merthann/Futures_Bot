def is_asc_triangle(df, flat_tolerance=0.01, breakout_confirm_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    # Direncin flat olup olmadığını daha sağlam kontrol et (5 high'ın std sapması düşükse)
    recent_highs = highs[-5:]
    flat_resistance = max(recent_highs) - min(recent_highs) <= flat_tolerance * max(recent_highs)

    # Dipler yükseliyor
    rising_lows = all(lows[i] >= lows[i - 1] * (1 - flat_tolerance) for i in range(1, len(lows)))

    if flat_resistance and rising_lows:
        resistance = max(recent_highs)
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < resistance:
                return False
        return True

    return False
