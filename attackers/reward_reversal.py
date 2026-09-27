"""Reward-reversal input for the poisoning experiment."""


def reverse_reward(reward: float) -> float:
    return -reward
