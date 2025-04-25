def is_sym_triangle(df, tolerance=0.01):  # %1 tolerans
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]

    lower_highs = all(highs[i] <= highs[i - 1] * (1 + tolerance) for i in range(1, len(highs)))
    higher_lows = all(lows[i] >= lows[i - 1] * (1 - tolerance) for i in range(1, len(lows)))

    return lower_highs and higher_lows
