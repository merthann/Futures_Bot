def is_bullish_pennant(df, tolerance=0.005):
    closes = df['close'].values[-30:]
    initial_surge = closes[0] < closes[10]

    consolidation = all(
        abs(closes[i] - closes[i - 1]) / closes[i - 1] < tolerance
        for i in range(11, len(closes))
    )

    return initial_surge and consolidation
