import unittest
import copy

from adhesive.workspace.kube.YamlDictNavigator import YamlDictNavigator


class YamlDictNavigatorTest(unittest.TestCase):
    def test_simple_property_read(self):
        p = YamlDictNavigator({
            "x": 3
        })

        self.assertEqual(3, p.x)

    def test_nested_property_read(self):
        p = YamlDictNavigator({
            "x": 3,
            "y": {
                "key": 1,
                "list": [1, 2, 3]
            }
        })

        self.assertEqual(1, p.y.key)
        self.assertEqual([1, 2, 3], p.y.list._raw)

    def test_read_via_get(self):
        p = YamlDictNavigator({
            "items": [1, 2, 3]
        })

        self.assertEqual([1,2,3], p["items"]._raw)

    def test_write_with_property(self):
        p = YamlDictNavigator({
            "x": "original"
        })

        p.x = "new"

        self.assertEqual("new", p.x)
        self.assertEqual("new", p["x"])

    def test_write_with_set(self):
        p = YamlDictNavigator({
            "x": "original"
        })

        p["x"] = "new"

        self.assertEqual("new", p.x)
        self.assertEqual("new", p["x"])

    def test_iteration_as_iterable(self):
        p = YamlDictNavigator({
            "x": "original",
            "y": "original",
            "z": "original",
        })
        items = set()

        for item in p:
            items.add(item)

        self.assertSetEqual({"x", "y", "z"}, items)

    def test_iteration_key_value(self):
        p = YamlDictNavigator({
            "x": "x",
            "y": "y",
            "z": "z",
        })

        items = dict()

        for k,v in p._items():
            items[k] = v

        self.assertDictEqual({
            "x": "x",
            "y": "y",
            "z": "z",
        }, items)

    def test_set_nested_property_navigator(self):
        """
        The `__content` should always be kept as objects pointing to each other,
        not property navigators.
        :return:
        """
        p = YamlDictNavigator()
        x = YamlDictNavigator()

        p.x = x
        p.x.y1 = "y1"
        x.y2 = "y2"
        p.y = "y"

        self.assertEqual({'x': {'y1': 'y1', 'y2': 'y2'}, 'y': 'y'}, p._raw)

    def test_deep_copy_really_deep_copies(self):
        dict = {"x": 1}
        p = YamlDictNavigator(dict)

        p_copy = copy.deepcopy(p)
        p_copy.x = 2

        self.assertEqual(2, p_copy.x)
        self.assertEqual(1, dict["x"])
        self.assertEqual(1, p.x)

    def test_len(self):
        d = YamlDictNavigator({"x": 1, "y": 2, "z": 3})
        self.assertEqual(3, len(d))

    def test_removal_attribute(self):
        d = YamlDictNavigator({"x": 1, "y": 2, "z": 3})
        del d.x

        self.assertEqual({"y": 2, "z": 3}, d._raw)

    def test_removal_item(self):
        d = YamlDictNavigator({"x": 1, "y": 2, "z": 3})
        del d["x"]

        self.assertEqual({"y": 2, "z": 3}, d._raw)
