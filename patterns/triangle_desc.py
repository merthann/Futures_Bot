def is_desc_triangle(df, flat_tolerance=0.01, breakdown_confirm_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    # Desteğin flat olup olmadığını daha sağlam kontrol et
    recent_lows = lows[-5:]
    flat_support = max(recent_lows) - min(recent_lows) <= flat_tolerance * max(recent_lows)

    # Tepeler düşüyor
    falling_highs = all(highs[i] <= highs[i - 1] * (1 + flat_tolerance) for i in range(1, len(highs)))

    if flat_support and falling_highs:
        support = min(recent_lows)
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > support:
                return False
        return True

    return False
