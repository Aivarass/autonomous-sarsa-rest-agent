from enum import Enum

from sarsa.generator.PayloadGenerator import Endpoint, Field, Strategy, Intensity
from sarsa.strategy.HttpType import HttpType


class Action(Enum):
    # HTTP Type (6)
    EXPLORE_GET = 0
    EXPLORE_GET_ALL = 1
    EXPLORE_POST = 2
    EXPLORE_PUT = 3
    EXPLORE_PATCH = 4
    EXPLORE_DELETE = 5
    # Endpoint (4)
    INSPECT_ITEMS = 6
    INSPECT_PRICES = 7
    INSPECT_DISCOUNTS = 8
    INSPECT_POINTS = 9
    # Field Targeting (11)
    FOCUS_NAME = 10
    FOCUS_QUANTITY = 11
    FOCUS_DESCRIPTION = 12
    FOCUS_PRICE = 13
    FOCUS_ITEM_ID = 14
    FOCUS_DISCOUNT_ID = 15
    FOCUS_DISCOUNT = 16
    FOCUS_POINTS_ID = 17
    FOCUS_POINTS = 18
    FOCUS_ALL = 19
    FOCUS_UNKNOWN = 20
    # Mutation Strategy (8)
    STRATEGY_VALID = 21
    STRATEGY_NULL_INJECT = 22
    STRATEGY_NEGATIVE = 23
    STRATEGY_BOUNDARY = 24
    STRATEGY_STRUCTURE = 25
    STRATEGY_INJECTION = 26
    STRATEGY_TYPE_CONFUSE = 27
    STRATEGY_ENCODING = 28
    # Intensity (2)
    INTENSIFY = 29
    CONSERVE = 30
    # Execute (1)
    EXECUTE = 31

    @staticmethod
    def count():
        return len(Action)

    def apply_to(self, strategy, state):
        match self:
            # HTTP Type
            case Action.EXPLORE_GET:
                state.is_ready_to_execute = 1
                state.http_type = HttpType.GET.value
                strategy.http_type = HttpType.GET
            case Action.EXPLORE_GET_ALL:
                state.is_ready_to_execute = 1
                state.http_type = HttpType.GET_ALL.value
                strategy.http_type = HttpType.GET_ALL
            case Action.EXPLORE_POST:
                state.is_ready_to_execute = 1
                state.http_type = HttpType.POST.value
                strategy.http_type = HttpType.POST
            case Action.EXPLORE_PUT:
                state.is_ready_to_execute = 1
                state.http_type = HttpType.PUT.value
                strategy.http_type = HttpType.PUT
            case Action.EXPLORE_PATCH:
                state.is_ready_to_execute = 1
                state.http_type = HttpType.PATCH.value
                strategy.http_type = HttpType.PATCH
            case Action.EXPLORE_DELETE:
                state.is_ready_to_execute = 1
                state.http_type = HttpType.DELETE.value
                strategy.http_type = HttpType.DELETE
            # Endpoints
            case Action.INSPECT_ITEMS:
                state.endpoint = Endpoint.ITEMS.value
                strategy.endpoint = Endpoint.ITEMS
            case Action.INSPECT_PRICES:
                state.endpoint = Endpoint.PRICES.value
                strategy.endpoint = Endpoint.PRICES
            case Action.INSPECT_DISCOUNTS:
                state.endpoint = Endpoint.DISCOUNTS.value
                strategy.endpoint = Endpoint.DISCOUNTS
            case Action.INSPECT_POINTS:
                state.endpoint = Endpoint.POINTS.value
                strategy.endpoint = Endpoint.POINTS
            # Fields
            case Action.FOCUS_NAME:
                state.current_field = Field.NAME.value
                strategy.field = Field.NAME
            case Action.FOCUS_QUANTITY:
                state.current_field = Field.QUANTITY.value
                strategy.field = Field.QUANTITY
            case Action.FOCUS_DESCRIPTION:
                state.current_field = Field.DESCRIPTION.value
                strategy.field = Field.DESCRIPTION
            case Action.FOCUS_PRICE:
                state.current_field = Field.PRICE.value
                strategy.field = Field.PRICE
            case Action.FOCUS_ITEM_ID:
                state.current_field = Field.ITEM_ID.value
                strategy.field = Field.ITEM_ID
            case Action.FOCUS_DISCOUNT_ID:
                state.current_field = Field.DISCOUNT_ID.value
                strategy.field = Field.DISCOUNT_ID
            case Action.FOCUS_DISCOUNT:
                state.current_field = Field.DISCOUNT.value
                strategy.field = Field.DISCOUNT
            case Action.FOCUS_POINTS_ID:
                state.current_field = Field.POINTS_ID.value
                strategy.field = Field.POINTS_ID
            case Action.FOCUS_POINTS:
                state.current_field = Field.POINTS.value
                strategy.field = Field.POINTS
            case Action.FOCUS_ALL:
                state.current_field = Field.ALL.value
                strategy.field = Field.ALL
            case Action.FOCUS_UNKNOWN:
                state.current_field = Field.UNKNOWN.value
                strategy.field = Field.UNKNOWN
            # Strategies
            case Action.STRATEGY_VALID:
                state.current_strategy = Strategy.VALID.value
                strategy.strategy = Strategy.VALID
            case Action.STRATEGY_NULL_INJECT:
                state.current_strategy = Strategy.NULL_INJECT.value
                strategy.strategy = Strategy.NULL_INJECT
            case Action.STRATEGY_NEGATIVE:
                state.current_strategy = Strategy.NEGATIVE.value
                strategy.strategy = Strategy.NEGATIVE
            case Action.STRATEGY_BOUNDARY:
                state.current_strategy = Strategy.BOUNDARY.value
                strategy.strategy = Strategy.BOUNDARY
            case Action.STRATEGY_STRUCTURE:
                state.current_strategy = Strategy.STRUCTURE.value
                strategy.strategy = Strategy.STRUCTURE
            case Action.STRATEGY_INJECTION:
                state.current_strategy = Strategy.INJECTION.value
                strategy.strategy = Strategy.INJECTION
            case Action.STRATEGY_TYPE_CONFUSE:
                state.current_strategy = Strategy.TYPE_CONFUSE.value
                strategy.strategy = Strategy.TYPE_CONFUSE
            case Action.STRATEGY_ENCODING:
                state.current_strategy = Strategy.ENCODING.value
                strategy.strategy = Strategy.ENCODING
            # Intensity
            case Action.INTENSIFY:
                state.current_intensity = Intensity.AGGRESSIVE.value
                strategy.intensity = Intensity.AGGRESSIVE
            case Action.CONSERVE:
                state.current_intensity = Intensity.MILD.value
                strategy.intensity = Intensity.MILD
            # Execute
            case Action.EXECUTE:
                pass

        return state

    def requires_id(self):
        return self in (
            Action.EXPLORE_GET,
            Action.EXPLORE_PUT,
            Action.EXPLORE_PATCH,
            Action.EXPLORE_DELETE,
        )
