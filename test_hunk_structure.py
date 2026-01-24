#!/usr/bin/env python3
"""Test script to understand hunk structure"""

from unidiff import PatchSet
from datasets import load_dataset

ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
inst = next(x for x in ds if x["instance_id"] == "astropy__astropy-8707")
patch_content = inst["test_patch"]

patch = PatchSet(patch_content)
f = patch[0]
h = f[0]

print("Original hunk header from patch:")
print(f"  @@ -{h.source_start},{h.source_length} +{h.target_start},{h.target_length} @@")

print("\nActual lines in hunk:")
source_lines = 0
target_lines = 0
for i, line in enumerate(h):
    print(f"  {i}: {repr(line.value[:60])} - type: {line.line_type}")
    if line.is_context or line.is_removed:
        source_lines += 1
    if line.is_context or line.is_added:
        target_lines += 1
    if i >= 15:  # Show first 15 lines
        print("  ...")
        break

print(f"\nCounted: source={source_lines}, target={target_lines}")
print(f"Original: source={h.source_length}, target={h.target_length}")
