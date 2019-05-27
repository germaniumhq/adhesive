import sys
import unittest
import uuid

from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive.storage.ensure_folder import ensure_folder


class TestLogRedirection(unittest.TestCase):
    def test_file_redirection_logs(self):
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        target_folder = ensure_folder(str(uuid.uuid4()))

        self.assertEqual(original_stdout, sys.stdout)
        self.assertEqual(original_stderr, sys.stderr)
        print("x")

        with redirect_stdout(target_folder):
            self.assertNotEqual(original_stdout, sys.stdout)
            self.assertNotEqual(original_stderr, sys.stderr)
            print("y")

        self.assertEqual(original_stdout, sys.stdout)
        self.assertEqual(original_stderr, sys.stderr)
        print("z")


if __name__ == '__main__':
    unittest.main()
