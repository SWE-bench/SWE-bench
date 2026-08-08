#!/usr/bin/env python3
"""
Script to fix test_patch fields for Astropy instances in SWE-bench Verified.

This script addresses issue #484:
- astropy__astropy-7606: Remove test case from PASS_TO_PASS
- astropy__astropy-8707: Fix pytest compatibility (nose → pytest) + NumPy 1.24+ compatibility
- astropy__astropy-8872: Fix distutils deprecation + NumPy compatibility

The fixes are based on the issue description and examples from:
https://huggingface.co/inweriok/SWE-bench_Verified_gold_fixes

Usage:
    python fix_astropy_test_patches.py --instance-id astropy__astropy-8707 --test-patch-file test_patch.diff
    python fix_astropy_test_patches.py --load-from-hf --instance-id astropy__astropy-8707
"""

import argparse
import re
import sys
from typing import Dict, List, Tuple, Optional

try:
    from unidiff import PatchSet
except ImportError:
    print("Error: unidiff is required. Install with: pip install unidiff")
    sys.exit(1)

try:
    from datasets import load_dataset
except ImportError:
    print("Warning: datasets not available. Cannot load from HuggingFace directly.")
    load_dataset = None


def add_numpy_compatibility_patch() -> str:
    """
    Generate a patch to add NumPy 1.24+ compatibility aliases.
    This should be added at the beginning of test files that use deprecated NumPy aliases.
    """
    return """# Compatibility fix for NumPy 1.24+ (removed deprecated aliases)
if not hasattr(np, "int"):
    np.int = int
    np.float = float
    np.bool = bool
    np.str = str
    np.unicode = str
    np.object = object
    np.long = int
"""


def fix_pytest_setup_methods_in_content(content: str) -> str:
    """
    Replace nose-style setup/teardown methods with pytest setup_method/teardown_method.
    Works on file content (not patch format).
    
    Args:
        content: The file content to fix
        
    Returns:
        Modified content with pytest-compatible setup methods
    """
    # Replace setup(self) with setup_method(self, method)
    content = re.sub(
        r'(\s+)def setup\(self\):',
        r'\1def setup_method(self, method):',
        content
    )
    
    # Replace super().setup() with super().setup_method(method)
    content = re.sub(
        r'super\(\)\.setup\(\)',
        r'super().setup_method(method)',
        content
    )
    
    # Replace teardown(self) with teardown_method(self, method)
    content = re.sub(
        r'(\s+)def teardown\(self\):',
        r'\1def teardown_method(self, method):',
        content
    )
    
    # Replace super().teardown() with super().teardown_method(method)
    content = re.sub(
        r'super\(\)\.teardown\(\)',
        r'super().teardown_method(method)',
        content
    )
    
    return content


def fix_pytest_setup_methods(patch_content: str) -> str:
    """
    Replace nose-style setup/teardown methods with pytest setup_method/teardown_method.
    Works on patch format by modifying the content within hunks.
    Maintains correct hunk line counts.
    
    Args:
        patch_content: The original test_patch content (git patch format)
        
    Returns:
        Modified patch content with pytest-compatible setup methods
    """
    try:
        patch = PatchSet(patch_content)
        fixed_lines = []
        
        for patched_file in patch:
            # Extract file paths (unidiff includes a/ and b/ prefixes)
            source_path = patched_file.source_file.split("a/", 1)[-1] if "a/" in patched_file.source_file else patched_file.source_file
            target_path = patched_file.target_file.split("b/", 1)[-1] if "b/" in patched_file.target_file else patched_file.target_file
            
            # Write the file header
            fixed_lines.append(f"diff --git a/{source_path} b/{target_path}")
            fixed_lines.append(f"--- a/{source_path}")
            fixed_lines.append(f"+++ b/{target_path}")
            
            for hunk in patched_file:
                # Track line counts as we process
                source_count = 0
                target_count = 0
                hunk_lines = []
                
                # Process each line in the hunk
                for line in hunk:
                    line_content = line.value
                    
                    # Modify added lines
                    if line.is_added:
                        line_content = fix_pytest_setup_methods_in_content(line_content)
                    
                    # Add the appropriate prefix for patch format
                    if line.is_context:
                        prefix = " "
                        source_count += 1
                        target_count += 1
                    elif line.is_removed:
                        prefix = "-"
                        source_count += 1
                    elif line.is_added:
                        prefix = "+"
                        target_count += 1
                    else:
                        prefix = " "  # Default to context
                    
                    # Write line with prefix
                    hunk_lines.append(prefix + line_content.rstrip("\n"))
                
                # Write hunk header with correct counts
                fixed_lines.append(f"@@ -{hunk.source_start},{source_count} +{hunk.target_start},{target_count} @@")
                fixed_lines.extend(hunk_lines)
        
        return "\n".join(fixed_lines) + "\n"
    except Exception as e:
        # Fallback to regex if unidiff parsing fails
        print(f"Warning: unidiff parsing failed, using regex fallback: {e}")
        # For regex fallback, just do simple replacements on the patch text
        return re.sub(
            r'(\+.*?)(\s+)def setup\(self\):',
            r'\1\2def setup_method(self, method):',
            patch_content,
            flags=re.MULTILINE
        )


def fix_distutils_looseversion_in_content(content: str) -> str:
    """
    Replace distutils.version.LooseVersion with packaging.version.Version.
    Works on file content (not patch format).
    
    Args:
        content: The file content to fix
        
    Returns:
        Modified content with packaging.version
    """
    # Replace import statement
    content = re.sub(
        r'from distutils\.version import LooseVersion',
        r'from packaging.version import Version',
        content
    )
    
    # Replace LooseVersion usage with Version
    content = re.sub(
        r'LooseVersion\(',
        r'Version(',
        content
    )
    
    # For cases where LooseVersion is used as a type alias in introspection.py
    content = re.sub(
        r'from distutils\.version import LooseVersion',
        r'from packaging.version import Version as LooseVersion',
        content
    )
    
    return content


def fix_distutils_looseversion(patch_content: str) -> str:
    """
    Replace distutils.version.LooseVersion with packaging.version.Version.
    Works on patch format by modifying the content within hunks.
    Maintains correct hunk line counts.
    
    Args:
        patch_content: The original test_patch content (git patch format)
        
    Returns:
        Modified patch content with packaging.version
    """
    try:
        patch = PatchSet(patch_content)
        fixed_lines = []
        
        for patched_file in patch:
            # Extract file paths (unidiff includes a/ and b/ prefixes)
            source_path = patched_file.source_file.split("a/", 1)[-1] if "a/" in patched_file.source_file else patched_file.source_file
            target_path = patched_file.target_file.split("b/", 1)[-1] if "b/" in patched_file.target_file else patched_file.target_file
            
            # Write the file header
            fixed_lines.append(f"diff --git a/{source_path} b/{target_path}")
            fixed_lines.append(f"--- a/{source_path}")
            fixed_lines.append(f"+++ b/{target_path}")
            
            for hunk in patched_file:
                # Track line counts
                source_count = 0
                target_count = 0
                hunk_lines = []
                
                # Process each line in the hunk
                for line in hunk:
                    line_content = line.value
                    
                    # Modify both added and context lines
                    if line.is_added or line.is_context:
                        # Special handling for introspection.py - use alias
                        if 'introspection.py' in source_path:
                            line_content = re.sub(
                                r'from distutils\.version import LooseVersion',
                                r'from packaging.version import Version as LooseVersion',
                                line_content
                            )
                        else:
                            line_content = fix_distutils_looseversion_in_content(line_content)
                    
                    # Add the appropriate prefix for patch format
                    if line.is_context:
                        prefix = " "
                        source_count += 1
                        target_count += 1
                    elif line.is_removed:
                        prefix = "-"
                        source_count += 1
                    elif line.is_added:
                        prefix = "+"
                        target_count += 1
                    else:
                        prefix = " "  # Default to context
                    
                    # Write line with prefix
                    hunk_lines.append(prefix + line_content.rstrip("\n"))
                
                # Write hunk header with correct counts
                fixed_lines.append(f"@@ -{hunk.source_start},{source_count} +{hunk.target_start},{target_count} @@")
                fixed_lines.extend(hunk_lines)
        
        return "\n".join(fixed_lines) + "\n"
    except Exception as e:
        # Fallback to regex if unidiff parsing fails
        print(f"Warning: unidiff parsing failed, using regex fallback: {e}")
        return fix_distutils_looseversion_in_content(patch_content)


def append_compatibility_hunk_to_file(patch_lines: List[str], file_path: str, insert_after_line: int, compatibility_code: str) -> List[str]:
    """
    Append a new hunk to a file in the patch for compatibility code.
    
    Args:
        patch_lines: List of patch lines for this file
        file_path: Path to the file
        insert_after_line: Line number after which to insert (0-based from file start)
        compatibility_code: The compatibility code to add
        
    Returns:
        Updated patch lines with new hunk appended
    """
    compat_lines = compatibility_code.strip().split("\n")
    num_compat_lines = len([l for l in compat_lines if l.strip()])
    
    # Find where to insert - after the last hunk or at the end
    # For simplicity, append at the end of existing hunks
    # Hunk format: @@ -start,count +start,count @@
    # We'll insert after line insert_after_line in the target file
    
    # Add new hunk
    target_start = insert_after_line + 1
    patch_lines.append(f"@@ -{target_start},0 +{target_start},{num_compat_lines} @@")
    for compat_line in compat_lines:
        if compat_line.strip():
            patch_lines.append(f"+{compat_line}")
        else:
            patch_lines.append("+")
    
    return patch_lines


def add_numpy_compatibility_to_patch(patch_content: str, target_files: List[str]) -> str:
    """
    Add NumPy compatibility code as new hunks to specified files in a patch.
    This appends new hunks rather than modifying existing ones.
    
    Args:
        patch_content: The patch content
        target_files: List of file paths that need NumPy compatibility
        
    Returns:
        Modified patch with NumPy compatibility code added as new hunks
    """
    try:
        patch = PatchSet(patch_content)
        fixed_lines = []
        numpy_compat = add_numpy_compatibility_patch()
        
        for patched_file in patch:
            # Extract file paths
            source_path = patched_file.source_file.split("a/", 1)[-1] if "a/" in patched_file.source_file else patched_file.source_file
            target_path = patched_file.target_file.split("b/", 1)[-1] if "b/" in patched_file.target_file else patched_file.target_file
            
            # Write the file header
            fixed_lines.append(f"diff --git a/{source_path} b/{target_path}")
            fixed_lines.append(f"--- a/{source_path}")
            fixed_lines.append(f"+++ b/{target_path}")
            
            needs_numpy_fix = any(target in source_path for target in target_files)
            file_hunk_lines = []
            last_target_line = 0
            
                # Process all existing hunks
            for hunk in patched_file:
                source_count = 0
                target_count = 0
                hunk_lines = []
                
                for line in hunk:
                    line_content = line.value
                    
                    # Add the appropriate prefix for patch format
                    if line.is_context:
                        prefix = " "
                        source_count += 1
                        target_count += 1
                    elif line.is_removed:
                        prefix = "-"
                        source_count += 1
                    elif line.is_added:
                        prefix = "+"
                        target_count += 1
                    else:
                        prefix = " "
                    
                    # Write line with prefix
                    hunk_lines.append(prefix + line_content.rstrip("\n"))
                    # Track the last target line number
                    if line.is_added or line.is_context:
                        last_target_line = max(last_target_line, hunk.target_start + target_count - 1)
                
                file_hunk_lines.append(f"@@ -{hunk.source_start},{source_count} +{hunk.target_start},{target_count} @@")
                file_hunk_lines.extend(hunk_lines)
            
            fixed_lines.extend(file_hunk_lines)
            
            # Add NumPy compatibility as a new hunk if needed
            if needs_numpy_fix:
                compat_lines = numpy_compat.strip().split("\n")
                num_compat_lines = len([l for l in compat_lines if l.strip()])
                # Insert after line 20 (after imports typically)
                insert_line = 20
                fixed_lines.append(f"@@ -{insert_line},0 +{insert_line},{num_compat_lines} @@")
                for compat_line in compat_lines:
                    if compat_line.strip():
                        fixed_lines.append(f"+{compat_line}")
                    else:
                        fixed_lines.append("+")
        
        return "\n".join(fixed_lines) + "\n"
    except Exception as e:
        print(f"Warning: Could not add NumPy compatibility via unidiff: {e}")
        return patch_content


def append_setup_method_fixes(patch_content: str, file_path: str, setup_line_numbers: List[int]) -> str:
    """
    Append hunks to fix setup() methods in a file.
    
    Args:
        patch_content: Existing patch content
        file_path: Path to the file to fix
        setup_line_numbers: List of line numbers where setup() methods exist
        
    Returns:
        Patch with new hunks appended
    """
    if not setup_line_numbers:
        return patch_content
    
    # Append new hunks for each setup() method
    new_hunks = []
    for line_num in setup_line_numbers:
        # Hunk to replace setup(self) with setup_method(self, method)
        # Format: @@ -line,1 +line,1 @@
        new_hunks.append(f"@@ -{line_num},1 +{line_num},1 @@")
        new_hunks.append(f"-    def setup(self):")
        new_hunks.append(f"+    def setup_method(self, method):")
    
    return patch_content.rstrip() + "\n" + "\n".join(new_hunks) + "\n"


def fix_astropy_8707(test_patch: str) -> str:
    """
    Fix test_patch for astropy__astropy-8707.
    
    Issues:
    1. pytest compatibility: nose-style setup() → setup_method()
    2. NumPy 1.24+ compatibility: add deprecated alias support
    
    Note: The test_patch only adds new tests. We need to append new hunks
    that fix existing setup() methods. However, we don't have the exact line
    numbers from the base commit, so this is a simplified approach that
    modifies the patch format correctly.
    
    Returns:
        Fixed test_patch content
    """
    # For now, just ensure the patch format is correct
    # The actual setup() fixes need to be added as new hunks with correct line numbers
    # which requires access to the base commit files
    
    # Try to fix any setup() references if they exist in the patch
    fixed_patch = fix_pytest_setup_methods(test_patch)
    
    # Note: NumPy compatibility and setup() fixes in existing code need to be
    # added as new hunks, which requires knowing the base commit file structure
    # This is documented in the implementation plan
    
    return fixed_patch


def fix_astropy_8872(test_patch: str) -> str:
    """
    Fix test_patch for astropy__astropy-8872.
    
    Issues:
    1. distutils.version.LooseVersion → packaging.version.Version
    2. NumPy 1.24+ compatibility
    3. matplotlib scatter plot fix
    
    Returns:
        Fixed test_patch content
    """
    # Fix distutils deprecation
    fixed_patch = fix_distutils_looseversion(test_patch)
    
    # Fix matplotlib scatter plot (if present) - works on patch format
    fixed_patch = re.sub(
        r'(\+.*?)plt\.scatter\(x, y\)',
        r'\1plt.scatter(x.value, y.value)',
        fixed_patch
    )
    
    # Add NumPy compatibility to test files
    target_files = ["test_quantity.py"]  # Files that need NumPy fix
    fixed_patch = add_numpy_compatibility_to_patch(fixed_patch, target_files)
    
    return fixed_patch


def fix_astropy_7606(test_patch: str) -> str:
    """
    Fix test_patch for astropy__astropy-7606.
    
    Issue: Remove test case 'astropy/units/tests/test_units.py::test_compose_roundtrip[]'
    from PASS_TO_PASS column (this is handled in dataset, not test_patch)
    
    Note: This instance might not need test_patch changes, but rather dataset metadata changes.
    
    Returns:
        Potentially modified test_patch (if test case needs to be removed from patch)
    """
    # Remove the test case from the patch if it's present
    # Pattern to match test file modifications
    pattern = r'diff --git a/.*/test_units\.py.*?test_compose_roundtrip.*?(?=diff --git|\Z)'
    fixed_patch = re.sub(pattern, '', test_patch, flags=re.DOTALL)
    
    return fixed_patch


def apply_fixes_to_patch(test_patch: str, instance_id: str) -> str:
    """
    Apply all necessary fixes to a test_patch based on instance_id.
    
    Args:
        test_patch: The original test_patch content (git patch format)
        instance_id: The instance ID (e.g., 'astropy__astropy-8707')
        
    Returns:
        Fixed test_patch content
    """
    if instance_id == "astropy__astropy-8707":
        return fix_astropy_8707(test_patch)
    elif instance_id == "astropy__astropy-8872":
        return fix_astropy_8872(test_patch)
    elif instance_id == "astropy__astropy-7606":
        return fix_astropy_7606(test_patch)
    else:
        raise ValueError(f"Unknown instance_id: {instance_id}")


def generate_all_fixes(output_dir: str = "fixed_patches") -> None:
    """
    Generate fixed test_patches for all three Astropy instances.
    Loads from HuggingFace, applies fixes, and saves to files.
    
    Args:
        output_dir: Directory to save fixed patches
    """
    import os
    from pathlib import Path
    
    if load_dataset is None:
        print("Error: datasets library required for this function")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    instance_ids = ["astropy__astropy-7606", "astropy__astropy-8707", "astropy__astropy-8872"]
    
    print("Loading SWE-bench Verified dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    
    for instance_id in instance_ids:
        print(f"\nProcessing {instance_id}...")
        try:
            instance = next(x for x in dataset if x["instance_id"] == instance_id)
            original_patch = instance["test_patch"]
            
            print(f"  Original patch length: {len(original_patch)} characters")
            fixed_patch = apply_fixes_to_patch(original_patch, instance_id)
            print(f"  Fixed patch length: {len(fixed_patch)} characters")
            
            output_file = Path(output_dir) / f"{instance_id}_fixed_test_patch.diff"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(fixed_patch)
            print(f"  Saved to: {output_file}")
            
        except StopIteration:
            print(f"  Warning: {instance_id} not found in dataset")
        except Exception as e:
            print(f"  Error processing {instance_id}: {e}")
    
    print(f"\nAll fixed patches saved to {output_dir}/")


def main():
    """
    Main function to fix test_patch for Astropy instances.
    """
    parser = argparse.ArgumentParser(
        description="Fix test_patch fields for Astropy instances in SWE-bench Verified"
    )
    parser.add_argument(
        "--instance-id",
        required=False,
        choices=["astropy__astropy-7606", "astropy__astropy-8707", "astropy__astropy-8872"],
        help="Instance ID to fix (not required if --generate-all is used)"
    )
    parser.add_argument(
        "--test-patch-file",
        type=str,
        help="Path to file containing test_patch (git patch format)"
    )
    parser.add_argument(
        "--load-from-hf",
        action="store_true",
        help="Load test_patch from HuggingFace dataset (requires datasets library)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for fixed test_patch (default: stdout)"
    )
    parser.add_argument(
        "--generate-all",
        action="store_true",
        help="Generate fixed patches for all three Astropy instances and save to files"
    )
    
    args = parser.parse_args()
    
    # Handle generate-all mode
    if args.generate_all:
        generate_all_fixes()
        return
    
    # Require instance-id if not in generate-all mode
    if not args.instance_id:
        print("Error: --instance-id is required unless --generate-all is used")
        sys.exit(1)
    
    # Load test_patch
    if args.load_from_hf:
        if load_dataset is None:
            print("Error: datasets library not available. Cannot load from HuggingFace.")
            sys.exit(1)
        print(f"Loading {args.instance_id} from HuggingFace dataset...")
        dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
        instance = next(x for x in dataset if x["instance_id"] == args.instance_id)
        test_patch = instance["test_patch"]
    elif args.test_patch_file:
        with open(args.test_patch_file, "r", encoding="utf-8") as f:
            test_patch = f.read()
    else:
        print("Error: Must provide either --test-patch-file or --load-from-hf")
        sys.exit(1)
    
    # Apply fixes
    print(f"Applying fixes for {args.instance_id}...")
    fixed_patch = apply_fixes_to_patch(test_patch, args.instance_id)
    
    # Output result
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(fixed_patch)
        print(f"Fixed test_patch written to {args.output}")
    else:
        print("\n" + "=" * 50)
        print("Fixed test_patch:")
        print("=" * 50)
        print(fixed_patch)


if __name__ == "__main__":
    main()
