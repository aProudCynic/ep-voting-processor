import datetime
import unittest

from loader.loader_util import extract_period_from


class TestExtractPeriodFrom(unittest.TestCase):

    def test_extract_period_from(self):
        result = extract_period_from("02-07-2019 / 31-01-2020")
        self.assertEqual(datetime.date(2019, 7, 2), result.start_date)
        self.assertEqual(datetime.date(2020, 1, 31), result.end_date)
        