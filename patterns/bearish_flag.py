def is_bearish_flag(df, tolerance=0.01):
    closes = df['close'].values[-30:]
    initial_drop = closes[0] > closes[10]  # İlk düşüş

    consolidation = all(
        closes[i] >= closes[i - 1] * (1 - tolerance)
        for i in range(11, len(closes))
    )

    return initial_drop and consolidation
