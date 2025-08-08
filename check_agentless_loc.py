import json
from pathlib import Path

# Paths to the input files
jsonl_path = "/data/workspace/yang/Agentless/agentless_swebench_verified/edit_location_samples/loc_outputs.jsonl"
json_path = "/data/workspace/yang/agent/result_files/confirmed_suspicious_funcs.json"
output_path = "method_comparison_results.json"

# Load the JSONL data
found_related_locs = {}
with open(jsonl_path, "r") as f:
    for line in f:
        item = json.loads(line)
        instance_id = item["instance_id"]
        related = item.get("found_related_locs", {})
        methods = set()
        for file, entries in related.items():
            for entry in entries:
                for e in entry.split("\n"):
                    if e.startswith("function:"):
                        methods.add(e.replace("function: ", "").strip())
        found_related_locs[instance_id] = {
            "methods": methods,
            "files": set(related.keys())
        }

# Load the new JSON data
with open(json_path, "r") as f:
    new_data = json.load(f)

# Collect comparison results
results = []
for instance_id in found_related_locs:
    if instance_id not in new_data:
        continue
    agentless_methods = found_related_locs[instance_id]["methods"]
    agentless_files = found_related_locs[instance_id]["files"]

    new_methods = set()
    new_files = set(new_data[instance_id].keys())
    for file, method_list in new_data[instance_id].items():
        new_methods.update(method_list)

    result = {
        "instance_id": instance_id,
        "agentless_method_count": len(agentless_methods),
        "agentless_file_count": len(agentless_files),
        "new_method_count": len(new_methods),
        "new_file_count": len(new_files),
        "common_methods": sorted(agentless_methods & new_methods),
        "agentless_only_methods": sorted(agentless_methods - new_methods),
        "new_only_methods": sorted(new_methods - agentless_methods),
        "agentless_all_methods": sorted(agentless_methods),
        "new_all_methods": sorted(new_methods),
        "agentless_files": sorted(agentless_files),
        "new_files": sorted(new_files)
    }
    results.append(result)

# Save to JSON
with open(output_path, "w") as out_f:
    json.dump(results, out_f, indent=2)

print(f"Results saved to {output_path}")
