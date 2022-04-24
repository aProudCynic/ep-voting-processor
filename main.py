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

VOTING_RECORD_FILE_PATH = 'voting_record.xml'

VOTES = [
    'For',
    'Against',
    'Abstention',
]


def download_voting_data(date_to_examine, logger) -> Optional[str]:
    filename = f"xml/{date_to_examine}.xml"
    if exists(filename):
        return filename
    else:
        response = requests.get(f'https://www.europarl.europa.eu/doceo/document/PV-9-{date_to_examine}-RCV_FR.xml')
        if response.status_code == 200:
            with open(filename, "wb") as voting_record_file:
                voting_record_file.write(response.content)
            return filename
        elif response.status_code == 404:
            logger.debug(f'file for {date_to_examine} is missing, skipping on the assumption that it is ')
            return None


def select_max_voted(votes: Counter) -> Optional[str]:
    max_voted = max(votes, key=votes.get)
    return max_voted if votes[max_voted] > 0 else None


def process_voting_data(fidesz):
    logger = create_logger()
    fidesz_epp_voting_comparison = Counter(same=0, different=0)
    fidesz_mep_ids = [fidesz_membership.member.id for fidesz_membership in fidesz.members]
    date_to_examine = date.today()
    while date_to_examine >= FIRST_DATE_OF_NINTH_EP_SESSION:
        filename = download_voting_data(date_to_examine, logger)
        if filename:
            with open(filename) as file:
                xml_tree = ElementTree.parse(file)
                root = xml_tree.getroot()
                for roll_call_vote_result in root:
                    epp_votes = Counter({vote: 0 for vote in VOTES})
                    fidesz_votes = Counter({vote: 0 for vote in VOTES})
                    for child in roll_call_vote_result:
                        if(child.tag == 'RollCallVote.Description.Text'):
                            url_part = child.find("a")
                            voting_identifier = f'{child.text}'
                            if url_part:
                                voting_identifier += f' {url_part.text} {url_part.tail}'
                            logger.debug(f'processing {voting_identifier}')
                        elif 'Result.' in child.tag:
                            current_tag = child.tag
                            vote = current_tag[len('Result.'):]
                            for political_group_votes in child:
                                political_group_id = political_group_votes.attrib['Identifier']
                                fidesz_eu_parliamentary_group = 'NI' if date_to_examine >= DATE_OF_FIDESZ_QUITTING_EPP_EP_GROUP else 'PPE'
                                if political_group_id == 'PPE':
                                    epp_votes[vote] = len(political_group_votes)
                                if political_group_id == fidesz_eu_parliamentary_group:
                                    for independent_mep_voting in political_group_votes:
                                        if independent_mep_voting.attrib['PersId'] in fidesz_mep_ids:
                                            fidesz_votes[vote] = fidesz_votes.get(vote, 0) + 1
                    logger.debug(f'EPP: {epp_votes}')
                    logger.debug(f'Fidesz: {fidesz_votes}')
                    epp_majority_vote = select_max_voted(epp_votes)
                    fidesz_majority_vote = select_max_voted(fidesz_votes)
                    if epp_majority_vote is not None and fidesz_majority_vote is not None:
                        if epp_majority_vote == fidesz_majority_vote:
                            logger.debug(f'both voted {fidesz_majority_vote}')
                            fidesz_epp_voting_comparison['same'] = fidesz_epp_voting_comparison['same'] + 1
                        else:
                            logger.debug(f'Fidesz voted {fidesz_majority_vote} while EPP with {epp_majority_vote}')
                            fidesz_epp_voting_comparison['different'] = fidesz_epp_voting_comparison['different'] + 1
        date_to_examine = date_to_examine - timedelta(days=1)
        sleep(1)
    logger.info(fidesz_epp_voting_comparison)


def create_logger():
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
    process_voting_data(fidesz)
