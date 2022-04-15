import requests
from os.path import exists
import xml.etree.ElementTree as ElementTree

VOTING_RECORD_FILE_PATH = 'voting_record.xml'

FIDESZ_MEPS = [
    'Bocskor',
    'Deli',
    'Deutsch',
    'Gál',
    'Győri',
    'Gyürk',
    'Hidvéghi',
    'Járóka',
    'Kósa',
    'Schaller-Baross',
    'Trócsányi',
]

VOTES = [
    'For',
    'Against',
    'Abstention',
]

def download_voting_data():
    response = requests.get('https://www.europarl.europa.eu/doceo/document/PV-9-2022-03-01-RCV_FR.xml')
    with open(VOTING_RECORD_FILE_PATH, "wb") as voting_record_file:
        voting_record_file.write(response.content)


def load_voting_data():
    if not exists(VOTING_RECORD_FILE_PATH):
        download_voting_data()
    with open(VOTING_RECORD_FILE_PATH) as file:
        xml_tree = ElementTree.parse(file)
        root = xml_tree.getroot()
        votes = { vote:set() for vote in VOTES }
        for roll_call_vote_result in root:
            for child in roll_call_vote_result:
                if(child.tag == 'RollCallVote.Description.Text'):
                    paragraph = child.find('a').tail[len(' - '):]
                elif 'Result.' in child.tag:
                    current_tag = child.tag
                    for result in child:
                        if result.attrib['Identifier'] == 'NI':
                            for independent_mep in result:
                                if independent_mep.text in FIDESZ_MEPS:
                                    vote = current_tag[len('Result.'):]
                                    votes[vote].add(paragraph)
        print(votes)


if __name__ == "__main__":
    load_voting_data()
