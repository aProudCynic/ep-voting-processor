from datetime import date
import unittest
from main import find_group_ids_of_party

from models import MEP, EUPoliticalGroup, Membership, NationalParty, Period


class TestFindGroupIdOfParty(unittest.TestCase):

    def test_find_group_id_of_party(self):
        date_to_examine = date.today()
        national_party_mep = MEP(1, "Test MEP", "HU")
        expected_result = ["TEST_ID"]

        political_group = EUPoliticalGroup("test_group_name", expected_result)
        political_group.members.add(Membership(national_party_mep, Period(date.today())))

        national_party = NationalParty("test", "HU")
        national_party_membership = Membership(national_party_mep, Period(date.today()))
        national_party.members.add(national_party_membership)

        result = find_group_ids_of_party(date_to_examine, {political_group}, national_party)
        self.assertEqual(expected_result, result)


    def test_find_group_id_of_party_negative_error(self):
        date_to_examine = date.today()
        national_party_mep = MEP(1, "Test MEP", "HU")

        political_group = EUPoliticalGroup("test_group_name", ["TEST_ID"])
        political_group.members.add(Membership(national_party_mep, Period(date.today())))

        national_party = NationalParty("test", "HU")
        national_party_membership = Membership(national_party_mep, Period(date.today()))
        national_party.members.add(national_party_membership)

        try:
            _ = find_group_ids_of_party(date_to_examine, {political_group}, NationalParty("test2", "HU"))
            self.assertFalse(True)
        except AssertionError:
            self.assertTrue(True)


    def test_find_group_id_of_party_negative(self):
        date_to_examine = date.today()
        national_party_mep = MEP(1, "Test MEP", "HU")
        expected_result = ["POS"]

        political_group_positive = EUPoliticalGroup("test_group_positive", expected_result)
        political_group_positive.members.add(Membership(national_party_mep, Period(date.today())))

        political_group_negative = EUPoliticalGroup("test_group_negative", ["NEG"])

        national_party = NationalParty("test", "HU")
        national_party_membership = Membership(national_party_mep, Period(date.today()))
        national_party.members.add(national_party_membership)

        result = find_group_ids_of_party(date_to_examine, {political_group_positive, political_group_negative}, national_party)
        self.assertEqual(expected_result, result)
