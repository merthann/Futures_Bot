def is_inverse_head_shoulders(df, shoulder_tolerance=0.02, breakout_confirm_candles=2):
    closes = df['close'].values
    if len(closes) < 60:
        return False

    l, h, r = closes[-50], closes[-40], closes[-30]  # left, head, right tops
    nl, nh, nr = closes[-35], closes[-25], closes[-15]  # left shoulder, head bottom, right shoulder

    shoulder_similarity = abs(nl - nr) <= shoulder_tolerance * nh
    neckline = max(l, r)  # boyun çizgisi: iki tepeyi bağlayan en yüksek seviye

    # Formasyon + kırılım kontrolü
    if l > h < r and nl < l and nr < r and shoulder_similarity:
        # Kırılım kontrolü: son kapanışlar neckline üstüne çıktı mı?
        for i in range(1, breakout_confirm_candles + 1):
            if closes[-i] < neckline:
                return False
        return True

    return False
