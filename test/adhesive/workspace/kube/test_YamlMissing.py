import copy
import unittest

from adhesive.workspace.kube.YamlDict import YamlDict
from adhesive.workspace.kube.YamlMissing import YamlMissing
from adhesive.workspace.kube.YamlNavigator import YamlNavigator


class YamlMissingTest(unittest.TestCase):
    def test_deep_copy(self):
        missing_property = YamlMissing(
            parent_property=None,
            property_name="b",
            full_property_name="a.b")

        copied = copy.deepcopy(missing_property)

        self.assertTrue(copied is not missing_property)
        self.assertEqual("YamlMissing(a.b)", f"{missing_property}")

    def test_get_item(self):
        missing_property = YamlMissing(
            parent_property=None,
            property_name="b",
            full_property_name="a.b")
        self.assertFalse(missing_property["x"])

    def test_set_attribute(self):
        p = YamlDict()

        p.x.y.z = "test"
        self.assertEqual("test", p.x.y.z)

    def test_set_item(self):
        p = YamlDict()

        p["x"]["y"]["z"] = "test"
        self.assertEqual("test", p["x"]["y"]["z"])

    @unittest.expectedFailure
    def test_set_missing_fails(self):
        a = YamlMissing(
            parent_property=None,
            property_name="a",
            full_property_name="x.a"
        )

        a.x = True


if __name__ == '__main__':
    unittest.main()
