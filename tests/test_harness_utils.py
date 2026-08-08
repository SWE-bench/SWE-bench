import unittest
from swebench.harness.utils import run_threadpool


class UtilTests(unittest.TestCase):
    def test_run_threadpool_all_failures(self):
        def failing_func(_):
            raise ValueError("Test error")

        payloads = [(1,), (2,), (3,)]
        succeeded, failed = run_threadpool(failing_func, payloads, max_workers=2)
        self.assertEqual(len(succeeded), 0)
        self.assertEqual(len(failed), 3)
