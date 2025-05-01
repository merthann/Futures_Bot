def is_double_bottom(df, tolerance=0.02, breakout_confirm_candles=2):
    closes = df['close'].values
    if len(closes) < 50:
        return False

    a, b, c = closes[-30], closes[-20], closes[-10]

    # 2 dibe yakın mı?
    dip_close_enough = abs(b - c) < tolerance * c

    # Boyun çizgisi (ilk tepeden sonraki direnç): a
    neckline = a

    if a > b < c and dip_close_enough and a > b and c > b:
        # Kırılım kontrolü: son kapanışlar neckline'ı geçti mi?
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < neckline:
                return False
        return True

    return False
