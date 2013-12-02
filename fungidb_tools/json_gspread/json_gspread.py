"""Convert gspread worksheets in to JSON format."""


def json_gspread(worksheet):
    """Return list of dicts for the worksheet's rows.

    All values are interpreted as strings.

    """
    return [r for r in dict_gspread(worksheet)]


def dict_gspread(worksheet):
    """Generate dictionaries from each row in the worksheet."""
    rows = iter(worksheet.get_all_values())
    header = next(rows)

    for row in rows:
        yield dict(zip(header, row))
