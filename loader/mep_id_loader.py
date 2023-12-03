from datetime import date, timedelta
import logging
from os.path import exists
import pickle
from xml.etree import ElementTree
from const import (
    FIRST_DATE_OF_NINTH_EP_SESSION,
    VOTES,
)
from loader.voting_data_loader import load_voting_data

from logger import create_logger


def load_mep_ids() -> dict[int, int]:
    cache_folder = "cache"
    mep_ids_file_uri = f"{cache_folder}/mep_ids.pkl"
    if exists(mep_ids_file_uri):
        with open(mep_ids_file_uri, "rb") as mep_ids_file:
            mep_ids = pickle.load(mep_ids_file)
    else:
        mep_ids = fetch_mep_ids()
        with open(mep_ids_file_uri, "wb") as mep_ids_file:
            pickle.dump(mep_ids, mep_ids_file)
    return mep_ids


def fetch_mep_ids() -> dict[int, int]:
    mep_id_pers_id_pairings = dict()
    logger = create_logger()
    logger.setLevel(logging.INFO)
    date_to_examine = FIRST_DATE_OF_NINTH_EP_SESSION
    end_date = date.today()
    while date_to_examine <= end_date:
        filename = load_voting_data(date_to_examine, logger, True)
        if filename:
            with open(filename) as file:
                xml_tree = ElementTree.parse(file)
                root = xml_tree.getroot()
                for roll_call_vote_result in root:
                    if roll_call_vote_result.tag == "RollCallVote.Result":
                        for vote in VOTES:
                            result_by_vote = roll_call_vote_result.find(f'Result.{vote}')
                            if result_by_vote:
                                for political_group_votes in result_by_vote:
                                    for mep_voting in political_group_votes:
                                        voting_mep_id = mep_voting.attrib.get('PersId')
                                        alternate_id = mep_voting.attrib['MepId']
                                        if voting_mep_id:
                                            mep_id_pers_id_pairings[alternate_id] = voting_mep_id
                                            logger.debug(f"pairing added: {alternate_id} - {voting_mep_id}")
        date_to_examine = date_to_examine + timedelta(days=1)
    return mep_id_pers_id_pairings