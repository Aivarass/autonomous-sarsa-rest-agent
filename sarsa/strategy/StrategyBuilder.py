from sarsa.strategy.Action import Action
from sarsa.strategy.StrategyState import StrategyState


class StrategyBuilder:

    def __init__(self):
        self.actions = list(Action)
        self.strategy = StrategyState()

    def apply_action(self, action_index, state):
        if action_index < 0 or action_index >= len(self.actions):
            raise ValueError(f"Invalid action index: {action_index}")
        action = self.actions[action_index]
        return action.apply_to(self.strategy, state)

    def is_execute(self, action_index):
        return action_index == Action.EXECUTE.value

    def get_state(self):
        return self.strategy

    def get_http_type(self):
        return self.strategy.http_type

    def get_endpoint(self):
        return self.strategy.endpoint

    def get_field(self):
        return self.strategy.get_effective_field()

    def get_strategy(self):
        return self.strategy.get_effective_strategy()

    def get_intensity(self):
        return self.strategy.intensity

    def is_ready(self):
        return self.strategy.is_ready_to_execute()

    def reset(self):
        self.strategy.reset()

    @staticmethod
    def get_action_count():
        return Action.count()

    @staticmethod
    def get_execute_index():
        return Action.EXECUTE.value

    def action_requires_id(self, action_index):
        if action_index < 0 or action_index >= len(self.actions):
            return False
        return self.actions[action_index].requires_id()
