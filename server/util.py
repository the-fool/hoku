def scale(value, d_min, d_max, r_min, r_max):
    # Figure out how 'wide' each range is
    r_span = r_max - r_min
    d_span = d_max - d_min

    # Convert the left range into a 0-1 range (float)
    value_scaled = float(value - r_min) / float(r_span)

    # Convert the 0-1 range into a value in the right range.
    return int(d_min + (value_scaled * d_span))


def cent_to_midi(value):
    return scale(value, 0, 100, 0, 127)
