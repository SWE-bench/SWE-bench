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


class MakeTestSpecTests(unittest.TestCase):
    # A row of a pre-5.0 dataset such as princeton-nlp/SWE-bench_Verified: no image,
    # eval_script, log_parser or eval_type.
    LEGACY_INSTANCE = {
        "instance_id": "django__django-11400",
        "repo": "django/django",
        "version": "3.0",
        "FAIL_TO_PASS": "[]",
        "PASS_TO_PASS": "[]",
    }

    def test_legacy_dataset_row_names_missing_fields(self):
        from swebench.harness.utils import make_test_spec

        with self.assertRaises(ValueError) as ctx:
            make_test_spec(self.LEGACY_INSTANCE)
        message = str(ctx.exception)
        self.assertIn("django__django-11400", message)
        for field in ("eval_script", "eval_type", "image", "log_parser"):
            self.assertIn(field, message)
        self.assertIn("SWE-bench/SWE-bench_Verified", message)
