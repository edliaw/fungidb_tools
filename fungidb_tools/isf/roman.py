"""Convert between integer and roman numerals.

http://code.activestate.com/recipes/81611-roman-numerals/
"""

NUMERAL_MAP = zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
)


def int_to_roman(i):
    result = []
    for integer, numeral in NUMERAL_MAP:
        count = int(i / integer)
        result.append(numeral * count)
        i -= integer * count
    return ''.join(result)


def roman_to_int(n):
    n = unicode(n).upper()

    i = result = 0
    for integer, numeral in NUMERAL_MAP:
        while n[i:i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    return result
