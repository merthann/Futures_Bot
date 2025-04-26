def is_falling_wedge(df, tolerance=0.005):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]

    descending = all(
        highs[i] <= highs[i - 1] * (1 + tolerance) and
        lows[i] <= lows[i - 1] * (1 + tolerance)
        for i in range(1, len(highs))
    )

    contracting = (max(highs) - min(highs)) > (max(lows) - min(lows))

    return descending and contracting
