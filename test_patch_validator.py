#!/usr/bin/env python3
"""Quick script to validate patch format"""

from unidiff import PatchSet
import sys

if len(sys.argv) < 2:
    print("Usage: python test_patch_validator.py <patch_file>")
    sys.exit(1)

patch_file = sys.argv[1]
try:
    with open(patch_file, 'r', encoding='utf-8') as f:
        patch_content = f.read()
    
    patch = PatchSet(patch_content)
    print(f"✓ Patch is valid: {len(patch)} file(s)")
    for f in patch:
        print(f"  - {f.source_file} ({len(f)} hunks)")
except Exception as e:
    print(f"✗ Patch is invalid: {e}")
    sys.exit(1)
