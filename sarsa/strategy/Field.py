from enum import Enum


class Field(Enum):
    NONE = 0
    NAME = 1
    QUANTITY = 2
    DESCRIPTION = 3
    PRICE = 4
    ITEM_ID = 5
    DISCOUNT_ID = 6
    DISCOUNT = 7
    POINTS_ID = 8
    POINTS = 9
    ALL = 10
    UNKNOWN = 11