def is_bearish_flag(df, tolerance=0.01, breakdown_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    # İlk 10 mumda net düşüş var mı?
    initial_drop = closes[10] < closes[0]

    # Sonraki mumlarda yükseliş/konsolidasyon (bearish flag genelde yukarıya doğru bir bayraktır)
    consolidation = all(
        closes[i] >= closes[i - 1] * (1 - tolerance)
        for i in range(11, 30)
    )

    if initial_drop and consolidation:
        # Bayrağın alt sınırı: konsolidasyonun en düşük noktası
        breakdown_level = min(closes[10:])
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > breakdown_level:
                return False
        return True

    return False
