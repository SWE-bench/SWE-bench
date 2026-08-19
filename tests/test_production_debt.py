import importlib.util
import os
import sys
import unittest

# Load module directly
file_path = os.path.join(
    os.path.dirname(__file__),
    "../swebench/metrics/production_debt.py",
)
spec = importlib.util.spec_from_file_location("swebench_production_debt", file_path)
production_debt_mod = importlib.util.module_from_spec(spec)
sys.modules["swebench_production_debt"] = production_debt_mod
spec.loader.exec_module(production_debt_mod)

ProductionDebtEvaluator = production_debt_mod.ProductionDebtEvaluator
TechnicalDueDiligenceLedger = production_debt_mod.TechnicalDueDiligenceLedger
GENESIS_HASH = production_debt_mod.GENESIS_HASH


class TestProductionDebtEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = ProductionDebtEvaluator(
            never_equate_intent_to_approval=True,
            max_acceptable_pdi=15.0,
        )

    def test_clean_patch_passes_production_readiness(self):
        report = self.evaluator.evaluate_patch(
            instance_id="django__django-12345",
            patch_text="def fix(): pass",
            context_tokens=2000,
            generated_tokens=100,
            cyclomatic_delta=0.5,
            un_gated_mutations=0,
        )
        self.assertTrue(report.is_production_ready)
        self.assertLessEqual(report.pdi_score, 15.0)
        self.assertEqual(len(report.critical_smells), 0)
        self.assertTrue(bool(report.receipt_hash))

    def test_degraded_patch_fails_due_diligence_pdi(self):
        report = self.evaluator.evaluate_patch(
            instance_id="sympy__sympy-99999",
            patch_text="while True: pass",
            context_tokens=1000,
            generated_tokens=2500,  # High token ratio (3.5x)
            cyclomatic_delta=8.0,   # High cyclomatic complexity spike
            un_gated_mutations=2,   # Un-gated production mutations
        )
        self.assertFalse(report.is_production_ready)
        self.assertGreater(report.pdi_score, 50.0)
        self.assertIn("HIGH_TOKEN_INFLATION_3.50X", report.critical_smells)
        self.assertIn("HIGH_CYCLOMATIC_COMPLEXITY_SPIKE_+8.0", report.critical_smells)
        self.assertIn("DETECTED_2_UNGATED_MUTATIONS", report.critical_smells)

    def test_cryptographic_ledger_integrity(self):
        self.evaluator.evaluate_patch("test-1", "patch1")
        self.evaluator.evaluate_patch("test-2", "patch2")
        self.evaluator.evaluate_patch("test-3", "patch3")

        entries = self.evaluator.ledger.get_ledger_entries()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["prev_hash"], GENESIS_HASH)
        self.assertEqual(entries[1]["prev_hash"], entries[0]["curr_hash"])
        self.assertEqual(entries[2]["prev_hash"], entries[1]["curr_hash"])
        self.assertTrue(self.evaluator.ledger.verify_ledger_integrity())


if __name__ == "__main__":
    unittest.main()
