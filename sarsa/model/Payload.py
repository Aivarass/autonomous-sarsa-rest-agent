from enum import Enum

class Payloads(Enum):
    POST_1 = '{"name": "apple", "description": "fruit", "quantity": 1}'
    POST_2 = '{"name": "", "description": "missing name", "quantity": 1}'
    POST_3 = '{"name": "banana", "quantity": -5}'
    POST_4 = '{"description": "no name field", "quantity": 1}'
    POST_5 = '{}'
    PUT_1 = '{"name": "updated", "description": "changed", "quantity": 10}'
    PUT_2 = '{"name": "", "description": "empty name", "quantity": 1}'
    PUT_3 = '{"quantity": 5}'
    PUT_4 = '{"name": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
    PUT_5 = 'not json at all'
    PATCH_1 = '{"quantity": 99}'
    PATCH_2 = '{"name": "patched"}'
    PATCH_3 = '{"unknownField": "test"}'
    PATCH_4 = '{"quantity": null}'
    PATCH_5 = '{"name": ""}'