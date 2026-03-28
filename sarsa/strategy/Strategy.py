from enum import Enum


class Strategy(Enum):
    NONE = 0
    VALID = 1
    NULL_INJECT = 2
    NEGATIVE = 3
    BOUNDARY = 4
    STRUCTURE = 5
    INJECTION = 6
    TYPE_CONFUSE = 7
    ENCODING = 8