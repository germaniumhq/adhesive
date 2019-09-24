import copy
import unittest

from adhesive.workspace.kube.YamlMissing import YamlMissing


class YamlMissingTest(unittest.TestCase):
    def test_deep_copy(self):
        missing_property = YamlMissing(property_name="a.b")

        copied = copy.deepcopy(missing_property)

        self.assertTrue(copied is not missing_property)
        self.assertEqual("YamlMissing(a.b)", f"{missing_property}")


if __name__ == '__main__':
    unittest.main()
