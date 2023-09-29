from time import strptime
from models import Period


def extract_period_from(unparsed_period: str) -> Period:
    if " / " in unparsed_period:
        dates = unparsed_period.split(" / ")
        start_date = strptime(dates[0], "%d-%m-%Y")
        end_date = strptime(dates[0], "%d-%m-%Y")
        return Period(start_date, end_date)
    elif "..." in unparsed_period:
        start_date = strptime(unparsed_period[:10], "%d-%m-%Y")
        return Period(start_date)
    else:
        raise AssertionError(f"Neither divider character nor ellipsis is detected in date string: {unparsed_period}")
  