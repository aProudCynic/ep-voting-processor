from datetime import datetime
from time import mktime, strptime
from models import Period


def extract_period_from(unparsed_period: str) -> Period:
    if " / " in unparsed_period:
        dates = unparsed_period.split(" / ")
        start_date = parse_datetime_from(dates[0])
        end_date = parse_datetime_from(dates[1])
        return Period(start_date, end_date)
    elif "..." in unparsed_period:
        start_date = parse_datetime_from(unparsed_period[:10])
        return Period(start_date)
    else:
        raise AssertionError(
            f"Neither divider character nor ellipsis is detected in date string: {unparsed_period}")


def parse_datetime_from(day_month_year_string: str):
    parsed_data = strptime(day_month_year_string, "%d-%m-%Y")
    time_tuple = mktime(parsed_data)
    extracted_datetime = datetime.fromtimestamp(time_tuple)
    return extracted_datetime.date()
