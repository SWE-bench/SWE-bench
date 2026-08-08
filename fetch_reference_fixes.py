#!/usr/bin/env python3
"""Fetch reference fixes from HuggingFace and save them"""

from datasets import load_dataset
import os

# Create directory for reference fixes
os.makedirs("reference_fixes", exist_ok=True)

# Load reference fixes
ds = load_dataset("inweriok/SWE-bench_Verified_gold_fixes", split="test")

# Find Astropy instances
astropy_instances = [x for x in ds if "astropy" in x["instance_id"]]

print(f"Found {len(astropy_instances)} Astropy instances in reference fixes\n")

for inst in astropy_instances:
    instance_id = inst["instance_id"]
    test_patch = inst["test_patch"]
    
    # Save reference fix
    filename = f"reference_fixes/{instance_id}_reference_test_patch.diff"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(test_patch)
    
    print(f"Saved: {filename}")
    print(f"  Patch length: {len(test_patch)} characters")
    print(f"  Files in patch: {test_patch.count('diff --git')}")
    print()

print("All reference fixes saved to reference_fixes/")
