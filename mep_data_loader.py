from typing import List

import requests
import xml.etree.ElementTree as ET
import re

from const import FIRST_DATE_OF_NINTH_EP_SESSION
from models import (
    EUPoliticalGroup,
    NationalParty,
    MEP,
    Membership,
)


def parse_xml(xml_data):
    mep_name = xml_data.find('fullName').text
    mep_party = xml_data.find('nationalPoliticalGroup').text
    mep_political_group = xml_data.find('politicalGroup').text
    mep_id = xml_data.find('id').text
    return mep_name, mep_party, mep_political_group, mep_id


def fetch_mep_xml(url: str) -> str:
    response = requests.get(url)
    return response.text


def load_mep_data() -> List[EUPoliticalGroup]:
    mep_xml = fetch_mep_xml("https://www.europarl.europa.eu/meps/en/full-list/xml/")
    xml_tree = ET.ElementTree(ET.fromstring(mep_xml))
    meps_data = xml_tree.getroot()
    political_groups = []
    for mep_data in meps_data:
        mep_name, mep_party_name, mep_political_group_name, mep_id = parse_xml(mep_data)
        same_political_groups = [
            political_group for political_group in political_groups if political_group.name == mep_political_group_name
        ]
        if len(same_political_groups) == 0:
            meps_political_group = EUPoliticalGroup(mep_political_group_name)
            political_groups.append(meps_political_group)
        else:
            assert len(same_political_groups) == 1
            meps_political_group = same_political_groups[0]
        same_party_membership = meps_political_group.get_member_party(mep_party_name)
        if not same_party_membership:
            meps_party = NationalParty(mep_party_name)
            meps_political_group.members.add(Membership(meps_party, FIRST_DATE_OF_NINTH_EP_SESSION))
        else:
            meps_party = same_party_membership
        mep = MEP(mep_id, mep_name)
        meps_party.members.add(Membership(mep, FIRST_DATE_OF_NINTH_EP_SESSION))
    return political_groups


def extract_last_name(mep_name):
    # David McAllister is the only MEP with non-capitalized last name
    return re.findall(r" [^a-z]+$| McALLISTER$", mep_name)[0][1:]
