def is_head_shoulders(df, shoulder_tolerance=0.02):  # %2 omuz farkı toleransı
    closes = df['close'].values
    if len(closes) < 60:
        return False

    l, h, r = closes[-50], closes[-40], closes[-30]
    nl, nh, nr = closes[-35], closes[-25], closes[-15]

    shoulder_similarity = abs(nl - nr) <= shoulder_tolerance * nh

    if l < h > r and nl > l and nr > r and shoulder_similarity:
        return True
    return False
