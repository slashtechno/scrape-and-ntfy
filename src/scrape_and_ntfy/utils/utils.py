def is_digit(n):
    try:
        float(n)
        return True
    except ValueError:
        return False