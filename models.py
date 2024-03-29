from typing import (
    Iterable,
    Optional,
    Union,
    TypeVar,
    Generic,
)

from datetime import date


class MEP:
    id: str
    name: str
    country: str

    def __init__(self, id: str, name: str, country: str):
        self.id = id
        self.name = name
        self.country = country

    def __key(self):
        return (self.id)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__key() == other.__key()
        return NotImplemented


class Period:
    start_date: date
    end_date: Union[date, None]

    def __init__(self, start_date: date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date

    def is_date_in_period(self, date_to_check: date) -> bool:
        return date_to_check is not None and date_to_check >= self.start_date and (self.end_date is None or date_to_check <= self.end_date)

    def is_other_period_in_period(self, period_to_check) -> bool:
        return (
            self.start_date is None
            or self.is_date_in_period(period_to_check.start_date)
        ) and (
            self.end_date is None
            or self.is_date_in_period(period_to_check.end_date)
        )

    def __key(self):
        return (self.start_date, self.end_date)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__key() == other.__key()
        return NotImplemented


T = TypeVar('T')


class Membership(Generic[T]):
    member: T
    period: Period

    def __init__(self, member, period: Period):
        self.member = member
        self.period = period


class NationalPartyMembership(Membership[MEP]):
    pass


class Memberships(Generic[T]):
    _memberships: list[Membership[T]]

    def __init__(self):
        self._memberships = []

    def get_members_at(self, date_to_check: date):
        return [membership.member for membership in self._memberships if membership.period.is_date_in_period(date_to_check)]
    
    def add(self, membership: Membership[T]):
        self._memberships.append(membership)

    def set_membership_period_for(self, member: T, period: Period):
        memberships = [membership for membership in self._memberships if membership.member == member]
        assert len(Membership) == 1
        memberships[0].period = period


class NationalParty:
    name: str
    country: Optional[str]
    members: Memberships[MEP]

    def __init__(self, name, country=None):
        self.name = name
        self.country = country
        self.members = Memberships()

    def __key(self):
        return (self.name, self.country)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__key() == other.__key()
        return NotImplemented


class EUPoliticalGroup:

    # TODO eliminate
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

    ids: list[str]
    name: str
    members: Memberships[MEP]

    def __init__(self, name: str, ids: list[str], aliases=None):
        self.name = name
        self.ids = ids
        self.members = Memberships()
        self.aliases = aliases

    def get_member_party_by_name(self, member_party_name: str, member_at=date.today()) -> NationalParty:
        found_national_parties = [
            member for member in self.members.get_members_at(member_at) if isinstance(member, NationalParty) and member_party_name == member.name
        ]
        assert len(found_national_parties) == 1 or len(found_national_parties) == 0
        return found_national_parties[0] if len(found_national_parties) else None

    def is_party_a_member(self, national_party: NationalParty, member_at=date.today()) -> bool:
        party_members = national_party.members.get_members_at(member_at)
        return any(self.is_mep_a_member(party_member) for party_member in party_members)
    
    def is_mep_a_member(self, mep: MEP, member_at=date.today()) -> bool:
        group_members = self.members.get_members_at(member_at)
        return mep in group_members

    def has_name(self, name: str) -> bool:
        return self.name == name or (self.aliases is not None and name in self.aliases)

    @classmethod
    def _pair_ids_with(self, name):
        ids = self.id_name_pairings[name]
        assert ids is not None
        return ids
