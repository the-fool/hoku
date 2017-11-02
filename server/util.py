def scale(value, d_min, d_max, r_min, r_max):
    return float(r_max - r_min) * (value - d_min) / (d_max - d_min) + r_min


def cent_to_midi(value):
    return int(scale(value, 0, 100, 0, 127))


def custom_domain_to_midi(value, domain_min, domain_max):
    return int(scale(value, domain_min, domain_max, 0, 127))
