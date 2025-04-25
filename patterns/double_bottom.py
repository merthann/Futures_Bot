def is_double_bottom(df, tolerance=0.02):  # %2 tolerans
    closes = df['close'].values
    if len(closes) < 50:
        return False

    a, b, c = closes[-30], closes[-20], closes[-10]

    # Toleranslı dip kontrolü
    dip_close_enough = abs(b - c) < tolerance * c

    if a > b < c and dip_close_enough and a > b and c > b:
        return True
    return False
