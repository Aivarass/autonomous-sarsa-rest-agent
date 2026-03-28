import json
import random
from enum import Enum

# ── Enums matching the Java Strategy classes ──

class Endpoint(Enum):
    ITEMS = 0
    PRICES = 1
    DISCOUNTS = 2
    POINTS = 3

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

class Intensity(Enum):
    MILD = 0
    MODERATE = 1
    AGGRESSIVE = 2


# ── Constants ──

ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
SPECIAL = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
UNICODE = "äöü中文"

INT_MAX = 2_147_483_647
INT_MIN = -2_147_483_648
LONG_MAX = 9_223_372_036_854_775_807
FLOAT_MAX = 1.7976931348623157e+308


class PayloadGenerator:
    def __init__(self, seed=None):

        if seed is None:
            seed = random.randrange(1 << 30)
        self.rng = random.Random(seed)

        # Track IDs for nested resource generation (set by SarsaRestTester)
        self.last_item_id: int | None = None
        self.last_price_id: int | None = None
        self.last_discount_id: int | None = None

    # ========================== Category 1: VALID ==========================

    def valid(self):
        name = self._random_string(3, 20)
        desc = self._random_string(5, 50)
        qty = self.rng.randint(1, 1000)
        return json.dumps({"name": name, "description": desc, "quantity": qty})

    # ========================== Category 2: NULL ==========================

    def null_injection(self):
        variant = self.rng.randint(0, 4)
        name = self._random_string(3, 10)
        qty = self.rng.randint(0, 99)

        match variant:
            case 0: return json.dumps({"name": None, "description": "test", "quantity": qty})
            case 1: return json.dumps({"name": name, "description": None, "quantity": qty})
            case 2: return json.dumps({"name": name, "description": "test", "quantity": None})
            case 3: return json.dumps({"name": None, "description": None, "quantity": None})
            case 4: return json.dumps({"name": name, "quantity": None})
            case _: return self.null_injection()

    # ========================== Category 3: NEGATIVE ==========================

    def negative(self):
        variant = self.rng.randint(0, 3)
        name = self._random_string(3, 10)
        neg_qty = -(self.rng.randint(1, 10000))

        match variant:
            case 0: return json.dumps({"name": name, "quantity": neg_qty})
            case 1: return json.dumps({"name": name, "quantity": INT_MIN})
            case 2: return json.dumps({"name": name, "quantity": -0.5})
            case 3: return json.dumps({"name": "", "quantity": neg_qty})
            case _: return self.negative()

    # ========================== Category 4: BOUNDARY ==========================

    def boundary(self):
        variant = self.rng.randint(0, 5)
        name = self._random_string(3, 10)

        match variant:
            case 0: return json.dumps({"name": "", "quantity": 0})
            case 1: return json.dumps({"name": name, "quantity": INT_MAX})
            case 2: return json.dumps({"name": name, "quantity": 0})
            case 3: return json.dumps({"name": self._random_string(1000, 2000), "quantity": 1})
            case 4: return json.dumps({"name": name, "description": self._random_string(5000, 10000), "quantity": 1})
            case 5: return json.dumps({"name": " ", "quantity": 1})
            case _: return self.boundary()

    # ========================== Category 5: STRUCTURE ==========================

    def structure(self):
        variant = self.rng.randint(0, 6)
        name = self._random_string(3, 10)
        qty = self.rng.randint(0, 99)

        match variant:
            case 0: return json.dumps({})
            case 1: return json.dumps({"quantity": qty})
            case 2: return json.dumps({"name": name})
            case 3: return json.dumps({"name": name, "quantity": qty, "unknown": "extra", "hack": True})
            case 4: return json.dumps({"name": 12345, "quantity": "not a number"})
            case 5: return json.dumps({"name": ["array"], "quantity": {"object": True}})
            case 6: return f'{{"name": "{name}", "name": "duplicate", "quantity": {qty}}}'
            case _: return self.structure()

    # ========================== BONUS: Injection ==========================

    def injection(self):
        variant = self.rng.randint(0, 4)
        qty = self.rng.randint(0, 99)

        match variant:
            case 0: return json.dumps({"name": "'; DROP TABLE items; --", "quantity": qty})
            case 1: return json.dumps({"name": "1' OR '1'='1", "quantity": qty})
            case 2: return json.dumps({"name": "<script>alert('xss')</script>", "quantity": qty})
            case 3: return json.dumps({"name": "../../../etc/passwd", "quantity": qty})
            case 4: return f'{{"name": "{self._random_unicode_string(5, 15)}", "quantity": {qty}}}'
            case _: return self.injection()

    # ========================== Convenience ==========================

    def by_category(self, category: int) -> str:
        """Generate payload by category index (for SARSA action mapping).
        0=VALID, 1=NULL, 2=NEGATIVE, 3=BOUNDARY, 4=STRUCTURE, 5=INJECTION
        """
        match category:
            case 0: return self.valid()
            case 1: return self.null_injection()
            case 2: return self.negative()
            case 3: return self.boundary()
            case 4: return self.structure()
            case 5: return self.injection()
            case _: return self.valid()

    # ========================== Strategy-Aware Generation ==========================

    def generate(self, endpoint: Endpoint, field: Field, strategy: Strategy, intensity: Intensity) -> str:
        """Main entry point for strategy-aware SARSA payload generation."""
        match endpoint:
            case Endpoint.ITEMS:    return self._generate_items_payload(field, strategy, intensity)
            case Endpoint.PRICES:   return self._generate_prices_payload(field, strategy, intensity)
            case Endpoint.DISCOUNTS: return self._generate_discounts_payload(field, strategy, intensity)
            case Endpoint.POINTS:   return self._generate_points_payload(field, strategy, intensity)

    def generate_for_items(self, field: Field, strategy: Strategy, intensity: Intensity) -> str:
        """Legacy method for backwards compatibility."""
        return self._generate_items_payload(field, strategy, intensity)

    # ── Intensity helpers ──

    def _get_string_length(self, intensity: Intensity) -> int:
        match intensity:
            case Intensity.MILD:       return 3 + self.rng.randint(0, 9)
            case Intensity.MODERATE:   return 10 + self.rng.randint(0, 49)
            case Intensity.AGGRESSIVE: return 100 + self.rng.randint(0, 999)

    def _get_num_magnitude(self, intensity: Intensity) -> int:
        match intensity:
            case Intensity.MILD:       return 1 + self.rng.randint(0, 99)
            case Intensity.MODERATE:   return 1 + self.rng.randint(0, 9999)
            case Intensity.AGGRESSIVE: return 1 + self.rng.randint(0, INT_MAX // 2 - 1)

    # ── ID helpers ──

    def _get_item_id_json(self) -> str:
        item_id = self.last_item_id if self.last_item_id is not None else (self.rng.randint(1, 1000))
        return f'{{"id": {item_id}}}'

    def _get_price_id_json(self) -> str:
        price_id = self.last_price_id if self.last_price_id is not None else (self.rng.randint(1, 1000))
        return f'{{"id": {price_id}}}'

    def _get_discount_id_json(self) -> str:
        discount_id = self.last_discount_id if self.last_discount_id is not None else (self.rng.randint(1, 1000))
        return f'{{"id": {discount_id}}}'

    # ========================== ITEMS Endpoint ==========================

    def _generate_items_payload(self, field: Field, strategy: Strategy, intensity: Intensity) -> str:
        string_len = self._get_string_length(intensity)
        num_magnitude = self._get_num_magnitude(intensity)

        match strategy:
            case Strategy.VALID:        return self._items_valid(field, string_len)
            case Strategy.NULL_INJECT:  return self._items_null_inject(field, string_len)
            case Strategy.NEGATIVE:     return self._items_negative(field, num_magnitude)
            case Strategy.BOUNDARY:     return self._items_boundary(field, intensity)
            case Strategy.STRUCTURE:    return self._items_structure(field)
            case Strategy.INJECTION:    return self._items_injection(field)
            case Strategy.TYPE_CONFUSE: return self._items_type_confuse(field)
            case Strategy.ENCODING:     return self._items_encoding(field, string_len)
            case Strategy.NONE:         return self.valid()

    def _items_valid(self, field: Field, string_len: int) -> str:
        name = self._random_string(3, string_len)
        desc = self._random_string(5, string_len)
        qty = self.rng.randint(1, 1000)
        return json.dumps({"name": name, "description": desc, "quantity": qty})

    def _items_null_inject(self, field: Field, string_len: int) -> str:
        name = self._random_string(3, string_len)
        qty = self.rng.randint(0, 99)

        match field:
            case Field.NAME:        return json.dumps({"name": None, "description": "test", "quantity": qty})
            case Field.QUANTITY:    return json.dumps({"name": name, "description": "test", "quantity": None})
            case Field.DESCRIPTION: return json.dumps({"name": name, "description": None, "quantity": qty})
            case Field.ALL:         return json.dumps({"name": None, "description": None, "quantity": None})
            case _:                 return self.null_injection()

    def _items_negative(self, field: Field, magnitude: int) -> str:
        name = self._random_string(3, 10)
        neg_qty = -(self.rng.randint(1, magnitude))

        match field:
            case Field.QUANTITY: return json.dumps({"name": name, "quantity": neg_qty})
            case Field.NAME:    return json.dumps({"name": "", "quantity": neg_qty})
            case Field.ALL:     return json.dumps({"name": "", "description": "", "quantity": neg_qty})
            case _:             return self.negative()

    def _items_boundary(self, field: Field, intensity: Intensity) -> str:
        name = self._random_string(3, 10)

        match field:
            case Field.NAME:
                match intensity:
                    case Intensity.MILD:       return json.dumps({"name": "", "quantity": 1})
                    case Intensity.MODERATE:   return json.dumps({"name": self._random_string(100, 500), "quantity": 1})
                    case Intensity.AGGRESSIVE: return json.dumps({"name": self._random_string(5000, 10000), "quantity": 1})
            case Field.QUANTITY:
                match intensity:
                    case Intensity.MILD:       return json.dumps({"name": name, "quantity": 0})
                    case Intensity.MODERATE:   return json.dumps({"name": name, "quantity": INT_MAX // 2})
                    case Intensity.AGGRESSIVE: return json.dumps({"name": name, "quantity": INT_MAX})
            case Field.DESCRIPTION:
                return json.dumps({"name": name, "description": self._random_string(1000, 5000), "quantity": 1})
            case _:
                return self.boundary()

    def _items_structure(self, field: Field) -> str:
        name = self._random_string(3, 10)
        qty = self.rng.randint(0, 99)

        match field:
            case Field.NAME:    return json.dumps({"quantity": qty})
            case Field.QUANTITY: return json.dumps({"name": name})
            case Field.UNKNOWN: return json.dumps({"name": name, "quantity": qty, "unknown": "extra", "hack": True})
            case Field.ALL:     return json.dumps({})
            case _:             return self.structure()

    def _items_injection(self, field: Field) -> str:
        qty = self.rng.randint(0, 99)
        injections = [
            "'; DROP TABLE items; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${7*7}",
            "{{constructor.constructor('return this')()}}",
        ]
        inject = self.rng.choice(injections)

        match field:
            case Field.NAME:        return json.dumps({"name": inject, "quantity": qty})
            case Field.DESCRIPTION: return json.dumps({"name": "test", "description": inject, "quantity": qty})
            case _:                 return json.dumps({"name": inject, "description": inject, "quantity": qty})

    def _items_type_confuse(self, field: Field) -> str:
        name = self._random_string(3, 10)

        match field:
            case Field.NAME:        return json.dumps({"name": 12345, "quantity": 1})
            case Field.QUANTITY:    return json.dumps({"name": name, "quantity": "not a number"})
            case Field.DESCRIPTION: return json.dumps({"name": name, "description": ["array"], "quantity": 1})
            case Field.ALL:         return json.dumps({"name": 123, "description": {"nested": True}, "quantity": "string"})
            case _:                 return json.dumps({"name": 12345, "quantity": "not a number"})

    def _items_encoding(self, field: Field, string_len: int) -> str:
        unicode_str = self._random_unicode_string(5, max(5, string_len))
        qty = self.rng.randint(0, 99)

        match field:
            case Field.NAME:        return json.dumps({"name": unicode_str, "quantity": qty})
            case Field.DESCRIPTION: return json.dumps({"name": "test", "description": unicode_str, "quantity": qty})
            case _:                 return json.dumps({"name": unicode_str, "description": unicode_str, "quantity": qty})

    # ========================== PRICES Endpoint ==========================

    def _generate_prices_payload(self, field: Field, strategy: Strategy, intensity: Intensity) -> str:
        num_magnitude = self._get_num_magnitude(intensity)

        match strategy:
            case Strategy.VALID:        return self._prices_valid(field)
            case Strategy.NULL_INJECT:  return self._prices_null_inject(field)
            case Strategy.NEGATIVE:     return self._prices_negative(field, num_magnitude)
            case Strategy.BOUNDARY:     return self._prices_boundary(field, intensity)
            case Strategy.STRUCTURE:    return self._prices_structure(field)
            case Strategy.INJECTION:    return self._prices_injection(field)
            case Strategy.TYPE_CONFUSE: return self._prices_type_confuse(field)
            case Strategy.ENCODING:     return self._prices_valid(field)
            case Strategy.NONE:         return self._prices_valid(field)

    def _prices_valid(self, field: Field) -> str:
        price = 10.0 + self.rng.random() * 990.0
        item_json = self._get_item_id_json()
        return f'{{"item": {item_json}, "price": {price:.2f}}}'

    def _prices_null_inject(self, field: Field) -> str:
        price = 10.0 + self.rng.random() * 100.0
        item_json = self._get_item_id_json()

        match field:
            case Field.PRICE:   return f'{{"item": {item_json}, "price": null}}'
            case Field.ITEM_ID: return f'{{"item": null, "price": {price}}}'
            case Field.ALL:     return '{"item": null, "price": null}'
            case _:
                variant = self.rng.randint(0, 1)
                if variant == 0:
                    return f'{{"item": null, "price": {price}}}'
                else:
                    return f'{{"item": {item_json}, "price": null}}'

    def _prices_negative(self, field: Field, magnitude: int) -> str:
        item_json = self._get_item_id_json()
        neg_price = -(self.rng.random() * magnitude + 1)

        match field:
            case Field.PRICE:   return f'{{"item": {item_json}, "price": {neg_price:.2f}}}'
            case Field.ITEM_ID: return '{"item": {"id": -1}, "price": 50.0}'
            case Field.ALL:     return f'{{"item": {{"id": -1}}, "price": {neg_price:.2f}}}'
            case _:             return f'{{"item": {item_json}, "price": {neg_price:.2f}}}'

    def _prices_boundary(self, field: Field, intensity: Intensity) -> str:
        item_json = self._get_item_id_json()

        match field:
            case Field.PRICE:
                match intensity:
                    case Intensity.MILD:       return f'{{"item": {item_json}, "price": 0}}'
                    case Intensity.MODERATE:   return f'{{"item": {item_json}, "price": {FLOAT_MAX / 2}}}'
                    case Intensity.AGGRESSIVE: return f'{{"item": {item_json}, "price": {FLOAT_MAX}}}'
            case Field.ITEM_ID:
                match intensity:
                    case Intensity.MILD:       return '{"item": {"id": 0}, "price": 50.0}'
                    case Intensity.MODERATE:   return f'{{"item": {{"id": {INT_MAX}}}, "price": 50.0}}'
                    case Intensity.AGGRESSIVE: return f'{{"item": {{"id": {LONG_MAX}}}, "price": 50.0}}'
            case _:
                return '{"item": {"id": 0}, "price": 0}'

    def _prices_structure(self, field: Field) -> str:
        item_json = self._get_item_id_json()
        price = 50.0 + self.rng.random() * 50.0

        match field:
            case Field.PRICE:   return f'{{"item": {item_json}}}'
            case Field.ITEM_ID: return f'{{"price": {price}}}'
            case Field.UNKNOWN: return f'{{"item": {item_json}, "price": {price}, "currency": "USD", "tax": 0.1}}'
            case Field.ALL:     return '{}'
            case _:
                variant = self.rng.randint(0, 2)
                match variant:
                    case 0: return '{}'
                    case 1: return f'{{"price": {price}}}'
                    case 2: return f'{{"item": {item_json}}}'
                    case _: return self._prices_valid(field)

    def _prices_injection(self, field: Field) -> str:
        item_json = self._get_item_id_json()
        injections = [
            "'; DROP TABLE prices; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
        ]
        inject = self.rng.choice(injections)

        match field:
            case Field.PRICE:   return f'{{"item": {item_json}, "price": "{inject}"}}'
            case Field.ITEM_ID: return f'{{"item": {{"id": "{inject}"}}, "price": 50.0}}'
            case _:             return f'{{"item": {{"id": "{inject}"}}, "price": "{inject}"}}'

    def _prices_type_confuse(self, field: Field) -> str:
        item_json = self._get_item_id_json()

        match field:
            case Field.PRICE:   return f'{{"item": {item_json}, "price": "not a number"}}'
            case Field.ITEM_ID: return '{"item": "not an object", "price": 50.0}'
            case Field.ALL:     return '{"item": [1, 2, 3], "price": {"value": 50}}'
            case _:
                variant = self.rng.randint(0, 2)
                match variant:
                    case 0: return f'{{"item": {item_json}, "price": "fifty dollars"}}'
                    case 1: return '{"item": 12345, "price": 50.0}'
                    case 2: return f'{{"item": {item_json}, "price": [50, 60, 70]}}'
                    case _: return self._prices_valid(field)

    # ========================== DISCOUNTS Endpoint ==========================

    def _generate_discounts_payload(self, field: Field, strategy: Strategy, intensity: Intensity) -> str:
        num_magnitude = self._get_num_magnitude(intensity)

        match strategy:
            case Strategy.VALID:        return self._discounts_valid(field)
            case Strategy.NULL_INJECT:  return self._discounts_null_inject(field)
            case Strategy.NEGATIVE:     return self._discounts_negative(field, num_magnitude)
            case Strategy.BOUNDARY:     return self._discounts_boundary(field, intensity)
            case Strategy.STRUCTURE:    return self._discounts_structure(field)
            case Strategy.INJECTION:    return self._discounts_injection(field)
            case Strategy.TYPE_CONFUSE: return self._discounts_type_confuse(field)
            case Strategy.ENCODING:     return self._discounts_valid(field)
            case Strategy.NONE:         return self._discounts_valid(field)

    def _discounts_valid(self, field: Field) -> str:
        discount = self.rng.random() * 50.0
        price_json = self._get_price_id_json()
        return f'{{"price": {price_json}, "discount": {discount:.2f}}}'

    def _discounts_null_inject(self, field: Field) -> str:
        discount = 10.0 + self.rng.random() * 20.0
        price_json = self._get_price_id_json()

        match field:
            case Field.PRICE: return f'{{"price": null, "discount": {discount}}}'
            case Field.ALL:   return '{"price": null, "discount": null}'
            case _:
                variant = self.rng.randint(0, 1)
                if variant == 0:
                    return f'{{"price": null, "discount": {discount}}}'
                else:
                    return f'{{"price": {price_json}, "discount": null}}'

    def _discounts_negative(self, field: Field, magnitude: int) -> str:
        price_json = self._get_price_id_json()
        neg_discount = -(self.rng.random() * min(magnitude, 100) + 1)

        match field:
            case Field.PRICE: return '{"price": {"id": -1}, "discount": 10.0}'
            case Field.ALL:   return f'{{"price": {{"id": -1}}, "discount": {neg_discount:.2f}}}'
            case _:           return f'{{"price": {price_json}, "discount": {neg_discount:.2f}}}'

    def _discounts_boundary(self, field: Field, intensity: Intensity) -> str:
        price_json = self._get_price_id_json()

        match field:
            case Field.PRICE:
                match intensity:
                    case Intensity.MILD:       return '{"price": {"id": 0}, "discount": 10.0}'
                    case Intensity.MODERATE:   return f'{{"price": {{"id": {INT_MAX}}}, "discount": 10.0}}'
                    case Intensity.AGGRESSIVE: return f'{{"price": {{"id": {LONG_MAX}}}, "discount": 10.0}}'
            case _:
                match intensity:
                    case Intensity.MILD:       return f'{{"price": {price_json}, "discount": 0}}'
                    case Intensity.MODERATE:   return f'{{"price": {price_json}, "discount": 100}}'
                    case Intensity.AGGRESSIVE: return f'{{"price": {price_json}, "discount": {FLOAT_MAX}}}'

    def _discounts_structure(self, field: Field) -> str:
        price_json = self._get_price_id_json()
        discount = 15.0 + self.rng.random() * 20.0

        match field:
            case Field.PRICE:   return f'{{"discount": {discount}}}'
            case Field.UNKNOWN: return f'{{"price": {price_json}, "discount": {discount}, "code": "SAVE10", "expires": "2025-12-31"}}'
            case Field.ALL:     return '{}'
            case _:
                variant = self.rng.randint(0, 2)
                match variant:
                    case 0: return '{}'
                    case 1: return f'{{"discount": {discount}}}'
                    case 2: return f'{{"price": {price_json}}}'
                    case _: return self._discounts_valid(field)

    def _discounts_injection(self, field: Field) -> str:
        price_json = self._get_price_id_json()
        injections = [
            "'; DROP TABLE discounts; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
        ]
        inject = self.rng.choice(injections)

        match field:
            case Field.PRICE: return f'{{"price": {{"id": "{inject}"}}, "discount": 10.0}}'
            case _:           return f'{{"price": {{"id": "{inject}"}}, "discount": "{inject}"}}'

    def _discounts_type_confuse(self, field: Field) -> str:
        price_json = self._get_price_id_json()

        match field:
            case Field.PRICE: return '{"price": "not an object", "discount": 10.0}'
            case Field.ALL:   return '{"price": [1, 2, 3], "discount": {"value": 10}}'
            case _:
                variant = self.rng.randint(0, 2)
                match variant:
                    case 0: return f'{{"price": {price_json}, "discount": "ten percent"}}'
                    case 1: return '{"price": 12345, "discount": 10.0}'
                    case 2: return f'{{"price": {price_json}, "discount": [10, 20, 30]}}'
                    case _: return self._discounts_valid(field)

    # ========================== POINTS Endpoint ==========================

    def _generate_points_payload(self, field: Field, strategy: Strategy, intensity: Intensity) -> str:
        num_magnitude = self._get_num_magnitude(intensity)

        match strategy:
            case Strategy.VALID:        return self._points_valid(field)
            case Strategy.NULL_INJECT:  return self._points_null_inject(field)
            case Strategy.NEGATIVE:     return self._points_negative(field, num_magnitude)
            case Strategy.BOUNDARY:     return self._points_boundary(field, intensity)
            case Strategy.STRUCTURE:    return self._points_structure(field)
            case Strategy.INJECTION:    return self._points_injection(field)
            case Strategy.TYPE_CONFUSE: return self._points_type_confuse(field)
            case Strategy.ENCODING:     return self._points_valid(field)
            case Strategy.NONE:         return self._points_valid(field)

    def _points_valid(self, field: Field) -> str:
        points = self.rng.randint(1, 1000)
        discount_json = self._get_discount_id_json()
        return f'{{"discount": {discount_json}, "points": {points}}}'

    def _points_null_inject(self, field: Field) -> str:
        points = 100 + self.rng.randint(0, 199)
        discount_json = self._get_discount_id_json()

        match field:
            case Field.DISCOUNT | Field.DISCOUNT_ID:
                return f'{{"discount": null, "points": {points}}}'
            case Field.POINTS:
                return f'{{"discount": {discount_json}, "points": null}}'
            case Field.ALL:
                return '{"discount": null, "points": null}'
            case _:
                variant = self.rng.randint(0, 1)
                if variant == 0:
                    return f'{{"discount": null, "points": {points}}}'
                else:
                    return f'{{"discount": {discount_json}, "points": null}}'

    def _points_negative(self, field: Field, magnitude: int) -> str:
        discount_json = self._get_discount_id_json()
        neg_points = -(self.rng.randint(1, magnitude))

        match field:
            case Field.DISCOUNT | Field.DISCOUNT_ID:
                return '{"discount": {"id": -1}, "points": 100}'
            case Field.ALL:
                return f'{{"discount": {{"id": -1}}, "points": {neg_points}}}'
            case _:
                return f'{{"discount": {discount_json}, "points": {neg_points}}}'

    def _points_boundary(self, field: Field, intensity: Intensity) -> str:
        discount_json = self._get_discount_id_json()

        match field:
            case Field.DISCOUNT | Field.DISCOUNT_ID:
                match intensity:
                    case Intensity.MILD:       return '{"discount": {"id": 0}, "points": 100}'
                    case Intensity.MODERATE:   return f'{{"discount": {{"id": {INT_MAX}}}, "points": 100}}'
                    case Intensity.AGGRESSIVE: return f'{{"discount": {{"id": {LONG_MAX}}}, "points": 100}}'
            case _:
                match intensity:
                    case Intensity.MILD:       return f'{{"discount": {discount_json}, "points": 0}}'
                    case Intensity.MODERATE:   return f'{{"discount": {discount_json}, "points": {INT_MAX}}}'
                    case Intensity.AGGRESSIVE: return f'{{"discount": {discount_json}, "points": {LONG_MAX}}}'

    def _points_structure(self, field: Field) -> str:
        discount_json = self._get_discount_id_json()
        points = 100 + self.rng.randint(0, 199)

        match field:
            case Field.DISCOUNT | Field.DISCOUNT_ID:
                return f'{{"points": {points}}}'
            case Field.POINTS:
                return f'{{"discount": {discount_json}}}'
            case Field.UNKNOWN:
                return f'{{"discount": {discount_json}, "points": {points}, "bonus": true, "tier": "gold"}}'
            case Field.ALL:
                return '{}'
            case _:
                variant = self.rng.randint(0, 2)
                match variant:
                    case 0: return '{}'
                    case 1: return f'{{"points": {points}}}'
                    case 2: return f'{{"discount": {discount_json}}}'
                    case _: return self._points_valid(field)

    def _points_injection(self, field: Field) -> str:
        discount_json = self._get_discount_id_json()
        injections = [
            "'; DROP TABLE points; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
        ]
        inject = self.rng.choice(injections)

        match field:
            case Field.DISCOUNT | Field.DISCOUNT_ID:
                return f'{{"discount": {{"id": "{inject}"}}, "points": 100}}'
            case _:
                return f'{{"discount": {{"id": "{inject}"}}, "points": "{inject}"}}'

    def _points_type_confuse(self, field: Field) -> str:
        discount_json = self._get_discount_id_json()

        match field:
            case Field.DISCOUNT | Field.DISCOUNT_ID:
                return '{"discount": "not an object", "points": 100}'
            case Field.POINTS:
                return f'{{"discount": {discount_json}, "points": "one hundred"}}'
            case Field.ALL:
                return '{"discount": [1, 2, 3], "points": {"value": 100}}'
            case _:
                variant = self.rng.randint(0, 2)
                match variant:
                    case 0: return f'{{"discount": {discount_json}, "points": "hundred"}}'
                    case 1: return '{"discount": 12345, "points": 100}'
                    case 2: return f'{{"discount": {discount_json}, "points": [100, 200, 300]}}'
                    case _: return self._points_valid(field)

    # ========================== String Helpers ==========================

    def _random_string(self, min_len: int, max_len: int) -> str:
        if max_len < min_len:
            max_len = min_len
        length = self.rng.randint(min_len, max_len)
        return ''.join(self.rng.choice(ALPHA) for _ in range(length))

    def _random_special_string(self, min_len: int, max_len: int) -> str:
        if max_len < min_len:
            max_len = min_len
        length = self.rng.randint(min_len, max_len)
        pool = ALPHA + SPECIAL
        raw = ''.join(self.rng.choice(pool) for _ in range(length))
        return self._escape_json(raw)

    def _random_unicode_string(self, min_len: int, max_len: int) -> str:
        if max_len < min_len:
            max_len = min_len
        length = self.rng.randint(min_len, max_len)
        pool = ALPHA + UNICODE
        return ''.join(self.rng.choice(pool) for _ in range(length))

    @staticmethod
    def _escape_json(s: str) -> str:
        return (s.replace("\\", "\\\\")
                 .replace('"', '\\"')
                 .replace("\n", "\\n")
                 .replace("\r", "\\r")
                 .replace("\t", "\\t"))