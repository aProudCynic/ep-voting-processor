from collections import Counter
from typing import Optional

import requests
import logging
import xml.etree.ElementTree as ElementTree

from mep_data_loader import load_mep_data

VOTING_RECORD_FILE_PATH = 'voting_record.xml'

VOTES = [
    'For',
    'Against',
    'Abstention',
]


def download_voting_data():
    response = requests.get('https://www.europarl.europa.eu/doceo/document/PV-9-2022-03-01-RCV_FR.xml')
    with open(VOTING_RECORD_FILE_PATH, "wb") as voting_record_file:
        voting_record_file.write(response.content)


def select_max_voted(votes: Counter) -> Optional[str]:
    max_voted = max(votes, key=votes.get)
    return max_voted if votes[max_voted] > 0 else None


def process_voting_data(fidesz):
    fidesz_epp_voting_comparison = Counter(same=0, different=0)
    fidesz_mep_ids = [fidesz_membership.member.id for fidesz_membership in fidesz.members]
    if not exists(VOTING_RECORD_FILE_PATH):
        download_voting_data()
    with open(VOTING_RECORD_FILE_PATH) as file:
        xml_tree = ElementTree.parse(file)
        root = xml_tree.getroot()
        for roll_call_vote_result in root:
            epp_votes = Counter({vote: 0 for vote in VOTES})
            fidesz_votes = Counter({vote: 0 for vote in VOTES})
            for child in roll_call_vote_result:
                if(child.tag == 'RollCallVote.Description.Text'):
                    voting_identifier = f'{child.text} {child.find("a").text} {child.find("a").tail}'
                    logging.debug(f'processing {voting_identifier}')
                elif 'Result.' in child.tag:
                    current_tag = child.tag
                    vote = current_tag[len('Result.'):]
                    for political_group_votes in child:
                        political_group_id = political_group_votes.attrib['Identifier']
                        if political_group_id == 'PPE':
                            epp_votes[vote] = len(political_group_votes)
                        elif political_group_id == 'NI':
                            for independent_mep_voting in political_group_votes:
                                if independent_mep_voting.attrib['PersId'] in fidesz_mep_ids:
                                    fidesz_votes[vote] = fidesz_votes.get(vote, 0) + 1
            logging.debug(f'EPP: {epp_votes}')
            logging.debug(f'Fidesz: {fidesz_votes}')
            epp_majority_vote = select_max_voted(epp_votes)
            fidesz_majority_vote = select_max_voted(fidesz_votes)
            if epp_majority_vote is not None and fidesz_majority_vote is not None:
                if epp_majority_vote == fidesz_majority_vote:
                    logging.debug(f'both voted {fidesz_majority_vote}')
                    fidesz_epp_voting_comparison['same'] = fidesz_epp_voting_comparison['same'] + 1
                else:
                    logging.debug(f'Fidesz voted {fidesz_majority_vote} while EPP with {epp_majority_vote}')
                    fidesz_epp_voting_comparison['different'] = fidesz_epp_voting_comparison['different'] + 1
        logging.info(fidesz_epp_voting_comparison)


if __name__ == "__main__":
    mep_data = load_mep_data()
    independents = [political_group for political_group in mep_data if political_group.name == 'Non-attached Members'][0]
    fidesz = independents.get_member_party('Fidesz-Magyar Polgári Szövetség-Kereszténydemokrata Néppárt')
    process_voting_data(fidesz)
