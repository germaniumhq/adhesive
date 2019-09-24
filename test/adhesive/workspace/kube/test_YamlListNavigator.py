import unittest
import copy

from adhesive.workspace.kube.YamlDictNavigator import YamlDictNavigator
from adhesive.workspace.kube.YamlListNavigator import YamlListNavigator


class YamlListNavigatorTest(unittest.TestCase):
    def test_simple_property_read(self):
        p = YamlListNavigator(content=[{"x":3}])

        self.assertEqual(3, p[0].x)

    def test_nested_property_read(self):
        p = YamlDictNavigator(content={
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
        self.assertEqual(["nested"], p.y.list[1].more[1].nested._raw)

    def test_read_via_get(self):
        p = YamlListNavigator(content=[ [1, 2, 3] ])

        self.assertEqual([1,2,3], p[0]._raw)

    def test_write_with_set(self):
        p = YamlListNavigator(content=["original"])

        p[0] = "new"

        self.assertEqual("new", p[0])

    def test_iteration_as_iterable(self):
        p = YamlListNavigator(content=["x", "y", "z"])
        items = set()

        for item in p:
            items.add(item)

        self.assertSetEqual({"x", "y", "z"}, items)

    def test_deep_copy_really_deep_copies(self):
        items = [1, 2, 3]
        p = YamlListNavigator(content=items)

        p_copy = copy.deepcopy(p)
        p_copy[0] = 0

        self.assertEqual(0, p_copy[0])
        self.assertEqual(1, items[0])
        self.assertEqual(1, p[0])

    def test_len_works(self):
        items = [1, 2, 3]
        p = YamlListNavigator(content=items)

        self.assertEqual(3, len(p))

    def test_is_empty(self):
        items = [1, 2, 3]

        p = YamlListNavigator(content=items)
        self.assertTrue(p)

        p = YamlListNavigator()
        self.assertFalse(p)

        p = YamlListNavigator(content=[])
        self.assertFalse(p)

    def test_removal(self):
        p = YamlListNavigator(content=[1, 2, 3])
        del p[0]

        self.assertEqual([2, 3], p._raw)

    def test_repr(self):
        p = YamlListNavigator(
            property_name="a.b",
            content=[1, 2, 3])

        representation = f"{p}"

        self.assertEqual("YamlListNavigator(a.b) [1, 2, 3]", representation)


    def test_nested_repr(self):
        p = YamlDictNavigator(
            property_name="a.b",
            content={
                "x": [{
                    "y": [1, 2, 3]
                }]
            }
        )

        representation = f"{p.x[0].y}"
        self.assertEqual("YamlListNavigator(a.b.x.0.y) [1, 2, 3]", representation)

        representation = f"{p.x[0].z}"
        self.assertEqual("YamlNoopNavigator(a.b.x.0.z)", representation)

if __name__ == '__main__':
    unittest.main()
