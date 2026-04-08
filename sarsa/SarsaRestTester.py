import json
import random
import time
from datetime import datetime

import numpy as np
import requests

from ann.QNetwork import QNetwork5
from sarsa.generator.PayloadGenerator import PayloadGenerator, Endpoint, Intensity, Strategy, Field
from sarsa.model.State import State
from sarsa.strategy.HttpType import HttpType
from sarsa.strategy.StrategyBuilder import StrategyBuilder


class SarsaRestTester:

    def __init__(self):
        self.discovery_counter = 0
        # Main
        self.EPISODES = 1000000
        self.LOG_EVERY = 10000
        self.SEED = 1234
        self.STEP_LIMIT = 35

        # Hyper params
        self.EPSILON = 0.01
        self.GAMMA = 1.0
        self.ALPHA = 0.01

        # ANN
        self.ANN_INPUTS = State.FEATURE_COUNT
        self.ANN_ACTIONS = StrategyBuilder.get_action_count()
        self.ANN_NEURONS = 16

        # URL
        self.BASE_URL = "http://localhost:8080/api/"

        # Helpers
        self.pbt = PayloadGenerator()
        self.last_item_id = None
        self.last_price_id = None
        self.last_discount_id = None
        self.last_points_id = None

        # Tracking
        self.all_action_counts: dict[int, int] = {}
        self.http_type_counts: dict[HttpType, int] = {}
        self.endpoint_counts: dict[Endpoint, int] = {}
        self.strategy_counts: dict[Strategy, int] = {}
        self.field_counts: dict[Field, int] = {}
        self.intensity_counts: dict[Intensity, int] = {}

        self.bugs_by_combo: dict[str, int] = {}
        self.unique_bug_combos: set[str] = set()

        self.execute_count = 0
        self.dial_turner_count = 0

        self.chart_data = []
        self.hidden_bug_discovered = False
        self.hidden_bug_first_episode = -1
        self.hidden_bug_count = 0
        self.hidden_bug_hits_this_window = 0

        self.ann = QNetwork5(self.ANN_INPUTS, self.ANN_NEURONS, self.ANN_ACTIONS)

        self.execute_sarsa(self.EPISODES)

        self.export_chart_data()




    def execute_sarsa(self, episodes):
        rng = random.Random(self.SEED)
        total_reward = 0
        total_bugs = 0
        start_time = time.time()

        for i in range(1, episodes + 1):
            result = self.execute_episode(rng, i)
            total_reward += result[0]
            total_bugs += result[1]

            if i % 1000 == 0:
                self.chart_data.append([i, self.hidden_bug_hits_this_window])

            if i % self.LOG_EVERY == 0:
                avg_reward = total_reward / self.LOG_EVERY
                elapsed = time.time() - start_time
                execute_ratio = (self.execute_count / (
                            self.execute_count + self.dial_turner_count) * 100) if self.execute_count > 0 else 0

                print(f"\n{'=' * 60}")
                print(
                    f"Episode {i:,} | Avg Reward: {avg_reward:.3f} | Unique Bug Combos: {len(self.unique_bug_combos)} | Time: {elapsed:.1f}s")
                print(
                    f"Execute ratio: {execute_ratio:.1f}% ({self.execute_count} executes, {self.dial_turner_count} dial-turners)")

                print("\n--- HttpType Distribution ---")
                for k, v in self.http_type_counts.items():
                    print(f"  {str(k):<10}: {v}")

                print("\n--- Resource Distribution ---")
                for k, v in self.endpoint_counts.items():
                    print(f"  {str(k):<10}: {v}")

                print("\n--- Strategy Distribution ---")
                for k, v in self.strategy_counts.items():
                    print(f"  {str(k):<15}: {v}")

                print("\n--- Field Distribution ---")
                for k, v in self.field_counts.items():
                    print(f"  {str(k):<12}: {v}")

                print("\n--- Intensity Distribution ---")
                for k, v in self.intensity_counts.items():
                    print(f"  {str(k):<12}: {v}")

                if self.bugs_by_combo:
                    print("\n--- Top Bug-Triggering Combos ---")
                    sorted_bugs = sorted(self.bugs_by_combo.items(), key=lambda x: x[1], reverse=True)[:5]
                    for k, v in sorted_bugs:
                        print(f"  {k}: {v} times")

                print("\n--- Raw Action Distribution ---")
                print("  ", end="")
                for k, v in sorted(self.all_action_counts.items()):
                    print(f"[{k}]:{v} ", end="")
                print()

                # Reset for next window
                total_reward = 0
                total_bugs = 0
                start_time = time.time()
                self.all_action_counts.clear()
                self.http_type_counts.clear()
                self.endpoint_counts.clear()
                self.strategy_counts.clear()
                self.field_counts.clear()
                self.intensity_counts.clear()
                self.bugs_by_combo.clear()
                self.execute_count = 0
                self.dial_turner_count = 0
                self.hidden_bug_hits_this_window = 0

    def execute_episode(self, rng, episode_num):
        api_history = []
        strategy = StrategyBuilder()
        self.last_item_id = None
        self.last_price_id = None
        self.last_discount_id = None
        self.last_points_id = None
        current_state = self.init_state()
        mask = self.get_valid_mask(current_state, strategy)
        current_action = self.ann.epsilon_greedy_masked(current_state.scale(), self.EPSILON, mask, rng)

        episode_reward = 0
        bugs_found = 0

        response = None

        strategy.reset()

        for step in range(self.STEP_LIMIT):
            response = None
            self.all_action_counts[current_action] = self.all_action_counts.get(current_action, 0) + 1

            executed_combo = None
            if strategy.is_execute(current_action):
                self.track_strategy_execution(strategy)
                executed_combo = f"{strategy.get_http_type()}+{strategy.get_endpoint()}+{strategy.get_strategy()}+{strategy.get_field()}"

                self.pbt.last_item_id = int(self.last_item_id) if self.last_item_id is not None else None
                self.pbt.last_price_id = int(self.last_price_id) if self.last_price_id is not None else None
                self.pbt.last_discount_id = int(self.last_discount_id) if self.last_discount_id is not None else None

                response = self.execute_with_strategy(strategy)
                if response is not None:
                    api_history.append({
                        "method": str(strategy.get_http_type()).split(".")[-1],
                        "endpoint": "/" + str(strategy.get_endpoint()).split(".")[-1].lower(),
                        "status": response.status_code
                    })
                self.execute_count += 1
            else:
                current_state = strategy.apply_action(current_action, current_state)
                current_state.steps_since_execute = min(current_state.steps_since_execute + 1, 10)
                self.dial_turner_count += 1

            # NEXT
            next_state = self.update_state_from_response(current_state, strategy, response)
            next_mask = self.get_valid_mask(next_state, strategy)
            next_action = self.ann.epsilon_greedy_masked(next_state.scale(), self.EPSILON, next_mask, rng)

            if response is not None:
                strategy.reset()
                next_state.reset_after_execute()

            reward, discovery = self.calculate_reward(response, executed_combo, episode_num, api_history, current_state)

            episode_reward += reward

            if discovery is not None:
                print(json.dumps(discovery))

            if reward > 0:
                bugs_found += 1

            terminal = bool(step == self.STEP_LIMIT - 1)

            self.ann.sarsa_update(current_state.scale(), current_action, reward, next_state.scale(), next_action, terminal, self.GAMMA, self.ALPHA)

            current_state = next_state
            current_action = next_action

        return [episode_reward, bugs_found]


    def execute_with_strategy(self, strategy_builder):
        http_type = strategy_builder.get_http_type()
        endpoint = strategy_builder.get_endpoint()
        payload = self.pbt.generate(endpoint, strategy_builder.get_field(), strategy_builder.get_strategy(), strategy_builder.get_intensity())

        last_id = None
        if endpoint == Endpoint.ITEMS:
            last_id = self.last_item_id
        elif endpoint == Endpoint.PRICES:
            last_id = self.last_price_id
        elif endpoint == Endpoint.DISCOUNTS:
            last_id = self.last_discount_id
        else:
            last_id = self.last_points_id

        endpoint_path = endpoint.name.lower()

        match http_type:
            case HttpType.POST:
                return self.post_item(payload, endpoint)
            case HttpType.PUT:
                return self.put_item(payload, endpoint)
            case HttpType.PATCH:
                return self.patch_item(payload, endpoint)
            case HttpType.DELETE:
                return requests.delete(f"{self.BASE_URL}{endpoint_path}/{last_id}")
            case HttpType.GET:
                return requests.get(f"{self.BASE_URL}{endpoint_path}/{last_id}")
            case HttpType.GET_ALL:
                return requests.get(f"{self.BASE_URL}{endpoint_path}")
            case _:
                return None

    def get_method_for_endpoint(self, http_type):
        match http_type:
            case HttpType.GET | HttpType.GET_ALL | HttpType.NONE:
                return 0
            case HttpType.POST:
                return 1
            case HttpType.PUT:
                return 2
            case HttpType.DELETE:
                return 3
            case HttpType.PATCH:
                return 4

    def post_item(self, payload, endpoint):
        response = requests.post(
            self.BASE_URL + endpoint.name.lower(),
            headers={"Content-Type": "application/json"},
            data=payload
        )
        if response.status_code == 201:
            item_id = response.json().get("id")
            if endpoint == Endpoint.ITEMS:
                self.last_item_id = item_id
            elif endpoint == Endpoint.PRICES:
                self.last_price_id = item_id
            elif endpoint == Endpoint.DISCOUNTS:
                self.last_discount_id = item_id
            else:
                self.last_points_id = item_id
        return response

    def put_item(self, payload, endpoint):
        target_id = str(self.get_endpoint_target(endpoint))

        response = requests.put(
            self.BASE_URL + endpoint.name.lower() + "/" + target_id,
            headers={"Content-Type": "application/json"},
            data=payload
        )
        return response

    def patch_item(self, payload, endpoint):
        target_id = str(self.get_endpoint_target(endpoint))

        response = requests.patch(
            self.BASE_URL + endpoint.name.lower() + "/" + target_id,
            headers={"Content-Type": "application/json"},
            data=payload
        )
        return response

    def extract_id_from_get_all(self, response, endpoint):
        if response.status_code != 200:
            return
        try:
            first_id = response.json()[0].get("id")
            if first_id is not None:
                if endpoint == Endpoint.ITEMS:
                    self.last_item_id = first_id
                elif endpoint == Endpoint.PRICES:
                    self.last_price_id = first_id
                elif endpoint == Endpoint.DISCOUNTS:
                    self.last_discount_id = first_id
                else:
                    self.last_points_id = first_id
        except (IndexError, KeyError, ValueError):
            pass

    def calculate_reward(self, response, executed_combo, episode_num, api_history, current_state):
        if response is None:
            return -0.15, None
        if response.status_code != 500:
            return 0, None

        reward = 10
        if executed_combo is not None:
            self.bugs_by_combo[executed_combo] = self.bugs_by_combo.get(executed_combo, 0) + 1
            self.unique_bug_combos.add(executed_combo)
            if executed_combo.startswith("DELETE+POINTS+"):
                self.hidden_bug_count += 1
                self.hidden_bug_hits_this_window += 1
                self.log_hidden_bug_discovery(executed_combo, episode_num)

        discovery = self.build_discovery(
            api_history, episode_num, reward, response.status_code,
            {
                "hasValidItemId": current_state.has_valid_item_id,
                "hasValidPriceId": current_state.has_valid_price_id,
                "hasValidDiscountId": current_state.has_valid_discount_id,
                "hasValidPointsId": current_state.has_valid_points_id
            }
        )
        return reward, None

    def build_discovery(self, api_history, episode_num, reward, status_code, state_features):
        self.discovery_counter += 1
        return {
            "discovery_id": str(self.discovery_counter).zfill(3),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "episode": episode_num,
            "api_sequence": api_history,
            "final_status": status_code,
            "reward": reward,
            "state_features": state_features
        }

    def get_endpoint_target(self, endpoint):
        if endpoint == Endpoint.ITEMS:
            return self.last_item_id
        elif endpoint == Endpoint.PRICES:
            return self.last_price_id
        elif endpoint == Endpoint.DISCOUNTS:
            return self.last_discount_id
        else:
            return self.last_points_id

    def log_hidden_bug_discovery(self, combo, episode_num):
        if not self.hidden_bug_discovered:
            self.hidden_bug_discovered = True
            self.hidden_bug_first_episode = episode_num
            print()
            print("╔════════════════════════════════════════════════════════════════╗")
            print("║              HIDDEN BUG DISCOVERED!                          ║")
            print("╠════════════════════════════════════════════════════════════════╣")
            print(f"║  Episode:    {episode_num:,}")
            print(f"║  Combo:      {combo}")
            print("║  Condition:  DELETE POINTS → 500 (ancestor price < 0)          ║")
            print("║  Chain:      ITEM → PRICE(neg) → DISCOUNT → POINTS → DELETE   ║")
            print("╚════════════════════════════════════════════════════════════════╝")
            print()
        else:
            print(f"🐛 HIDDEN BUG HIT #{self.hidden_bug_count} @ Episode {episode_num:,} | {combo} | HTTP 500")

    def init_state(self):
        return State(0,0, 0,0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0)

    def update_state_from_response(self, state, strategy, response):
        if response is None:
            return state

        state.last_status_call = response.status_code
        http_type = strategy.get_http_type()
        state.last_method = self.get_method_for_endpoint(http_type)
        state.endpoint = strategy.get_endpoint().value

        # POST success
        if http_type == HttpType.POST and response.status_code == 201:
            if strategy.get_endpoint() == Endpoint.ITEMS:
                state.has_valid_item_id = 1
            elif strategy.get_endpoint() == Endpoint.PRICES:
                state.has_valid_price_id = 1
            elif strategy.get_endpoint() == Endpoint.DISCOUNTS:
                state.has_valid_discount_id = 1
            elif strategy.get_endpoint() == Endpoint.POINTS:
                state.has_valid_points_id = 1

        # DELETE success
        if http_type == HttpType.DELETE and response.status_code in (200, 204):
            if strategy.get_endpoint() == Endpoint.ITEMS:
                state.has_valid_item_id = 0
                self.last_item_id = None
            elif strategy.get_endpoint() == Endpoint.PRICES:
                state.has_valid_price_id = 0
                self.last_price_id = None
            elif strategy.get_endpoint() == Endpoint.DISCOUNTS:
                state.has_valid_discount_id = 0
                self.last_discount_id = None
            elif strategy.get_endpoint() == Endpoint.POINTS:
                state.has_valid_points_id = 0
                self.last_points_id = None

        # GET_ALL
        if http_type == HttpType.GET_ALL and response.status_code == 200:
            if strategy.get_endpoint() == Endpoint.ITEMS:
                self.extract_id_from_get_all(response, Endpoint.ITEMS)
                if self.last_item_id is not None:
                    state.has_valid_item_id = 1
                    state.has_any_item = 1
                else:
                    state.has_any_item = 0
            elif strategy.get_endpoint() == Endpoint.PRICES:
                self.extract_id_from_get_all(response, Endpoint.PRICES)
                if self.last_price_id is not None:
                    state.has_valid_price_id = 1
            elif strategy.get_endpoint() == Endpoint.DISCOUNTS:
                self.extract_id_from_get_all(response, Endpoint.DISCOUNTS)
                if self.last_discount_id is not None:
                    state.has_valid_discount_id = 1
            elif strategy.get_endpoint() == Endpoint.POINTS:
                self.extract_id_from_get_all(response, Endpoint.POINTS)
                if self.last_points_id is not None:
                    state.has_valid_points_id = 1

        return state


    def track_strategy_execution(self, strategy):
        self.http_type_counts[strategy.get_http_type()] = self.http_type_counts.get(strategy.get_http_type(), 0) + 1
        self.endpoint_counts[strategy.get_endpoint()] = self.endpoint_counts.get(strategy.get_endpoint(), 0) + 1
        self.strategy_counts[strategy.get_strategy()] = self.strategy_counts.get(strategy.get_strategy(), 0) + 1
        self.field_counts[strategy.get_field()] = self.field_counts.get(strategy.get_field(), 0) + 1
        self.intensity_counts[strategy.get_intensity()] = self.intensity_counts.get(strategy.get_intensity(), 0) + 1

    def get_valid_mask(self, state, strategy_builder):
        mask = np.zeros(self.ANN_ACTIONS, dtype=bool)
        has_item_id = state.has_valid_item_id
        has_price_id = state.has_valid_price_id
        has_discount_id = state.has_valid_discount_id
        has_points_id = state.has_valid_points_id
        current_endpoint = strategy_builder.get_endpoint()

        for i in range(self.ANN_ACTIONS):
            if strategy_builder.action_requires_id(i):
                if current_endpoint == Endpoint.ITEMS:
                    mask[i] = has_item_id
                elif current_endpoint == Endpoint.PRICES:
                    mask[i] = has_price_id
                elif current_endpoint == Endpoint.DISCOUNTS:
                    mask[i] = has_discount_id
                else:
                    mask[i] = has_points_id
            elif i == strategy_builder.get_execute_index():
                mask[i] = strategy_builder.is_ready()
            else:
                mask[i] = True
        return mask


    def export_chart_data(self):
        try:
            with open("bug_discovery.csv", "w") as f:
                f.write("episode,hidden_bug_hits\n")
                for data in self.chart_data:
                    f.write(f"{data[0]},{data[1]}\n")
            print("\n📊 Chart data exported to: bug_discovery.csv")
        except IOError as e:
            print(f"Failed to export CSV: {e}")

        print(f"\n{'=' * 60}")
        print("FINAL SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total unique bugs discovered: {len(self.unique_bug_combos)}")
        print(f"Hidden bug (DELETE+POINTS) hits: {self.hidden_bug_count}")
        if self.hidden_bug_first_episode > 0:
            print(f"Hidden bug first discovered at episode: {self.hidden_bug_first_episode:,}")
        else:
            print("Hidden bug was NOT discovered in this run.")

if __name__ == "__main__":
    SarsaRestTester()