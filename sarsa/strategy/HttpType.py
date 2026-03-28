from enum import Enum


class HttpType(Enum):
    NONE = 0
    GET = 1
    GET_ALL = 2
    POST = 3
    PUT = 4
    PATCH = 5
    DELETE = 6