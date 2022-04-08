import requests
from os.path import exists

VOTING_RECORD_FILE_PATH = 'voting_record.xml'


def download_voting_data():
    response = requests.get('https://www.europarl.europa.eu/doceo/document/PV-9-2022-03-01-RCV_FR.xml')
    open(VOTING_RECORD_FILE_PATH, "wb").write(response.content)


def load_voting_data():
    if not exists(VOTING_RECORD_FILE_PATH):
        download_voting_data()


if __name__ == "__main__":
    load_voting_data()
