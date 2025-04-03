import unittest
from unittest.mock import MagicMock, patch
from tqdm import tqdm
from swebench.harness.utils import run_threadpool

class UtilTests(unittest.TestCase):
    @patch('swebench.harness.utils.tqdm')
    def test_pbar_updates_correctly_with_all_failures(self, mock_tqdm):
        # Create mock progress bar
        mock_pbar = MagicMock()

        # Configure mock chain
        mock_tqdm.return_value = mock_pbar
        mock_pbar.__enter__.return_value = mock_pbar
        mock_pbar.__exit__.return_value = None

        def failing_func(_):
            raise ValueError("Test error")

        # Run the function
        payloads = [(1,), (2,), (3,)]
        succeeded, failed = run_threadpool(failing_func, payloads, max_workers=2)

        # Verify mock_pbar was used correctly
        self.assertEqual(3, len(failed))
        self.assertEqual(3, mock_pbar.update.call_count)
        self.assertEqual(3, mock_pbar.set_description.call_count)
        mock_pbar.set_description.assert_called_with(
            "0 ran successfully, 3 failed"
        )