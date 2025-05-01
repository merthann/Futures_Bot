def is_falling_wedge(df, tolerance=0.005, breakout_confirm_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    descending = all(
        highs[i] <= highs[i - 1] * (1 + tolerance) and
        lows[i] <= lows[i - 1] * (1 + tolerance)
        for i in range(1, len(highs))
    )

    contracting = (max(highs) - min(highs)) > (max(lows) - min(lows))

    if descending and contracting:
        breakout_level = max(highs)
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < breakout_level:
                return False
        return True

    return False
