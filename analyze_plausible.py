import os
import json
from pathlib import Path

original_agentless_resolved =  [
    "astropy__astropy-12907",
    "astropy__astropy-13453",
    "astropy__astropy-14096",
    "astropy__astropy-14309",
    "astropy__astropy-14539",
    "astropy__astropy-7166",
    "astropy__astropy-7336",
    "astropy__astropy-7671",
    "django__django-10097",
    "django__django-10880",
    "django__django-10914",
    "django__django-10973",
    "django__django-11066",
    "django__django-11095",
    "django__django-11099",
    "django__django-11119",
    "django__django-11133",
    "django__django-11163",
    "django__django-11179",
    "django__django-11292",
    "django__django-11333",
    "django__django-11451",
    "django__django-11551",
    "django__django-11555",
    "django__django-11603",
    "django__django-11749",
    "django__django-11790",
    "django__django-11848",
    "django__django-11880",
    "django__django-11964",
    "django__django-12143",
    "django__django-12155",
    "django__django-12209",
    "django__django-12276",
    "django__django-12419",
    "django__django-12708",
    "django__django-12713",
    "django__django-13089",
    "django__django-13109",
    "django__django-13279",
    "django__django-13315",
    "django__django-13363",
    "django__django-13410",
    "django__django-13417",
    "django__django-13516",
    "django__django-13658",
    "django__django-13670",
    "django__django-13786",
    "django__django-13810",
    "django__django-13820",
    "django__django-13821",
    "django__django-13837",
    "django__django-13933",
    "django__django-13964",
    "django__django-14053",
    "django__django-14089",
    "django__django-14122",
    "django__django-14238",
    "django__django-14349",
    "django__django-14373",
    "django__django-14493",
    "django__django-14500",
    "django__django-14539",
    "django__django-14752",
    "django__django-14765",
    "django__django-14787",
    "django__django-14855",
    "django__django-14915",
    "django__django-14999",
    "django__django-15104",
    "django__django-15277",
    "django__django-15278",
    "django__django-15315",
    "django__django-15368",
    "django__django-15380",
    "django__django-15467",
    "django__django-15499",
    "django__django-15561",
    "django__django-15569",
    "django__django-15731",
    "django__django-15814",
    "django__django-15863",
    "django__django-15987",
    "django__django-16082",
    "django__django-16116",
    "django__django-16139",
    "django__django-16145",
    "django__django-16255",
    "django__django-16333",
    "django__django-16429",
    "django__django-16485",
    "django__django-16527",
    "django__django-16569",
    "django__django-16595",
    "django__django-16612",
    "django__django-16642",
    "django__django-16662",
    "django__django-16801",
    "django__django-16819",
    "django__django-16899",
    "django__django-17029",
    "django__django-17084",
    "django__django-7530",
    "django__django-9296",
    "matplotlib__matplotlib-13989",
    "matplotlib__matplotlib-22719",
    "matplotlib__matplotlib-23412",
    "matplotlib__matplotlib-24026",
    "matplotlib__matplotlib-24149",
    "matplotlib__matplotlib-24570",
    "matplotlib__matplotlib-24637",
    "matplotlib__matplotlib-24970",
    "matplotlib__matplotlib-25122",
    "matplotlib__matplotlib-25775",
    "matplotlib__matplotlib-26113",
    "matplotlib__matplotlib-26291",
    "matplotlib__matplotlib-26342",
    "pallets__flask-5014",
    "psf__requests-1724",
    "psf__requests-1766",
    "psf__requests-1921",
    "psf__requests-2317",
    "psf__requests-2931",
    "pydata__xarray-3151",
    "pydata__xarray-3677",
    "pydata__xarray-4075",
    "pydata__xarray-4356",
    "pydata__xarray-4629",
    "pydata__xarray-4966",
    "pylint-dev__pylint-6903",
    "pylint-dev__pylint-7277",
    "pytest-dev__pytest-5631",
    "pytest-dev__pytest-5809",
    "pytest-dev__pytest-6202",
    "pytest-dev__pytest-7236",
    "pytest-dev__pytest-7432",
    "pytest-dev__pytest-7571",
    "pytest-dev__pytest-8399",
    "scikit-learn__scikit-learn-10297",
    "scikit-learn__scikit-learn-10844",
    "scikit-learn__scikit-learn-10908",
    "scikit-learn__scikit-learn-11310",
    "scikit-learn__scikit-learn-11578",
    "scikit-learn__scikit-learn-12585",
    "scikit-learn__scikit-learn-13142",
    "scikit-learn__scikit-learn-13328",
    "scikit-learn__scikit-learn-13439",
    "scikit-learn__scikit-learn-13779",
    "scikit-learn__scikit-learn-14053",
    "scikit-learn__scikit-learn-14141",
    "scikit-learn__scikit-learn-14496",
    "scikit-learn__scikit-learn-14894",
    "scikit-learn__scikit-learn-15100",
    "scikit-learn__scikit-learn-25232",
    "scikit-learn__scikit-learn-25931",
    "scikit-learn__scikit-learn-26323",
    "scikit-learn__scikit-learn-9288",
    "sphinx-doc__sphinx-10449",
    "sphinx-doc__sphinx-8269",
    "sphinx-doc__sphinx-8595",
    "sphinx-doc__sphinx-8721",
    "sphinx-doc__sphinx-9320",
    "sphinx-doc__sphinx-9367",
    "sphinx-doc__sphinx-9698",
    "sphinx-doc__sphinx-9711",
    "sympy__sympy-12096",
    "sympy__sympy-12481",
    "sympy__sympy-13372",
    "sympy__sympy-13480",
    "sympy__sympy-13877",
    "sympy__sympy-14531",
    "sympy__sympy-14711",
    "sympy__sympy-14976",
    "sympy__sympy-15349",
    "sympy__sympy-15875",
    "sympy__sympy-16766",
    "sympy__sympy-16886",
    "sympy__sympy-18189",
    "sympy__sympy-18763",
    "sympy__sympy-19040",
    "sympy__sympy-19637",
    "sympy__sympy-20154",
    "sympy__sympy-20801",
    "sympy__sympy-21847",
    "sympy__sympy-22456",
    "sympy__sympy-22714",
    "sympy__sympy-22914",
    "sympy__sympy-23534",
    "sympy__sympy-23824",
    "sympy__sympy-23950",
    "sympy__sympy-24066",
    "sympy__sympy-24213",
    "sympy__sympy-24443",
    "sympy__sympy-24539"
  ]

def find_resolved_instance_reports(root_dir):
    resolved_map = {}
    resolved_patches = {}
    root_path = Path(root_dir)

    for report_path in root_path.rglob("report.json"):
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            if len(data) != 1:
                print(f"Unexpected format in {report_path}")
                continue

            instance_id = next(iter(data))
            report = data[instance_id]


            if report.get("resolved") is True:
                if instance_id not in resolved_map:
                    resolved_map[instance_id] = []
                if instance_id not in resolved_patches:
                    resolved_patches[instance_id] = []
                path = str(report_path.resolve())
                if path not in resolved_map[instance_id]:
                    resolved_map[instance_id].append(path)
                patch_path = report_path.parent / "patch.diff"
                if patch_path.exists():
                    patch_path = str(patch_path.resolve())
                    # read patch content
                    with open(patch_path, "r") as patch_file:
                        patch_content = patch_file.read()
                    if patch_content not in resolved_patches[instance_id]:
                        resolved_patches[instance_id].append(patch_content)

        except Exception as e:
            print(f"Failed to process {report_path}: {e}")

    return resolved_map, resolved_patches

def get_original_patch(instance_id):
    # read jsonl file 
    jsonl_path = Path("all_preds_original.jsonl")
    if not jsonl_path.exists():
        print(f"Original agentless resolved file {jsonl_path} does not exist.")
        return None
    with open(jsonl_path, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["instance_id"] == instance_id:
                return data.get("model_patch")


if __name__ == "__main__":
    base_dir = "logs/run_evaluation"
    output_file = "resolved_instance_merged.json"
    patch_file = "resolved_instance_merged_patches.json"

    resolved_instances, resolved_patches = find_resolved_instance_reports(base_dir)

    with open(output_file, "w") as f:
        json.dump(resolved_instances, f, indent=2)
    
    with open(patch_file, "w") as f:
        json.dump(resolved_patches, f, indent=2)
    
    print(f"Agentless resolved instances found: {len(original_agentless_resolved)}")

    print(f"Saved {len(resolved_instances)} resolved instance reports to {output_file}")
    print(f"Saved {len(resolved_patches)} resolved instance patches to {patch_file}")
    print(resolved_instances.keys())

    # Check if the resolved instances match the original agentless resolved list
    original_set = set(original_agentless_resolved)
    found_set = set(resolved_instances.keys())
    missing_instances = original_set - found_set
    extra_instances = found_set - original_set

    print("Extra instances found in resolved reports:")
    for instance in extra_instances:
        print(instance)
        print(resolved_instances[instance])
        print(f"Number of unique patches: {len(resolved_instances[instance])}")
        for path in resolved_instances[instance]:
            patch_path = path.replace("report.json", "patch.diff")
            # print patch content
            if os.path.exists(patch_path):
                with open(patch_path, "r") as patch_file:
                    print(f"New patch:\n")
                    print(patch_file.read())
            else:
                print(f"Patch file {patch_path} does not exist.")

        original_patch = get_original_patch(instance)
        print(f"Original patch:\n{original_patch}")
