def is_double_top(df, tolerance=0.02):  # %2 tolerans
    closes = df['close'].values
    if len(closes) < 50:
        return False

    a, b, c = closes[-30], closes[-20], closes[-10]

    top_close_enough = abs(b - a) <= tolerance * b

    if a < b > c and top_close_enough and a < b and c < b:
        return True
    return False
