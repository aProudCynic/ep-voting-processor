from datetime import datetime, date
import os
from os.path import exists
from time import sleep
from typing import (
    List,
    Optional,
    Tuple,
)
from re import sub

import requests
from bs4 import BeautifulSoup, Tag
import xml.etree.ElementTree as ET
import re
import logging
import pickle

from const import FIRST_DATE_OF_NINTH_EP_SESSION
from loader.eu_political_group_loader import extract_political_group_memberships, load_default_political_groups
from loader.loader_util import extract_period_from
from logger import create_logger
from models import (
    EUPoliticalGroup,
    NationalParty,
    MEP,
    Membership,
)


def parse_xml(xml_data) -> Tuple[str, Optional[str], str, str]:
    mep_name = xml_data.find('fullName').text
    mep_party_container = xml_data.find('nationalPoliticalGroup')
    mep_party = mep_party_container.text if mep_party_container else None
    mep_political_group = xml_data.find('politicalGroup').text
    mep_id = xml_data.find('id').text
    return mep_name, mep_party, mep_political_group, mep_id


def fetch_mep_xml(url: str) -> str:
    cache_file_name = sub(r"[^a-z0-9]", "", url)
    cache_file_uri = f"xml/{cache_file_name}.xml"
    if os.path.exists(cache_file_uri):
        with open(cache_file_uri) as cached_xml:
            return cached_xml.read()
    else:
        response = requests.get(url)
        content = response.text
        with open(cache_file_uri, "w") as cached_xml:
            cached_xml.write(content)
        return content


def load_default_list() -> List[EUPoliticalGroup]:
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
        same_party_membership = meps_political_group.get_member_party_by_name(mep_party_name)
        if not same_party_membership:
            meps_party = NationalParty(mep_party_name)
            meps_political_group.members.add(Membership(meps_party, FIRST_DATE_OF_NINTH_EP_SESSION))
        else:
            meps_party = same_party_membership
        mep = MEP(mep_id, mep_name)
        meps_party.members.add(Membership(mep, FIRST_DATE_OF_NINTH_EP_SESSION))
    return political_groups


def parse_to_date(mep_data, tag_name):
    unparsed_date = mep_data.find(tag_name).text
    return None if unparsed_date == 'ONGOING' else datetime.strptime(unparsed_date, "%d/%m/%Y").date()


def search_meps_party_in_other_groups(
        political_groups: list[EUPoliticalGroup],
        meps_party_name: str,
        date_at_check: date,
) -> Optional[NationalParty]:
    date_to_check = date.today() if date_at_check is None else date_at_check
    other_groups_containing_party = [
        political_group
        for political_group in political_groups
        if political_group.get_member_party_by_name(meps_party_name, date_to_check)
    ]
    assert len(other_groups_containing_party) < 2
    # TODO resolve memberships' date
    return other_groups_containing_party[0].get_member_party_by_name(meps_party_name, date_at_check) if len(other_groups_containing_party) == 1 else None


def add_outgoing_meps(political_groups: list[EUPoliticalGroup]):
    mep_xml = fetch_mep_xml("https://www.europarl.europa.eu/meps/en/incoming-outgoing/outgoing/xml")
    xml_tree = ET.ElementTree(ET.fromstring(mep_xml))
    outgoing_data = xml_tree.getroot()
    for mep_data in outgoing_data:
        political_group_id = mep_data.find("politicalGroup").attrib['bodyCode']
        try:
            meps_political_group = [
                political_group for political_group in political_groups if political_group_id in political_group.ids
            ][0]
        except Exception as e:
            print(political_group_id)
            raise e
        meps_party_name = mep_data.find("nationalPoliticalGroup").text
        print(meps_party_name)
        start_date = parse_to_date(mep_data, "mandate-start")
        end_date = parse_to_date(mep_data, "mandate-end")
        meps_party = meps_political_group.get_member_party_by_name(meps_party_name)
        if meps_party is None:
            meps_party = search_meps_party_in_other_groups(political_groups, meps_party_name, end_date)
            if meps_party is None:
                meps_party = NationalParty(meps_party_name)
                meps_political_group.members.add(Membership(meps_party, start_date))
        name = mep_data.find("fullName").text
        id = mep_data.find("id").text

        mep = MEP(id, name)
        membership = Membership(mep, start_date, end_date)
        meps_party.members.add(membership)


def create_mep_from(mep_data: ET.Element) -> MEP:
    mep_id = mep_data.find('id').text
    mep_name = mep_data.find('fullName').text
    country = mep_data.find('country').text
    return MEP(mep_id, mep_name, country)

def create_meps_from(xml_address: str) -> set[MEP]:
    mep_xml = fetch_mep_xml(xml_address)
    xml_tree = ET.ElementTree(ET.fromstring(mep_xml))
    root_data = xml_tree.getroot()
    return {create_mep_from(mep_data) for mep_data in root_data}

def create_national_party_from(mep_data: ET.Element) -> Optional[NationalParty]:
    party_name_container = mep_data.find('nationalPoliticalGroup')
    if party_name_container is None or not party_name_container.text:
        return None
    party_name = party_name_container.text
    if party_name == "Independent":
        return NationalParty(party_name)
    country = mep_data.find('country').text
    return NationalParty(party_name, country)
    

def create_national_parties_from(xml_address: str) -> set[NationalParty]:
    mep_xml = fetch_mep_xml(xml_address)
    xml_tree = ET.ElementTree(ET.fromstring(mep_xml))
    root_data = xml_tree.getroot()
    return {create_national_party_from(mep_data) for mep_data in root_data}


def load_mep_data() -> tuple[List[EUPoliticalGroup], List[NationalParty]]:
    cache_folder = "cache"
    eu_groups_file_uri = f"{cache_folder}/eu_groups.pkl"
    national_party_file_uri = f"{cache_folder}/national_parties.pkl"
    if exists(eu_groups_file_uri) and exists(national_party_file_uri):
        with open(eu_groups_file_uri, "rb") as eu_groups_file:
            eu_groups = pickle.load(eu_groups_file)
        with open(national_party_file_uri, "rb") as national_party_file:
            national_parties = pickle.load(national_party_file)
        return eu_groups, national_parties
    else:
        eu_groups, national_parties = fetch_mep_data()
        with open(eu_groups_file_uri, "wb") as eu_groups_file:
            pickle.dump(eu_groups, eu_groups_file)
        with open(national_party_file_uri, "wb") as national_party_file:
            pickle.dump(national_parties, national_party_file)
        return eu_groups, national_parties



def fetch_mep_data() -> tuple[List[EUPoliticalGroup], List[NationalParty]]:
    logger = create_logger()
    current_meps = create_meps_from("https://www.europarl.europa.eu/meps/en/full-list/xml/")
    former_meps = create_meps_from("https://www.europarl.europa.eu/meps/en/incoming-outgoing/outgoing/xml")
    all_meps = current_meps.union(former_meps)
    national_parties = create_national_parties_from("https://www.europarl.europa.eu/meps/en/full-list/xml/").union(
        create_national_parties_from("https://www.europarl.europa.eu/meps/en/incoming-outgoing/outgoing/xml").union(
            create_national_parties_from("https://www.europarl.europa.eu/meps/en/incoming-outgoing/incoming/xml")            
        )
    )
    political_groups = load_default_political_groups()
    for mep in all_meps:
        url_name_part = mep.name.upper().replace(" ", "_")
        mep_data_url = f"https://www.europarl.europa.eu/meps/en/{mep.id}/{url_name_part}/history/9#detailedcardmep"
        soup = extract_soup_from(mep_data_url)
        logging.info(f"processing {mep_data_url}...")
        details_containers = soup.select(".erpl_meps-status-list > .erpl_meps-status > ul")
        if len(details_containers) > 0:
            national_parties_container = details_containers[1]
            national_parties_container_children = national_parties_container.findChildren("li" , recursive=False)
            for national_party_data_container in national_parties_container_children:
                unparsed_period = national_party_data_container.select_one("strong").text
                national_party_membership_period = extract_period_from(unparsed_period)
                national_party_name, national_party_nation = extract_national_party_from(national_party_data_container.text, unparsed_period)
                national_parties_found = [party for party in national_parties if party.name == national_party_name and party.country == national_party_nation]
                assert len(national_parties_found) < 2
                national_party = national_parties_found[0] if len(national_parties_found) == 1 else NationalParty(national_party_name, national_party_nation)
                national_party.members.add(Membership(mep, national_party_membership_period))
                if len(national_parties_found) == 0:
                    national_parties.add(national_party)
            eu_group_memberships_data = extract_political_group_memberships(details_containers)
            for eu_group_name, eu_group_membership_period in eu_group_memberships_data:
                political_group = find_political_group_by_name(political_groups, eu_group_name)
                political_group_membership = Membership(mep, eu_group_membership_period)
                political_group.members.add(political_group_membership)
        else:
            logger.warn(f"No details for {mep_data_url}, skipping")
    return political_groups, national_parties


def find_political_group_by_name(political_groups_to_be_searched: list[EUPoliticalGroup], political_group_name: str) -> EUPoliticalGroup:
    found_groups = [group for group in political_groups_to_be_searched if group.has_name(political_group_name)]
    assert len(found_groups) == 1, f"No political group named {political_group_name} found"
    return found_groups[0]


def party_is_member_of_group(political_group: EUPoliticalGroup, national_party: NationalParty) -> bool:
    national_parties_found = [membership for membership in political_group.members._memberships if membership == national_party]
    assert len(national_parties_found) < 2
    return national_parties_found == 1


def extract_national_party_from(child: str, unparsed_period: str) -> tuple[str, str]:
    party_name_start = len(unparsed_period) + len(" : ")
    party_name_end = child.rindex(" (")
    party_name = child[party_name_start:party_name_end]
    party_nation_start = party_name_end + len(" (")
    party_nation = child[party_nation_start:-1]
    return party_name, party_nation
  

def extract_last_name(mep_name):
    # David McAllister is the only MEP with non-capitalized last name
    return re.findall(r" [^a-z]+$| McALLISTER$", mep_name)[0][1:]

def extract_soup_from(url: str) -> BeautifulSoup:
    try:
        page = requests.get(url)
    except Exception:
        sleep(3)
        page = requests.get(url)
    return BeautifulSoup(page.content, 'html.parser')
