from tokenize import endpats

import numpy as np


class State:

    FEATURE_COUNT = 14

    def __init__(self, has_valid_item_id, has_valid_price_id, has_valid_discount_id, has_valid_points_id, has_any_item, last_status_call, last_method, http_type, endpoint, current_field, current_strategy, current_intensity, steps_since_execute, is_ready_to_execute):

        self.has_valid_item_id = has_valid_item_id
        self.has_valid_price_id = has_valid_price_id
        self.has_valid_discount_id = has_valid_discount_id
        self.has_valid_points_id = has_valid_points_id
        self.has_any_item = has_any_item
        self.last_status_call = last_status_call
        self.last_method = last_method

        self.http_type = http_type
        self.endpoint = endpoint
        self.current_field = current_field
        self.current_strategy = current_strategy
        self.current_intensity = current_intensity
        self.steps_since_execute = steps_since_execute

        self.is_ready_to_execute = is_ready_to_execute

    def scale(self):
        features = np.zeros(self.FEATURE_COUNT)
        features[0] = self.has_valid_item_id
        features[1] = self.has_valid_price_id
        features[2] = self.has_valid_discount_id
        features[3] = self.has_valid_points_id
        features[4] = self.has_any_item
        features[5] = self.normalize_status_code(self.last_status_call)
        features[6] = int(self.last_method) / 4.0
        features[7] = int(self.http_type) / 6.0
        features[8] = int(self.endpoint) / 3.0
        features[9] = int(self.current_field) / 11.0
        features[10] = int(self.current_strategy) / 8.0
        features[11] = int(self.current_intensity) / 2.0
        features[12] = min(self.steps_since_execute, 10) / 10.0
        features[13] = self.is_ready_to_execute
        return features


    def normalize_status_code(self, code):
        if code == 0: return 0.0

        match(code // 100):
            case 2:
                return  0.25
            case 3:
                return 0.5
            case 4:
                return 0.75
            case 5:
                return 1.0
            case _:
                return 0.0

    def reset_after_execute(self):
        self.http_type = 0
        self.endpoint = 0
        self.current_field = 0
        self.current_strategy = 0
        self.current_intensity = 0
        self.steps_since_execute = 0
        self.is_ready_to_execute = 0