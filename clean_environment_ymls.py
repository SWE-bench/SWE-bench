"""
Clean environment.yml files by removing the repo's own package from pip dependencies.

The repo's package (e.g., astropy, django) gets installed via setup commands later,
so having it in the environment.yml with a dev version causes build failures.
"""

import re
from pathlib import Path
from tqdm import tqdm


def get_package_name_from_instance_id(instance_id: str) -> str:
    """
    Get the package name from instance_id.
    E.g., astropy__astropy-11693 -> astropy
         django__django-10087 -> django
    """
    # Split by double underscore, take last part before single underscore
    parts = instance_id.split("__")
    if len(parts) >= 2:
        # Handle cases like django__django-10087 or matplotlib__matplotlib-13859
        repo_name = parts[1].split("-")[0]
        return repo_name.lower()
    return None


def clean_environment_yml(yml_text: str, package_to_remove: str) -> str:
    """
    Remove a specific package from the pip dependencies section.
    """
    if not package_to_remove:
        return yml_text

    # Find the pip section
    pip_match = re.search(r"^(\s*-\s*pip\s*:\s*\n)", yml_text, flags=re.MULTILINE)
    if not pip_match:
        return yml_text

    pip_content_start = pip_match.end()
    pip_indent = len(pip_match.group(1)) - len(pip_match.group(1).lstrip())

    # Find where pip section ends
    lines_after_pip = yml_text[pip_content_start:].split("\n")
    pip_section_end = pip_content_start
    for ix, line in enumerate(lines_after_pip):
        if line.strip() == "":
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= pip_indent:
            pip_section_end = pip_content_start + sum(
                len(l) + 1 for l in lines_after_pip[:ix]
            )
            break
    else:
        pip_section_end = len(yml_text)

    prefix = yml_text[:pip_content_start]
    pip_portion = yml_text[pip_content_start:pip_section_end]
    suffix = yml_text[pip_section_end:]

    # Remove the package line (handles == and other version specs)
    # Pattern: "      - package==version" or "      - package>=version" etc.
    pattern = rf"^(\s*-\s*){re.escape(package_to_remove)}([<>=!~].*)?$\n?"
    cleaned_pip = re.sub(pattern, "", pip_portion, flags=re.MULTILINE | re.IGNORECASE)

    return prefix + cleaned_pip + suffix


def main():
    env_base = Path("swebench/resources/swebench-og/environments")

    total_files = sum(1 for _ in env_base.rglob("*.yml"))
    cleaned = 0
    skipped = 0

    print(f"Cleaning {total_files} environment files...")

    for env_file in tqdm(list(env_base.rglob("*.yml")), desc="Cleaning"):
        instance_id = env_file.stem
        package_name = get_package_name_from_instance_id(instance_id)

        if not package_name:
            skipped += 1
            continue

        yml_text = env_file.read_text()

        # Check if package exists in the file
        if re.search(
            rf"^\s*-\s*{re.escape(package_name)}[<>=!~]",
            yml_text,
            re.MULTILINE | re.IGNORECASE,
        ):
            cleaned_text = clean_environment_yml(yml_text, package_name)
            env_file.write_text(cleaned_text)
            cleaned += 1
        else:
            skipped += 1

    print("\nResults:")
    print(f"  Cleaned: {cleaned}")
    print(f"  Skipped (no package found): {skipped}")
    print(f"  Total: {total_files}")


if __name__ == "__main__":
    main()
