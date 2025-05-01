def is_bullish_pennant(df, tolerance=0.005, breakout_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    # İlk 10 mumda yükseliş (direk kısmı)
    initial_surge = closes[10] > closes[0]

    # Sonraki mumlarda sıkışan konsolidasyon
    consolidation = all(
        abs(closes[i] - closes[i - 1]) / closes[i - 1] < tolerance
        for i in range(11, 30)
    )

    if initial_surge and consolidation:
        # Konsolidasyonun üst sınırı
        breakout_level = max(closes[10:])
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < breakout_level:
                return False
        return True

    return False
