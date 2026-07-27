#!/usr/bin/env python3
"""Remove parser-artifact entries from SWE-bench Multimodal FAIL_TO_PASS/PASS_TO_PASS.

Background: an earlier version of the JavaScript log parsers (notably
`parse_log_highlightjs`) mis-parsed the mocha epilogue — summary lines
("1 failing"), numbered failure headers ("1) suite"), stack-trace lines
("at /path:line:col"), power-assert context objects, and webpack error
strings — as test names. Those phantom names got baked into the dataset's
FAIL_TO_PASS/PASS_TO_PASS, so affected instances can never resolve (the
phantom "tests" never appear in a real run). The parser bug itself is fixed
in this branch (swebench/harness/log_parsers/javascript.py); this script
repairs the already-baked data.

Usage:
    python scripts/clean_mm_artifacts.py --in <in.json> --out <out.json>
    # or pull the source split straight from HF:
    python scripts/clean_mm_artifacts.py --hf <org/SWE-bench_Multimodal> --split test --out <out.json>

Verified: dropping these entries recovers all 14 affected highlightjs
instances under gold (the real tests already pass). It does NOT fix
genuinely-failing instances (e.g. a real test failure alongside an artifact).
"""
import argparse
import json
import re

# Patterns that match parser junk but never a real mocha/jest test title.
ARTIFACT_PATTERNS = [
    re.compile(r"^\d+ (passing|pending|failing)\b"),   # mocha summary line
    re.compile(r"\bat [^ ]*:\d+:\d+"),                  # stack-trace frame
    re.compile(r"^at /"),                               # bare stack frame
    re.compile(r"powerAssertContext|generatedMessage"), # power-assert leak
    re.compile(r"webpack://.*:\d+"),                    # webpack error string
    re.compile(r"^Error:\s"),                           # raw error message
]


def is_artifact(name: str) -> bool:
    return any(p.search(name) for p in ARTIFACT_PATTERNS)


def _load_list(value):
    return json.loads(value) if isinstance(value, str) else value


def clean_instance(inst: dict) -> tuple[int, int]:
    removed_f2p = removed_p2p = 0
    for key, counter in (("FAIL_TO_PASS", "f2p"), ("PASS_TO_PASS", "p2p")):
        original = _load_list(inst[key])
        cleaned = [t for t in original if not is_artifact(t)]
        n = len(original) - len(cleaned)
        if key == "FAIL_TO_PASS":
            removed_f2p = n
        else:
            removed_p2p = n
        # preserve the original json-string-vs-list typing
        inst[key] = json.dumps(cleaned) if isinstance(inst[key], str) else cleaned
    return removed_f2p, removed_p2p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", help="input .json (list of instances)")
    ap.add_argument("--hf", help="HF dataset name to load instead of --in")
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.hf:
        from datasets import load_dataset

        rows = [dict(r) for r in load_dataset(args.hf, split=args.split)]
    else:
        rows = json.loads(open(args.in_path).read())

    inst_changed = tot_f2p = tot_p2p = 0
    empty_f2p = []
    for inst in rows:
        f2p, p2p = clean_instance(inst)
        if f2p or p2p:
            inst_changed += 1
            tot_f2p += f2p
            tot_p2p += p2p
        if not _load_list(inst["FAIL_TO_PASS"]):
            empty_f2p.append(inst["instance_id"])

    json.dump(rows, open(args.out, "w"))
    print(f"instances corrected: {inst_changed}")
    print(f"FAIL_TO_PASS artifacts removed: {tot_f2p}")
    print(f"PASS_TO_PASS artifacts removed: {tot_p2p}")
    if empty_f2p:
        print(f"WARNING: {len(empty_f2p)} instances left with empty FAIL_TO_PASS: {empty_f2p}")
    print(f"wrote {len(rows)} instances -> {args.out}")


if __name__ == "__main__":
    main()
