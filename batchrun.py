"""Run two small local-update cases without the full training schedule."""

from attackers.reward_reversal import reverse_reward
from fl.algorithms.fedql import TabularQAgent
from fl.local_training import local_q_updates


def main() -> None:
    state, action = 0, 0
    for label, reward in (("regular", 1.0), ("reward reversal", reverse_reward(1.0))):
        agent = TabularQAgent(action_count=9, seed=42)
        table = local_q_updates(agent, [(state, action, reward, state)])
        print(f"{label}: Q[{state}, {action}] = {table[(state, action)]:+.2f}")


if __name__ == "__main__":
    main()
