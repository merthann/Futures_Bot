def is_asc_triangle(df, flat_tolerance=0.01):  # %1 tolerans
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]

    # İlk ve son high arasındaki fark küçük olmalı
    flat_resistance = abs(highs[-1] - highs[0]) <= flat_tolerance * highs[-1]

    # Dipler yukarı gidiyor (katı şekilde, istersen burada da tolerans verebiliriz)
    rising_lows = all(lows[i] >= lows[i - 1] * (1 - flat_tolerance) for i in range(1, len(lows)))

    return flat_resistance and rising_lows
