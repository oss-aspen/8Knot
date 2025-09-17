from enum import Enum


class SearchItem(Enum):
    """
    Enum representing different types of things that can be searched for in the search bar
    """

    REPO = "repo"
    ORG = "org"
    OTHER = "other"

    @classmethod
    def from_id(cls, identifier) -> "SearchItem":
        """
        Determine type of search item based on its identifying value
        """
        if isinstance(identifier, str):
            return cls.REPO if identifier.isnumeric() else cls.ORG
        elif isinstance(identifier, int):
            return cls.REPO
        else:
            return cls.OTHER
