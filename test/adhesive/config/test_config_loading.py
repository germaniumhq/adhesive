import unittest

from adhesive.config.LocalConfigReader import read_configuration


class TestConfigLoading(unittest.TestCase):
    def test_local_config_reading(self):
        config = read_configuration(
            cwd="test/adhesive/config/tc_local/local",
            environment={
                "HOME": "test/adhesive/config/tc_local/user",
                "ADHESIVE_ENVIRONMENT": "environment"
            }
        )

        self.assertEqual("local", config.local)
        self.assertEqual("user", config.user)
        self.assertEqual("environment", config.environment)
        self.assertEqual("/tmp", config.temp_folder)
        self.assertIsNone(config.not_existing)
