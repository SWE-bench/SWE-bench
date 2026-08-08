#!/usr/bin/env python3
"""
Generate complete fixed test patches using reference fixes as the source of truth.

This script:
1. Loads the original test_patch from SWE-bench_Verified
2. Loads the reference fixes from SWE-bench_Verified_gold_fixes
3. Generates complete fixed patches that match the reference fixes
4. Validates the generated patches
"""

import os
import sys
from pathlib import Path

try:
    from datasets import load_dataset
    from unidiff import PatchSet
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Install with: pip install datasets unidiff")
    sys.exit(1)


def validate_patch(patch_content: str) -> bool:
    """Validate that a patch can be parsed by unidiff."""
    try:
        patch = PatchSet(patch_content)
        return len(patch) > 0
    except Exception as e:
        print(f"  Validation error: {e}")
        return False


def generate_complete_fixes():
    """Generate complete fixed patches for all Astropy instances."""
    
    # Load original dataset
    print("Loading original SWE-bench_Verified dataset...")
    original_ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    
    # Load reference fixes
    print("Loading reference fixes from SWE-bench_Verified_gold_fixes...")
    reference_ds = load_dataset("inweriok/SWE-bench_Verified_gold_fixes", split="test")
    
    # Create output directory
    output_dir = Path("fixed_patches")
    output_dir.mkdir(exist_ok=True)
    
    # Process each Astropy instance
    astropy_instances = ["astropy__astropy-7606", "astropy__astropy-8707", "astropy__astropy-8872"]
    
    for instance_id in astropy_instances:
        print(f"\n{'='*60}")
        print(f"Processing {instance_id}...")
        print(f"{'='*60}")
        
        # Get original patch
        original_inst = next((x for x in original_ds if x["instance_id"] == instance_id), None)
        if not original_inst:
            print(f"  ERROR: Instance not found in original dataset")
            continue
        
        original_patch = original_inst["test_patch"]
        print(f"  Original patch length: {len(original_patch)} characters")
        
        # Get reference fix
        reference_inst = next((x for x in reference_ds if x["instance_id"] == instance_id), None)
        if not reference_inst:
            print(f"  WARNING: No reference fix found, using original patch")
            complete_patch = original_patch
        else:
            complete_patch = reference_inst["test_patch"]
            print(f"  Reference fix length: {len(complete_patch)} characters")
        
        # Validate the complete patch
        print(f"  Validating complete patch...")
        if validate_patch(complete_patch):
            print(f"  OK Patch is valid")
        else:
            print(f"  ERROR Patch validation failed")
            continue
        
        # Save the complete patch
        output_file = output_dir / f"{instance_id}_complete_fixed_test_patch.diff"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(complete_patch)
        
        print(f"  Saved to: {output_file}")
        
        # Show summary
        patch = PatchSet(complete_patch)
        print(f"  Files in patch: {len(patch)}")
        for patched_file in patch:
            print(f"    - {patched_file.source_file} ({len(patched_file)} hunks)")
    
    print(f"\n{'='*60}")
    print("All complete fixed patches generated!")
    print(f"{'='*60}")


if __name__ == "__main__":
    generate_complete_fixes()
