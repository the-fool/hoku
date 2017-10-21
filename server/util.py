def scale(value, d_min, d_max, r_min, r_max):
    # Figure out how 'wide' each range is
    r_span = r_max - r_min
    d_span = d_max - d_min

    # Convert the left range into a 0-1 range (float)
    value_scaled = float(value - r_min) / float(r_span)

    return float(r_max - r_min) * (value - d_min) / (d_max - d_min) + r_min


def cent_to_midi(value):
    return int(scale(value, 0, 100, 0, 127))


def custom_domain_to_midi(value, domain_min, domain_max):
    return int(scale(value, domain_min, domain_max, 0, 127))
