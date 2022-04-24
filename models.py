from typing import (
    Union,
    TypeVar,
    Generic,
)

from datetime import date


class MEP:
    id: str
    first_name: str
    last_name: str

    def __init__(self, id, first_name, last_name):
        self.id = id
        self.last_name = last_name
        self.first_name = first_name


class Period:
    start_date: date
    end_date: Union[date, None]

    def __init__(self, start_date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date


T = TypeVar('T')


class Membership(Generic[T]):
    member: T
    period: Period

    def __init__(self, member, start_date, end_date=None):
        self.member = member
        self.period = Period(start_date, end_date)


class NationalPartyMembership(Membership[MEP]):
    pass


class NationalParty:
    name: str
    members: list[NationalPartyMembership]

    def __init__(self, name):
        self.name = name
        self.members = []


class EUPoliticalGroupMembership(Membership[Union[NationalParty, MEP]]):
    pass


class EUPoliticalGroup:

    id_name_pairings = {
        "Group of the European People's Party (Christian Democrats)": "PPE",
        "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&amp;D",
        "Renew Europe Group": "Renew",
        "European Conservatives and Reformists Group": "ECR",
        "Group of the Greens/European Free Alliance": "Verts/ALE",
        "The Left group in the European Parliament - GUE/NGL": "The Left",
        "Identity and Democracy Group": "ID",
        "Non-attached Members": "NI",
    }

    name: str
    members: list[EUPoliticalGroupMembership]

    def __init__(self, name):
        self.id = self._pair_id_with(name)
        self.name = name
        self.members = []

    def get_member_party(self, member_party_name: str) -> NationalParty:
        found_national_parties = [
            member.member for member in self.members if isinstance(member.member, NationalParty) and member_party_name == member.member.name
        ]
        assert len(found_national_parties) == 1
        return found_national_parties[0]

    @classmethod
    def _pair_id_with(self, name):
        id = self.id_name_pairings[name]
        assert id is not None
        return id
