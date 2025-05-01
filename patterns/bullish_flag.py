def is_bullish_flag(df, tolerance=0.01, breakout_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    initial_surge = closes[10] > closes[0]  # İlk 10 mumda yükseliş

    consolidation = all(
        closes[i] <= closes[i - 1] * (1 + tolerance)
        for i in range(11, 30)
    )

    if initial_surge and consolidation:
        breakout_level = max(closes[10:])  # Bayrağın üst seviyesi
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < breakout_level:
                return False
        return True

    return False
