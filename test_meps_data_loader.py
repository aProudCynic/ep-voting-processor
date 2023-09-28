import unittest

from mep_data_loader import extract_national_party_from


class MepsDataLoader(unittest.TestCase):

    def test_extract_national_party_from_party_name(self):
        self.assertEqual("Bezpartyjna", extract_national_party_from("02-07-2019 / 16-07-2019 : Bezpartyjna (Poland)", "02-07-2019 / 16-07-2019")[0])


    def test_extract_national_party_from_party_country(self):
        self.assertEqual("Poland", extract_national_party_from("02-07-2019 / 16-07-2019 : Bezpartyjna (Poland)", "02-07-2019 / 16-07-2019")[1])
