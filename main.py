import requests
from os.path import exists
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


def load_voting_data(party):
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
                        vote = current_tag[len('Result.'):]
                        votes[vote].add(paragraph)
                        if result.attrib['Identifier'] == 'NI':
                            for independent_mep in result:
                                if independent_mep.text in party.members:
                                    vote = current_tag[len('Result.'):]
                                    votes[vote].add(paragraph)
        print(votes)


if __name__ == "__main__":
    mep_data = load_mep_data()
    independents = [political_group for political_group in mep_data if political_group.name == 'Non-attached Members'][0]
    fidesz = independents.get_member_party('Fidesz-Magyar Polgári Szövetség-Kereszténydemokrata Néppárt')
    load_voting_data(fidesz)
