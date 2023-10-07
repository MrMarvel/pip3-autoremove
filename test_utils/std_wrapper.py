import sys
from io import StringIO
from unittest import TestCase


class STDWrapper:
    def __init__(self, stdin=None, stdout=None):
        self.stdin = self._io_format(stdin)
        self.stdout = self._io_format(stdout)
        self.base_stdin = None
        self.base_stdout = None

    def __enter__(self):
        self.base_stdin = sys.stdin
        self.base_stdout = sys.stdout
        if self.stdin:
            sys.stdin = self.stdin
        if self.stdout:
            sys.stdout = self.stdout
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdin = self.base_stdin
        sys.stdout = self.base_stdout
        self.base_stdin = None
        self.base_stdout = None

    @staticmethod
    def _io_format(io_like):
        if type(io_like) == str:
            return StringIO(io_like)
        return io_like
