from typing import (
    Union,
    TypeVar,
    Generic,
)

from datetime import date


class MEP:
    id: str
    name: str

    def __init__(self, id, name):
        self.id = id
        self.name = name


class Period:
    start_date: date
    end_date: Union[date, None]

    def __init__(self, start_date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date

    def is_in_period(self, date_to_check: date):
        return date_to_check >= self.start_date and (self.end_date is None or date_to_check <= self.end_date)


T = TypeVar('T')


class Membership(Generic[T]):
    member: T
    period: Period

    def __init__(self, member, start_date, end_date=None):
        self.member = member
        self.period = Period(start_date, end_date)


class NationalPartyMembership(Membership[MEP]):
    pass


class Memberships(Generic[T]):
    _membeships = list[Membership[T]]

    def __init__(self):
        self._memberships = []

    def get_members_at(self, date_to_check: date):
        return [membership.member for membership in self._memberships if membership.period.is_in_period(date_to_check)]
    
    def add(self, membership: Membership[T]):
        self._memberships.append(membership)


class NationalParty:
    name: str
    members: Memberships[MEP]

    def __init__(self, name):
        self.name = name
        self.members = Memberships()


class EUPoliticalGroup:

    id_name_pairings = {
        "Group of the European People's Party (Christian Democrats)": [
            "PPE",
            "EPP",
        ],
        "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": [
            "S&amp;D",
            "S&D",
        ],
        "Renew Europe Group": [
            "Renew",
        ],
        "European Conservatives and Reformists Group": [
            "ECR",
        ],
        "Group of the Greens/European Free Alliance": [
            "Verts/ALE",
            "Greens/EFA",
        ],
        "The Left group in the European Parliament - GUE/NGL": [
            "The Left",
            "GUE/NGL",
        ],
        "Identity and Democracy Group": [
            "ID"
        ],
        "Non-attached Members": [
            "NI"
        ],
    }

    name: str
    members: Memberships[Union[NationalParty, MEP]]

    def __init__(self, name):
        self.ids = self._pair_ids_with(name)
        self.name = name
        self.members = Memberships()

    def get_member_party(self, member_party_name: str, member_at=date.today()) -> NationalParty:
        found_national_parties = [
            member for member in self.members.get_members_at(member_at) if isinstance(member, NationalParty) and member_party_name == member.name
        ]
        assert len(found_national_parties) == 1 or len(found_national_parties) == 0
        return found_national_parties[0] if len(found_national_parties) else None

    @classmethod
    def _pair_ids_with(self, name):
        ids = self.id_name_pairings[name]
        assert ids is not None
        return ids
