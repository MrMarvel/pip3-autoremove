import logging
import subprocess
import sys
from typing import Sequence, Callable

from extra import importlib_utils

logger = logging.getLogger(__name__)


def install_dist(req):
    pip_cmd = [sys.executable, '-m', 'pip']
    call = subprocess.check_call(pip_cmd + ["install", req])
    if call != 0:
        raise Exception("Failed to install %s" % req)


def need_dists(dists: Sequence[str], remove_after: bool = False):
    def _decorator(func):
        def wrapper(*args, **kwargs):
            util = importlib_utils.ImportUtilsFactory.create()
            for dist in dists:
                logger.info("Checking if distribution \"%s\" is installed.",
                            dist)
                try:
                    util.get_distribution(dist)
                except util.InstalledDependencyNotFound:
                    logger.info(
                        "Distribution \"%s\" is not installed. Installing it.",
                        dist)
                    install_dist(dist)
                util.clear_known_distributions()
                try:
                    util.get_distribution(dist)
                except util.InstalledDependencyNotFound:
                    raise Exception(
                        "Distribution \"%s\" failed to install." % dist)
                logger.info(
                    "Distribution \"%s\" is installed. OK.",
                    dist)
            res = func(*args, **kwargs)
            if not remove_after:
                return res
            for dist in dists:
                logger.info(
                    "Removing distribution \"%s\" as requested.", dist)
            call_result = subprocess.check_call(
                [sys.executable, '-m', 'pip', 'uninstall', '-y'] + list(dists))
            if call_result != 0:
                raise Exception(
                    "Failed to remove requested distributions: %s" % dists)
            logger.info("All requested distributions removed.")
            return res

        return wrapper

    if isinstance(dists, Callable):
        # logger.info("No arguments. Just decorator on \"%s\".", dists.__name__)
        return _decorator(dists)
    # logger.info("Arguments: %s", dists)
    return _decorator
