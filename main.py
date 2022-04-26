from collections import Counter
from datetime import (
    date,
    timedelta,
)
from os.path import exists
from time import sleep
from typing import Optional
from sys import stdout

import requests
import logging
import xml.etree.ElementTree as ElementTree

from const import (
    FIRST_DATE_OF_NINTH_EP_SESSION,
    DATE_OF_FIDESZ_QUITTING_EPP_EP_GROUP,
)
from mep_data_loader import load_mep_data
from models import EUPoliticalGroup

VOTING_RECORD_FILE_PATH = 'voting_record.xml'

VOTES = [
    'For',
    'Against',
    'Abstention',
]


def acquire_voting_data(date_to_examine, logger, offline=False) -> Optional[str]:
    filename = f"xml/{date_to_examine}.xml"
    if exists(filename):
        return filename
    elif not offline:
        response = requests.get(f'https://www.europarl.europa.eu/doceo/document/PV-9-{date_to_examine}-RCV_FR.xml')
        if response.status_code == 200:
            with open(filename, "wb") as voting_record_file:
                voting_record_file.write(response.content)
            return filename
        elif response.status_code == 404:
            logger.debug(f'file for {date_to_examine} is missing, skipping on the assumption that no vote took place')
            return None
    else:
        logger.debug(f'file for {date_to_examine} is missing, skipping due to offline mode')


def select_max_voted(votes: Counter) -> Optional[str]:
    max_voted = max(votes, key=votes.get)
    return max_voted if votes[max_voted] > 0 else None


def process_voting_data(fidesz, start_date=FIRST_DATE_OF_NINTH_EP_SESSION, end_date=date.today(), offline=False):
    logger = create_logger()
    fidesz_political_group_voting_comparisons = {
        political_group_name_ids: Counter(same=0, different=0) for political_group_name_ids in EUPoliticalGroup.id_name_pairings
    }
    date_to_examine = start_date
    fidesz_mep_ids = [fidesz_member.id for fidesz_member in fidesz.members.get_members_at(date_to_examine)]
    while date_to_examine <= end_date:
        filename = acquire_voting_data(date_to_examine, logger, offline)
        if filename:
            with open(filename) as file:
                xml_tree = ElementTree.parse(file)
                root = xml_tree.getroot()
                for political_group_name in EUPoliticalGroup.id_name_pairings:
                    for roll_call_vote_result in root:
                        if roll_call_vote_result.tag == "RollCallVote.Result":
                            epp_votes = Counter({vote: 0 for vote in VOTES})
                            fidesz_votes = Counter({vote: 0 for vote in VOTES})
                            voting_description = roll_call_vote_result.find("RollCallVote.Description.Text")
                            voting_identifier = voting_description.text if voting_description.text is not None else f' {voting_description.find("a").text} {voting_description.find("a").tail}'
                            logger.debug(f'processing {voting_identifier}')
                            for vote in VOTES:
                                result_by_vote = roll_call_vote_result.find(f'Result.{vote}')
                                if result_by_vote:
                                    for political_group_votes in result_by_vote:
                                        political_group_id = political_group_votes.attrib['Identifier']
                                        # TODO: process membeship change as part of the model, use that instead of baked-in condition
                                        fidesz_eu_parliamentary_group = 'NI' if date_to_examine >= DATE_OF_FIDESZ_QUITTING_EPP_EP_GROUP else 'PPE'
                                        if political_group_id in EUPoliticalGroup.id_name_pairings[political_group_name]:
                                            epp_votes[vote] = len(political_group_votes)
                                        if political_group_id == fidesz_eu_parliamentary_group:
                                            for independent_mep_voting in political_group_votes:
                                                if independent_mep_voting.attrib['PersId'] in fidesz_mep_ids:
                                                    fidesz_votes[vote] = fidesz_votes.get(vote, 0) + 1
                            logger.debug(f'{political_group_name}: {epp_votes}')
                            logger.debug(f'Fidesz: {fidesz_votes}')
                            epp_majority_vote = select_max_voted(epp_votes)
                            fidesz_majority_vote = select_max_voted(fidesz_votes)
                            if epp_majority_vote is not None and fidesz_majority_vote is not None:
                                if epp_majority_vote == fidesz_majority_vote:
                                    logger.debug(f'both voted {fidesz_majority_vote}')
                                    fidesz_political_group_voting_comparisons[political_group_name]['same'] = fidesz_political_group_voting_comparisons[political_group_name]['same'] + 1
                                else:
                                    logger.debug(f'Fidesz voted {fidesz_majority_vote} while {political_group_name} with {epp_majority_vote}')
                                    fidesz_political_group_voting_comparisons[political_group_name]['different'] = fidesz_political_group_voting_comparisons[political_group_name]['different'] + 1
        date_to_examine = date_to_examine + timedelta(days=1)
        if not offline:
            sleep(1)
    logger.info(fidesz_political_group_voting_comparisons)
    percentages = {political_group_name: fidesz_political_group_voting_comparisons[political_group_name]['same'] / (fidesz_political_group_voting_comparisons[political_group_name]['same'] + fidesz_political_group_voting_comparisons[political_group_name]['different']) * 100 for political_group_name in EUPoliticalGroup.id_name_pairings}
    logger.info(percentages)


def create_logger():
    logging.basicConfig(filename='logger.log', encoding='utf-8', level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


if __name__ == "__main__":
    mep_data = load_mep_data()
    independents = [political_group for political_group in mep_data if political_group.name == 'Non-attached Members'][0]
    fidesz = independents.get_member_party('Fidesz-Magyar Polgári Szövetség-Kereszténydemokrata Néppárt')
    process_voting_data(fidesz, FIRST_DATE_OF_NINTH_EP_SESSION, DATE_OF_FIDESZ_QUITTING_EPP_EP_GROUP, True)
    process_voting_data(fidesz, DATE_OF_FIDESZ_QUITTING_EPP_EP_GROUP + timedelta(days=1), date.today(), True)
