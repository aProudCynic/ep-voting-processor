from datetime import date
from typing import List

import requests
import xml.etree.ElementTree as ET
import re

from models import (
    EUPoliticalGroup,
    NationalParty,
    EUPoliticalGroupMembership,
    NationalPartyMembership,
    MEP,
)


def parse_xml(xml_data):
    mep_name = xml_data.find('fullName').text
    mep_party = xml_data.find('nationalPoliticalGroup').text
    mep_political_group = xml_data.find('politicalGroup').text
    return mep_name, mep_party, mep_political_group


def fetch_mep_xml() -> str:
    response = requests.get("https://www.europarl.europa.eu/meps/en/full-list/xml/")
    return response.text


def load_mep_data() -> List[EUPoliticalGroup]:
    mep_xml = fetch_mep_xml()
    xml_tree = ET.ElementTree(ET.fromstring(mep_xml))
    meps_data = xml_tree.getroot()
    political_groups = []
    for mep_data in meps_data:
        mep_name, mep_party_name, mep_political_group_name = parse_xml(mep_data)
        same_political_groups = [
            political_group for political_group in political_groups if political_group.name == mep_political_group_name
        ]
        if len(same_political_groups) == 0:
            meps_political_group = EUPoliticalGroup(mep_political_group_name)
            political_groups.append(meps_political_group)
        else:
            assert len(same_political_groups) == 1
            meps_political_group = same_political_groups[0]
        same_party_membership = [
            party_membership for party_membership in meps_political_group.members
            if party_membership.member and party_membership.member.name == mep_party_name
        ]
        if len(same_party_membership) == 0:
            meps_party = NationalParty(mep_party_name)
            meps_political_group.members.append(EUPoliticalGroupMembership(meps_party, date.today()))
        else:
            meps_party = same_party_membership[0].member
        try:
            # optional Mc included for McALLISTER
            last_name = re.findall(r" [^a-z]{1,}$|Mc[^a-z]{1,}$", mep_name)[0][1:]
        except IndexError as e:
            print(f'Regex not applicable to {mep_name}')
            raise e
        first_name = mep_name[:-len(last_name) - 1]
        mep = MEP(first_name, last_name)
        meps_party.members.append(NationalPartyMembership(mep, date.today()))
    return political_groups
