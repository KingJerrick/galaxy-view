def int_to_roman(num: int) -> str:
    """"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman = ""
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman += syms[i]
            num -= val[i]
        i += 1
    return roman

def int_to_letters(num: int) -> str:
    """1 -> a, 26 -> z, 27 -> aa"""
    result = ""
    while num > 0:
        num -= 1  # Excel 列号是从 1 开始的，所以先减 1
        result = chr(num % 26 + ord('a')) + result
        num //= 26
    return result