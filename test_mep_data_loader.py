import unittest

from mep_data_loader import extract_last_name


class TestExtractLastName(unittest.TestCase):

    def test_extract_last_name(self):
        self.assertEqual(extract_last_name("Magdalena ADAMOWICZ"), "ADAMOWICZ")

    def test_extract_last_name_mcallister(self):
        self.assertEqual(extract_last_name("David McALLISTER"), "McALLISTER")

    def test_extract_last_name_special_characters(self):
        self.assertEqual(extract_last_name("Ernő SCHALLER-BAROSS"), "SCHALLER-BAROSS")
