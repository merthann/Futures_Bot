def is_bearish_pennant(df, tolerance=0.005, breakdown_confirm_candles=2):
    closes = df['close'].values[-30:]
    if len(closes) < 30:
        return False

    # İlk 10 mumda düşüş var mı?
    initial_drop = closes[10] < closes[0]

    # Konsolidasyon: küçük dalgalanma (daralan fiyat hareketi)
    consolidation = all(
        abs(closes[i] - closes[i - 1]) / closes[i - 1] < tolerance
        for i in range(11, 30)
    )

    if initial_drop and consolidation:
        # Pennant'ın alt sınırı
        breakdown_level = min(closes[10:])
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > breakdown_level:
                return False
        return True

    return False
