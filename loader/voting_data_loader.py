from typing import Optional
from os import makedirs
from os.path import exists
import requests


def load_voting_data(date_to_examine, logger, offline=False) -> Optional[str]:
    foldername = "xml"
    filename = f"{foldername}/{date_to_examine}.xml"
    if exists(filename):
        return filename
    elif not offline:
        if not exists(foldername):
            makedirs(foldername)
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
