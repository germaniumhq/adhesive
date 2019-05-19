import sys
import unittest
import uuid
import time

from adhesive.logging.LogRedirect import redirect_stdout
from adhesive.storage.ensure_folder import ensure_folder


class LogRedirectTest(unittest.TestCase):
    def test_file_redirection_logs(self):
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        target_folder = ensure_folder(str(uuid.uuid4()))

        print("x")
        with redirect_stdout(target_folder):
            print("y")
        print("z")

        self.assertEqual(original_stdout, sys.stdout)
        self.assertEqual(original_stderr, sys.stderr)


if __name__ == '__main__':
    unittest.main()
