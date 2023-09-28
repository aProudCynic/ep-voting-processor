from datetime import date
import unittest

from models import Period


class TestPeriod(unittest.TestCase):

    def test_period_inside_other_fully_inside(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 9, 27), date(2023, 9, 28))
        self.assertTrue(period.is_other_period_in_period(period_inside_other_period))

    def test_period_inside_other_same_start_earlier_end(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 9, 26), date(2023, 9, 28))
        self.assertTrue(period.is_other_period_in_period(period_inside_other_period))

    def test_period_inside_other_earlier_start_same_end(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 9, 27), date(2023, 9, 29))
        self.assertTrue(period.is_other_period_in_period(period_inside_other_period))

    def test_period_inside_other_same(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 9, 26), date(2023, 9, 29))
        self.assertTrue(period.is_other_period_in_period(period_inside_other_period))

    def test_period_inside_earlier_start(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 9, 25), date(2023, 9, 29))
        self.assertFalse(period.is_other_period_in_period(period_inside_other_period))

    def test_period_inside_later_end(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 9, 26), date(2023, 9, 30))
        self.assertFalse(period.is_other_period_in_period(period_inside_other_period))

    def test_period_inside_no_overlap(self):
        period = Period(date(2023, 9, 26), date(2023, 9, 29)) 
        period_inside_other_period = Period(date(2023, 8, 26), date(2023, 8, 30))
        self.assertFalse(period.is_other_period_in_period(period_inside_other_period))
