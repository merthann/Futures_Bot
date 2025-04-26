def is_bullish_flag(df, tolerance=0.01):
    closes = df['close'].values[-30:]
    initial_surge = closes[0] < closes[10]  # İlk yükseliş

    consolidation = all(
        closes[i] <= closes[i - 1] * (1 + tolerance)
        for i in range(11, len(closes))
    )

    return initial_surge and consolidation
