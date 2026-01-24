# HuggingFace Dataset Update Requirements

## Overview

To fully resolve issue #484, the `test_patch` field in the HuggingFace dataset `princeton-nlp/SWE-bench_Verified` needs to be updated for three Astropy instances.

## Required Updates

### 1. astropy__astropy-7606

**Current Issue:**
- Test case `astropy/units/tests/test_units.py::test_compose_roundtrip[]` appears in `PASS_TO_PASS` column but should be removed

**Dataset Update Required:**
- **Field**: `PASS_TO_PASS`
- **Action**: Remove `"astropy/units/tests/test_units.py::test_compose_roundtrip[]"` from the list
- **Note**: This is a metadata change, not a test_patch change

### 2. astropy__astropy-8707

**Current Issue:**
- pytest compatibility: nose-style `setup(self)` methods cause failures
- NumPy 1.24+ compatibility: deprecated type aliases removed

**Dataset Update Required:**
- **Field**: `test_patch`
- **Action**: Replace with fixed test_patch that includes:
  1. Original test additions (2 new test methods)
  2. New hunk fixing `setup()` → `setup_method()` in `test_header.py`
  3. New hunk fixing `setup()`/`teardown()` in `__init__.py` (FitsTestCase)
  4. New hunk adding NumPy compatibility code after imports

**Files to modify in test_patch:**
- `astropy/io/fits/tests/test_header.py`
- `astropy/io/fits/tests/__init__.py`

### 3. astropy__astropy-8872

**Current Issue:**
- distutils.version.LooseVersion deprecated
- NumPy 1.24+ compatibility
- matplotlib scatter plot issue

**Dataset Update Required:**
- **Field**: `test_patch`
- **Action**: Replace with fixed test_patch that includes:
  1. Original test additions
  2. New hunk replacing `LooseVersion` → `Version` in test files
  3. New hunk replacing `LooseVersion` → `Version as LooseVersion` in `introspection.py`
  4. New hunk adding NumPy compatibility code
  5. Fix matplotlib scatter plot calls

**Files to modify in test_patch:**
- `astropy/units/tests/test_quantity.py`
- `astropy/utils/introspection.py`

## How to Update

### Option 1: Using the Script

The `fix_astropy_test_patches.py` script can generate the fixed patches:

```bash
python fix_astropy_test_patches.py --generate-all
```

This creates fixed patches in `fixed_patches/` directory that can be used to update the dataset.

### Option 2: Manual Update

1. Load the dataset from HuggingFace
2. For each instance, replace the `test_patch` field with the fixed version
3. Upload the updated dataset

### Option 3: Using HuggingFace Dataset Scripts

Create a script that:
1. Loads the current dataset
2. Applies fixes using `fix_astropy_test_patches.py`
3. Updates the dataset with new test_patch values
4. Pushes the updated dataset

## Dataset Structure

The dataset is at: `princeton-nlp/SWE-bench_Verified`

**Fields to update:**
- `test_patch` (string): Git patch format for test modifications
- `PASS_TO_PASS` (list): For astropy-7606 only

## Validation

After updating the dataset:

1. Run gold patch evaluation:
   ```bash
   python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Verified \
       --predictions_path gold \
       --max_workers 1 \
       --instance_ids astropy__astropy-8707 astropy__astropy-8872 astropy__astropy-7606 \
       --run_id validate-fixed-patches
   ```

2. Verify all instances pass validation
3. Check that test outputs show no pytest/NumPy/distutils errors

## References

- Issue: #484
- Fix examples: https://huggingface.co/inweriok/SWE-bench_Verified_gold_fixes
- Dataset: https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified
