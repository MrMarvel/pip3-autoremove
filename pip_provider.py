from typing import Protocol
import importlib.metadata


def get_distribution(name: str):
    dist = importlib.metadata.distribution(name)
    dist.
    return dist


def list_installed_distributions() -> list:
    return list(importlib.metadata.distributions())
