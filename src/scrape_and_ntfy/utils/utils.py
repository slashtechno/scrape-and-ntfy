import re


def convert_to_float(n):
    try:
        # Remove non-numeric characters
        n = re.sub(r"[^\d.]", "", n)
        return float(n)
    except (ValueError, TypeError):
        # ValueError if a float could not be extracted
        # TypeError if for whatever reason n is not a string (might be None)
        return False
