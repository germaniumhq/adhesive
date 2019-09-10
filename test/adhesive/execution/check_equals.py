from typing import Dict, Set

import unittest

test = unittest.TestCase()


def assert_equal_execution(expected: Dict[str, int],
                           actual: Dict[str, Set[str]]) -> None:
    test.assertEqual(expected.keys(), actual.keys())
    actual_dict = dict()

    for k, v in actual.items():
        actual_dict[k] = len(v)

    test.assertEqual(expected, actual_dict)
