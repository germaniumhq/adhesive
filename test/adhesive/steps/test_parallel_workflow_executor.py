import concurrent
import time
import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from .test_tasks import adhesive, _async


class TestWorkflowExecutor(unittest.TestCase):
    def test_parallel_tasks(self):
        """
        Load a bunch of tasks in parallel.
        :return:
        """
        WorkflowExecutor.pool = concurrent.futures.ProcessPoolExecutor(max_workers=6)
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/parallel5.bpmn")

        start_time = time.time() * 1000.0
        _async(WorkflowExecutor(adhesive.process).execute())
        end_time = time.time() * 1000.0

        # the whole thing should be faster than 2 secs
        total_time = end_time - start_time
        self.assertTrue(total_time < 2000,
                        f"Total time ({total_time}) should be less than 2000ms.")
        self.assertTrue(total_time >= 1000,
                        f"Total time ({total_time}) should be more than 1000ms.")

    def test_parallel_sub_processes_tasks(self):
        """
        Load a bunch of tasks in parallel.
        :return:
        """
        WorkflowExecutor.pool = concurrent.futures.ProcessPoolExecutor(max_workers=6)
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/parallel5-sub-processes.bpmn")

        start_time = time.time() * 1000.0
        _async(WorkflowExecutor(adhesive.process).execute())
        end_time = time.time() * 1000.0

        # the whole thing should be faster than 2 secs
        total_time = end_time - start_time
        self.assertTrue(total_time < 2000,
                        f"Total time ({total_time}) should be less than 2000ms.")
        self.assertTrue(total_time >= 1000,
                        f"Total time ({total_time}) should be more than 1000ms.")


if __name__ == '__main__':
    unittest.main()
