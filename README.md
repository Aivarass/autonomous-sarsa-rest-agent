# Autonomous SARSA REST Agent

Python implementation of an autonomous reinforcement learning agent that discovers stateful API bugs through exploration. No scripted rules, no domain knowledge, no external ML libraries for the core RL logic.

For detailed technical writeup covering the RL approach, state representation, hyperparameter choices, and learning progression, see the [Java implementation](https://github.com/Aivarass/sarsa-rest-bug-hunter).

## What it does

REST APIs often contain bugs that only surface after a specific sequence of dependent calls. A price can't exist without an item. A discount depends on a valid price. Certain delete operations fail only after a precise chain of creates.

This agent learns those dependencies on its own. It starts with no knowledge of the API, explores through trial and error, and discovers multi-step defect chains up to 5 dependent calls deep across a search space of ~3.2 quintillion possible paths.

## How it works

- **Algorithm:** SARSA (on-policy temporal difference learning)
- **Neural network:** Single hidden layer (8 neurons), manual backpropagation
- **Learning signal:** Sparse rewards only (5xx responses = bug found)
- **Exploration:** Epsilon-greedy with action masking
- **Payload generation:** Property-based testing to generate valid and invalid request bodies

The agent builds and sends API requests, observes the response, updates its policy, and gradually learns which sequences of calls lead to defects. No reward shaping, no domain knowledge baked in.

## About implementation

This is a port from the [original Java implementation](https://github.com/Aivarass/sarsa-rest-bug-hunter) to demonstrate the same approach in Python. Both versions produce equivalent results. The neural network, SARSA loop, state representation, and property-based test generation are all implemented from scratch.

## Project structure

```
ann/            # Neural network (forward pass, backpropagation, weight management)
sarsa/          # SARSA agent, state representation, action selection, reward logic
requirements.txt
```

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Start the target API (Java, separate terminal)
mvn spring-boot:run

# Run the agent
python -m sarsa.sarsa_runner
```

## Key results

| Metric | Value |
|--------|-------|
| Chain depth | 5 dependent API calls |
| Search space | ~3.2 quintillion paths |
| Hidden neurons | 8 |
| Time to discovery | ~30 minutes |
| Unique bug combos | 115+ |

## Tech stack

Python, NumPy, property-based testing, REST APIs

## Related projects

- [sarsa-rest-bug-hunter](https://github.com/Aivarass/sarsa-rest-bug-hunter) — Original Java implementation with full technical writeup
- [simple-java-ppo](https://github.com/Aivarass/simple-java-ppo) — PPO built from scratch in Java
- [a2c-from-scratch](https://github.com/Aivarass/a2c-from-scratch) — Actor-Critic in pure Java
