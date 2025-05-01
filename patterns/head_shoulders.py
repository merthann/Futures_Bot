def is_head_shoulders(df, shoulder_tolerance=0.02, breakdown_confirm_candles=2):
    closes = df['close'].values
    if len(closes) < 60:
        return False

    l, h, r = closes[-50], closes[-40], closes[-30]  # left, head, right dips
    nl, nh, nr = closes[-35], closes[-25], closes[-15]  # left shoulder, head peak, right shoulder

    shoulder_similarity = abs(nl - nr) <= shoulder_tolerance * nh
    neckline = min(l, r)  # boyun çizgisi: iki dipten en düşük olan

    # Formasyon + kırılım kontrolü
    if l < h > r and nl > l and nr > r and shoulder_similarity:
        # Kırılım kontrolü: son kapanışlar neckline altına indi mi?
        for i in range(1, breakdown_confirm_candles + 1):
            if closes[-i] > neckline:
                return False
        return True

    return False
