
from sarsa.generator.PayloadGenerator import Endpoint, Field, Strategy, Intensity
from sarsa.strategy.HttpType import HttpType


class StrategyState:

    def __init__(self):
        self.http_type = HttpType.NONE
        self.endpoint = Endpoint.ITEMS
        self.field = Field.ALL
        self.strategy = Strategy.VALID
        self.intensity = Intensity.MILD

    def is_ready_to_execute(self):
        return self.http_type != HttpType.NONE

    def get_effective_field(self):
        return Field.ALL if self.field == Field.NONE else self.field

    def get_effective_strategy(self):
        return Strategy.VALID if self.strategy == Strategy.NONE else self.strategy

    def reset(self):
        self.http_type = HttpType.NONE
        self.endpoint = Endpoint.ITEMS
        self.field = Field.ALL
        self.strategy = Strategy.VALID
        self.intensity = Intensity.MILD
