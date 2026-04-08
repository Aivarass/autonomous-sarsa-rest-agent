from math import sqrt
from random import uniform
from threading import active_count

import numpy as np

class QNetwork5:
    def __init__(self, input_count, neuron_count, action_count):
        self.input_count = input_count
        self.neuron_count = neuron_count
        self.action_count = action_count

        self.input_weights = np.zeros((neuron_count, input_count))
        self.input_bias = np.zeros(neuron_count)

        self.action_weights = np.zeros((action_count, neuron_count))
        self.action_bias = np.zeros(action_count)

        self.init_xavier()

    def init_xavier(self):
        limit1 = sqrt(6.0 / (self.neuron_count + self.input_count))
        self.input_weights = np.random.uniform(-limit1, limit1, (self.neuron_count, self.input_count))
        self.input_bias = np.zeros(self.neuron_count)

        limit2 = sqrt(6.0 / (self.action_count + self.neuron_count))
        self.action_weights = np.random.uniform(-limit2, limit2, (self.action_count, self.neuron_count))
        self.action_bias = np.zeros(self.action_count)

    def predict(self, state, action):
        hidden = self.input_forward_pass(state)
        return self.calc_q(action, hidden)

    def sarsa_update(self, state, action, reward, next_state, next_action, terminal, gamma, alpha):
        q_state_action = self.predict(state, action)
        q_next = 0.0 if terminal else self.predict(next_state, next_action)
        target = reward + gamma * q_next
        error = target - q_state_action

        self.apply_semi_gradient(state, action, error, alpha)

    def apply_semi_gradient(self, state, action, error, alpha):
        hidden = self.input_forward_pass(state)
        err_clip = np.clip(error, -10.0, 10.0)
        step = err_clip * alpha

        self.action_weights[action] += step * hidden
        self.action_bias[action] += step

        action_weights = self.action_weights[action]
        dtanh = 1.0 - hidden * hidden
        chain = step * action_weights * dtanh

        self.input_weights += np.outer(chain, state)
        self.input_bias += chain

    def epsilon_greedy_masked(self, state, epsilon, valid_mask, rng):
        valid_indices = np.where(valid_mask)[0]
        if len(valid_indices) == 0:
            raise ValueError("No valid actions available")

        if rng.random() < epsilon:
            idx = rng.randint(0, len(valid_indices) - 1)
            return int(valid_indices[idx])

        q_values = self.forward(state)
        q_values[~valid_mask] = float('-inf')
        return np.argmax(q_values)

    def forward(self, x):
        hidden = self.input_forward_pass(x)
        return self.action_weights @ hidden + self.action_bias

    def input_forward_pass(self, x):
        return np.tanh(self.input_weights @ x + self.input_bias)

    def calc_q(self, action, hidden):
        return self.action_weights[action] @ hidden + self.action_bias[action]