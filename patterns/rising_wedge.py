def is_rising_wedge(df, tolerance=0.005, breakdown_confirm_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    ascending = all(
        highs[i] >= highs[i - 1] * (1 - tolerance) and
        lows[i] >= lows[i - 1] * (1 - tolerance)
        for i in range(1, len(highs))
    )

    contracting = (max(highs) - min(highs)) > (max(lows) - min(lows))

    if ascending and contracting:
        breakdown_level = min(lows)
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > breakdown_level:
                return False
        return True

    return False
