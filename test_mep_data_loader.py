import unittest
from collections import Counter

from main import calculate_cohesion
from mep_data_loader import extract_last_name, extract_national_party_from


class TestExtractLastName(unittest.TestCase):

    def test_extract_last_name(self):
        self.assertEqual(extract_last_name("Magdalena ADAMOWICZ"), "ADAMOWICZ")

    def test_extract_last_name_mcallister(self):
        self.assertEqual(extract_last_name("David McALLISTER"), "McALLISTER")

    def test_extract_last_name_special_characters(self):
        self.assertEqual(extract_last_name("Ernő SCHALLER-BAROSS"), "SCHALLER-BAROSS")


class TestCalculateCohesion(unittest.TestCase):

    def test_total_cohesion(self):
        self.assertEqual(100.0, calculate_cohesion(Counter({'For': 9, 'Against': 0, 'Abstention': 0})))

    def test_high_cohesion(self):
        self.assertEqual(90.0, calculate_cohesion(Counter({'For': 9, 'Against': 1, 'Abstention': 0})))

    def test_low_cohesion(self):
        self.assertEqual(50.0, calculate_cohesion(Counter({'For': 2, 'Against': 4, 'Abstention': 2})))

class TestExtractNationalParty(unittest.TestCase):

    def test_extract_national_party_from_party_name(self):
        self.assertEqual("Bezpartyjna", extract_national_party_from("02-07-2019 / 16-07-2019 : Bezpartyjna (Poland)", "02-07-2019 / 16-07-2019")[0])


    def test_extract_national_party_from_party_country(self):
        self.assertEqual("Poland", extract_national_party_from("02-07-2019 / 16-07-2019 : Bezpartyjna (Poland)", "02-07-2019 / 16-07-2019")[1])
