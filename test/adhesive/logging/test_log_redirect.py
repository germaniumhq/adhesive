import sys
import unittest
import uuid

from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive import logredirect
from adhesive.storage.ensure_folder import ensure_folder


class TestLogRedirection(unittest.TestCase):
    def test_file_redirection_logs(self):
        original_stdout_fileno = sys.stdout.fileno()
        original_stderr_fileno = sys.stderr.fileno()

        target_folder = ensure_folder(str(uuid.uuid4()))

        self.assertEqual(original_stdout_fileno, sys.stdout.fileno())
        self.assertEqual(original_stderr_fileno, sys.stderr.fileno())
        print("x")

        with redirect_stdout(target_folder):
            self.assertNotEqual(original_stdout_fileno, sys.stdout.fileno())
            self.assertNotEqual(original_stderr_fileno, sys.stderr.fileno())
            print("y")

        self.assertEqual(original_stdout_fileno, sys.stdout.fileno())
        self.assertEqual(original_stderr_fileno, sys.stderr.fileno())
        print("z")


if __name__ == '__main__':
    unittest.main()
