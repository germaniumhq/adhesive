import unittest
import copy

from adhesive.workspace.kube.YamlDictNavigator import YamlDictNavigator
from adhesive.workspace.kube.YamlListNavigator import YamlListNavigator


class YamlListNavigatorTest(unittest.TestCase):
    def test_simple_property_read(self):
        p = YamlListNavigator([{"x":3}])

        self.assertEqual(3, p[0].x)

    def test_nested_property_read(self):
        p = YamlDictNavigator({
            "x": 3,
            "y": {
                "key": 1,
                "list": [1, {
                    "more": [1, {
                        "nested": ["nested"]
                    }]
                }, 3]
            }
        })

        self.assertEqual(1, p.y.key)
        self.assertEqual(["nested"], p.y.list[1].more[1].nested._raw())

    def test_read_via_get(self):
        p = YamlListNavigator([ [1, 2, 3] ])

        self.assertEqual([1,2,3], p[0])

    def test_write_with_set(self):
        p = YamlListNavigator(["original"])

        p[0] = "new"

        self.assertEqual("new", p[0])

    def test_iteration_as_iterable(self):
        p = YamlListNavigator(["x", "y", "z"])
        items = set()

        for item in p:
            items.add(item)

        self.assertSetEqual({"x", "y", "z"}, items)

    def test_set_nested_property_navigator(self):
        """
        The `__content` should always be kept as objects pointing to each other,
        not property navigators.
        :return:
        """
        p = YamlListNavigator()
        x = YamlListNavigator()

        p.x = x
        p.x.y1 = "y1"
        x.y2 = "y2"
        p.y = "y"

        self.assertEqual(p, {'x': {'y1': 'y1', 'y2': 'y2'}, 'y': 'y'})

    def test_deep_copy_really_deep_copies(self):
        items = [1, 2, 3]
        p = YamlListNavigator(items)

        p_copy = copy.deepcopy(p)
        p_copy[0] = 0

        self.assertEqual(0, p_copy[0])
        self.assertEqual(1, items[0])
        self.assertEqual(1, p[0])

    def test_len_works(self):
        items = [1, 2, 3]
        p = YamlListNavigator(items)

        self.assertEqual(3, len(items))

    def test_is_empty(self):
        items = [1, 2, 3]

        p = YamlListNavigator(items)
        self.assertTrue(p)

        p = YamlListNavigator()
        self.assertFalse(p)

        p = YamlListNavigator([])
        self.assertFalse(p)
