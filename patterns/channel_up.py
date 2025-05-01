def is_channel_up(df, tolerance=0.005, breakdown_candles=2):
    highs = df['high'].values[-20:]
    lows = df['low'].values[-20:]
    closes = df['close'].values

    rising = all(
        highs[i] >= highs[i - 1] * (1 - tolerance) and
        lows[i] >= lows[i - 1] * (1 - tolerance)
        for i in range(1, len(highs))
    )

    if not rising:
        return False

    # Breakdown kontrolü: son kapanışlar kanalın altına düşmüş mü
    min_low = min(lows)
    for i in range(1, breakdown_candles + 1):
        if closes[-i] < min_low:
            return False  # Aşağı kırılım varsa long sinyali verilmez

    return True
