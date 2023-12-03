from collections import Counter
from datetime import (
    date,
    timedelta,
)
from time import sleep
from typing import Iterable, Optional
from sys import stdout
import logging
import xml.etree.ElementTree as ElementTree

from const import (
    DK_NAME,
    FIRST_DATE_OF_NINTH_EP_SESSION,
    DATE_OF_FIDESZ_QUITTING_EPP_EP_GROUP,
    KDNP_NAME,
    MOMENTUM_NAME,
    VOTES,
)
from loader.mep_id_loader import load_mep_ids
from loader.voting_data_loader import load_voting_data
from logger import create_logger
from loader.mep_data_loader import load_mep_data
from models import MEP, EUPoliticalGroup, NationalParty

VOTING_RECORD_FILE_PATH = 'voting_record.xml'


def select_max_voted(votes: Counter) -> Optional[str]:
    max_voted = max(votes, key=votes.get)
    return max_voted if votes[max_voted] > 0 else None


def calculate_cohesion(fidesz_votes: Counter) -> float:
    fidesz_majority_vote = select_max_voted(fidesz_votes)
    majority_vote_count = fidesz_votes[fidesz_majority_vote]
    total_vote_count = sum(fidesz_votes.values())
    return majority_vote_count / total_vote_count * 100


def is_mep_party_member(mep_voting: ElementTree.Element, party_meps: list[MEP], mep_id_pers_id_pairings: dict[int, int]) -> bool:
    voting_mep_id = mep_voting.attrib.get('PersId')
    alternate_id = mep_voting.attrib['MepId']
    if not voting_mep_id:
        voting_mep_id = mep_id_pers_id_pairings.get(alternate_id)
    if not voting_mep_id:
        # TODO implement backup based on name and country
        logging.error(f"No ID found for {mep_voting.text} (ID: {voting_mep_id}, alternative: {alternate_id})")
        return False
    party_mep_ids = [mep.id for mep in party_meps]
    return voting_mep_id in party_mep_ids


def find_group_ids_of_party(date_to_examine: date, political_groups: set[EUPoliticalGroup], national_party: NationalParty) -> list[str]:
    groups_of_party = [group for group in political_groups if group.is_party_a_member(national_party, date_to_examine)]
    assert len(groups_of_party) == 1
    return groups_of_party[0].ids


def extract_national_vote_counter(roll_call_vote_result, eu_parliamentary_group_of_party: list[str], national_party_meps: list[MEP], mep_id_pers_id_pairings: dict[int, int]) -> Counter:
    national_party_votes_counter = Counter({vote: 0 for vote in VOTES})
    for vote in VOTES:
        result_by_vote = roll_call_vote_result.find(f'Result.{vote}')
        if result_by_vote:
            for political_group_votes in result_by_vote:
                political_group_id = political_group_votes.attrib['Identifier']
                if political_group_id in eu_parliamentary_group_of_party:
                    for mep_voting in political_group_votes:
                        if is_mep_party_member(mep_voting, national_party_meps, mep_id_pers_id_pairings):
                            national_party_votes_counter[vote] = national_party_votes_counter.get(vote, 0) + 1
    return national_party_votes_counter


def extract_political_group_votes_counter(roll_call_vote_result, political_group: EUPoliticalGroup) -> Counter:
    political_group_votes_counter = Counter({vote: 0 for vote in VOTES})
    for vote in VOTES:
        result_by_vote = roll_call_vote_result.find(f'Result.{vote}')
        if result_by_vote:
            for political_group_votes in result_by_vote:
                political_group_id = political_group_votes.attrib['Identifier']
                if political_group_id in political_group.ids:
                    political_group_votes_counter[vote] = len(political_group_votes)
    return political_group_votes_counter


def compare_voting_cohesion_with_ep_groups(national_party: NationalParty, eu_political_groups: list[EUPoliticalGroup], mep_id_pers_id_pairings, start_date=FIRST_DATE_OF_NINTH_EP_SESSION, end_date=date.today(), offline=False):
    logger = create_logger()
    logger.setLevel(logging.INFO)
    political_group_voting_comparisons = {
        political_group_name_ids: Counter(same=0, different=0) for political_group_name_ids in EUPoliticalGroup.id_name_pairings
    }
    national_party_voting_cohesion_per_voting = []
    non_coherent_votings = set()
    date_to_examine = start_date
    national_party_meps = national_party.members.get_members_at(date_to_examine)
    while date_to_examine <= end_date:
        filename = load_voting_data(date_to_examine, logger, offline)
        if filename:
            with open(filename) as file:
                eu_parliamentary_group_of_party = find_group_ids_of_party(date_to_examine, eu_political_groups, national_party)
                xml_tree = ElementTree.parse(file)
                root = xml_tree.getroot()
                for roll_call_vote_result in root:
                    if roll_call_vote_result.tag == "RollCallVote.Result":
                        voting_description = roll_call_vote_result.find("RollCallVote.Description.Text")
                        voting_identifier = voting_description.text if voting_description.text and voting_description.text.strip() else f'{voting_description.find("a").text} {voting_description.find("a").tail}'    
                        logger.debug(f'processing {voting_identifier}')
                        national_party_votes_counter = extract_national_vote_counter(roll_call_vote_result, eu_parliamentary_group_of_party, national_party_meps, mep_id_pers_id_pairings)
                        logger.debug(f'national party: {national_party_votes_counter}')
                        party_majority_vote = select_max_voted(national_party_votes_counter)
                        if party_majority_vote is not None:
                            cohesion = calculate_cohesion(national_party_votes_counter)
                            national_party_voting_cohesion_per_voting.append(calculate_cohesion(national_party_votes_counter))
                            if cohesion < 100:
                                non_coherent_votings.add(f'{date_to_examine} - {voting_identifier}')
                            for political_group in eu_political_groups:
                                political_group_votes_counter = extract_political_group_votes_counter(roll_call_vote_result, political_group)
                                political_group_majority_vote = select_max_voted(political_group_votes_counter)
                                if political_group_majority_vote is not None:
                                    comparison_result = 'same' if political_group_majority_vote == party_majority_vote else 'different'
                                    logger.debug(f'{comparison_result}: {national_party.name} voted {party_majority_vote} while {political_group.name} with {political_group_majority_vote}')
                                    political_group_voting_comparisons[political_group.name][comparison_result] = political_group_voting_comparisons[political_group.name][comparison_result] + 1
        date_to_examine = date_to_examine + timedelta(days=1)
        if not offline:
            sleep(1)
    logger.info(political_group_voting_comparisons)
    percentages = {political_group_name: political_group_voting_comparisons[political_group_name]['same'] / (political_group_voting_comparisons[political_group_name]['same'] + political_group_voting_comparisons[political_group_name]['different']) * 100 for political_group_name in EUPoliticalGroup.id_name_pairings}
    logger.info(percentages)
    fidesz_cohesion_overall_average = sum(national_party_voting_cohesion_per_voting) / len(national_party_voting_cohesion_per_voting)
    logger.info(fidesz_cohesion_overall_average)
    logger.info(f"{len(non_coherent_votings)} non-coherent votings: {non_coherent_votings}")


def find_party_by_name_and_country(national_parties: Iterable[NationalParty], name: str, country: str):
    parties_by_name_and_country = [party for party in national_parties if party.name == name and party.country == country]
    assert len(parties_by_name_and_country) == 1
    return parties_by_name_and_country[0]
    

if __name__ == "__main__":
    eu_political_groups, national_parties = load_mep_data()
    mep_id_pers_id_pairings = load_mep_ids()
    party = find_party_by_name_and_country(national_parties, MOMENTUM_NAME, 'Hungary')
    compare_voting_cohesion_with_ep_groups(party, eu_political_groups, mep_id_pers_id_pairings, FIRST_DATE_OF_NINTH_EP_SESSION, date.today(), True)
