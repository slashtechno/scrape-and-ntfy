import re


def convert_to_float(n):
    try:
        # Remove non-numeric characters
        n = re.sub(r"[^\d.]", "", n)
        return float(n)
    except ValueError:
        return False