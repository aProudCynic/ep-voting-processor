from loader_util import extract_period_from
from models import EUPoliticalGroup, Period


def load_default_political_groups():
    return {
        EUPoliticalGroup("Group of the European People's Party (Christian Democrats)", ["PPE", "EPP"]),
        EUPoliticalGroup("Group of the Progressive Alliance of Socialists and Democrats in the European Parliament", ["S&amp;D", "S&D"]),
        EUPoliticalGroup("Renew Europe Group", ["Renew"]),
        EUPoliticalGroup("European Conservatives and Reformists Group", ["ECR"]),
        EUPoliticalGroup("Group of the Greens/European Free Alliance", ["Verts/ALE", "Greens/EFA"]),
        EUPoliticalGroup("The Left group in the European Parliament - GUE/NGL", ["The Left", "GUE/NGL"], ["Group of the European United Left - Nordic Green Left"]),
        EUPoliticalGroup("Identity and Democracy Group", ["ID"]),
        EUPoliticalGroup("Non-attached Members", ["NI"])
    }


def extract_political_group_memberships(details_containers) -> list[tuple[str, Period]]:
    political_groups_container = details_containers[0]
    political_groups_container_children = political_groups_container.findChildren("li" , recursive=False)
    return [extract_political_group_membership_data_from(child) for child in political_groups_container_children]


def extract_political_group_membership_data_from(political_groups_container_child) -> tuple[str, Period]:
    unparsed_period = political_groups_container_child.select_one("strong").text
    period = extract_period_from(unparsed_period)
    political_group_name = extract_political_group_from(political_groups_container_child.text, unparsed_period)
    return political_group_name, period


def extract_political_group_from(party_membership_info: str, unparsed_period: str) -> str:
    if "Non-attached Members" in party_membership_info:
        return "Non-attached Members"
    group_name_start = len(unparsed_period) + len(" : ")
    group_name_end = party_membership_info.rindex(" - ")
    return party_membership_info[group_name_start:group_name_end]
