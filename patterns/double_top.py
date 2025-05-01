def is_double_top(df, tolerance=0.02, breakdown_confirm_candles=2):
    closes = df['close'].values
    if len(closes) < 50:
        return False

    a, b, c = closes[-30], closes[-20], closes[-10]

    top_close_enough = abs(b - a) <= tolerance * b

    # Boyun çizgisi (ilk dipten sonraki destek): a
    neckline = a

    if a < b > c and top_close_enough and a < b and c < b:
        # Kırılım kontrolü: son kapanışlar neckline'ın altına indi mi?
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > neckline:
                return False
        return True

    return False
