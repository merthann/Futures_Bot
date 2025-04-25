def is_desc_triangle(df, flat_tolerance=0.01):  # %1 tolerans
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]

    flat_support = abs(lows[-1] - lows[0]) <= flat_tolerance * lows[-1]
    falling_highs = all(highs[i] <= highs[i - 1] * (1 + flat_tolerance) for i in range(1, len(highs)))

    return flat_support and falling_highs
