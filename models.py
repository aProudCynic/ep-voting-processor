from typing import (
    Union,
    TypeVar,
    Generic,
)

from datetime import date


class MEP:
    first_name: str
    last_name: str

    def __init__(self, first_name, last_name):
        self.last_name = last_name
        self.first_name = first_name


class Period:
    start_date: date
    end_date: Union[date, None]

    def __init__(self, start_date) -> None:
        self.start_date = start_date
        self.end_date = None


T = TypeVar('T')


class Membership(Generic[T]):
    member: T
    membership: Period

    def __init__(self, member, start_date):
        self.member = member
        self.membership = Period(start_date)


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
    name: str
    members: list[EUPoliticalGroupMembership]

    def __init__(self, name):
        self.name = name
        self.members = []

    def get_member_party(self, member_party_name: str) -> NationalParty:
        found_national_parties = [
            member.member for member in self.members if isinstance(member.member, NationalParty) and member_party_name == member.member.name
        ]
        assert len(found_national_parties) == 1
        return found_national_parties[0]
