def is_channel_down(df, tolerance=0.005):  # %0.5 tolerans
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]

    falling = all(
        highs[i] <= highs[i - 1] * (1 + tolerance) and
        lows[i] <= lows[i - 1] * (1 + tolerance)
        for i in range(1, len(highs))
    )
    return falling
