# %%
import pandas as pd

from dataclasses import dataclass

from ghapi.all import GhApi

import requests

import functools

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

import tqdm

import os

from unidiff import PatchSet

import collections

import re


# %%
df = pd.read_json("/home/jeffreyma/scratch/swebench/tasks/xarray-task-instances.jsonl.all", lines=True)

pr_df = pd.read_json("/home/jeffreyma/scratch/swebench/pull_requests/xarray-prs.jsonl", lines=True)

# %%
tasks_with_no_test_patch = df[df['test_patch'].astype(bool) != True]

print("number of tasks:", len(df))
print("number of tasks with no test patch:", len(tasks_with_no_test_patch))

# %%
valid_counter = 0

GET_SOURCE_FILE_REGEX = r"--- (.*?)\n"
GET_DEST_FILE_REGEX = r"\+\+\+ (.*?)\n"

def remove_diff_prefix(elem):
    f1, f2, diff = elem

    if f1.startswith("a/"):
        f1 = f1[2:]

    if f2.startswith("b/"):
        f2 = f2[2:]

    return f1, f2, diff

def raw_diff_to_details(raw_diff, remove_prefix=True):
    split_by_diff = patch.split("diff --git")[1:]

    edits = []
    
    for raw_diff in split_by_diff:
        raw_diff_split_by_lines = raw_diff.splitlines(True)
    
        source_file_match = re.search(GET_SOURCE_FILE_REGEX, raw_diff)
        dst_file_match = re.search(GET_DEST_FILE_REGEX, raw_diff)

        if not source_file_match or not dst_file_match:
            raise ValueError("regex match failed")

        source_file = source_file_match.group(1)
        dst_file = dst_file_match.group(1)

        index = 2
        for line in raw_diff_split_by_lines[2:]:
            if line.startswith("@@"):
                break
            index += 1

        diff_lines = []
        for l in raw_diff_split_by_lines[index:]:
            if l.startswith("@@"):
                l_components = l.split("@@")[:-1] + ["\n"]
                diff_lines.append("@@".join(l_components))
            else:
                diff_lines.append(l)


        diff = "".join(diff_lines)    
        edits.append((source_file, dst_file, diff))

    if remove_prefix:
        edits = [remove_diff_prefix(e) for e in edits]
    
    return edits


kept_indices = []
for i, example in tasks_with_no_test_patch.iterrows():
    patch = example.patch

    try:
        edits = raw_diff_to_details(patch)
    except Exception as e:
        continue

    # Ignore tasks where we delete or create full files (i.e. ou
    if any('/dev/null' in f for f, _, _ in edits):
        continue

    # Ignore tasks where all edited files are hidden.
    if all(f.startswith(".") for f, _, _ in edits):
        continue

    # Ignore tasks where all edits are not python.
    if not all(".py" in f for f, _, _ in edits):
        continue

    # Ignore tasks where first file and second file are not equal
    if not all(f1 == f2 for f1, f2, _ in edits):
        continue

    kept_indices.append(i)

# New df of indices.
filtered_df = df[df.index.isin(kept_indices)]

print("number of tasks with no test patch and only python edits:", len(filtered_df))

# %%
filtered_df

# %%
api = GhApi()

# TODO: Temporary to play with.
OWNER = "pydata"
REPO = "xarray"

@functools.cache
def get_source_files(pull_number):
    example = api.pulls.list_files(OWNER, REPO, pull_number, 100)

    source_files = dict()
    
    for e in example:
        filename = e['filename']
        source = requests.get(e["raw_url"]).text
        source_files[filename] = source

    return source_files


# %%
NUM_ELEMS = 500
pull_number_to_postedit_files = {}

for i, row in tqdm.tqdm(filtered_df.head(NUM_ELEMS).iterrows(), total=NUM_ELEMS, desc="getting pulls and file info..."):
    pull_number = row['pull_number']
    filename_to_source = get_source_files(pull_number)
    pull_number_to_postedit_files[pull_number] = filename_to_source

# %%
from diff_match_patch import diff_match_patch

def invert_diff(diff):
    diff_split_by_lines = diff.splitlines(True)
    inverted_diff_split_by_lines = []
    for l in diff_split_by_lines:
        if l.startswith("+"):
            inverted_diff_split_by_lines.append("-" + l[1:])
        elif l.startswith("-"):
            inverted_diff_split_by_lines.append("+" + l[1:])
        elif l.startswith("@@"):
            l_components = l.split()
            l_components[1], l_components[2] = l_components[2], l_components[1]
            l_components[1] = l_components[1].replace("+", "-")
            l_components[2] = l_components[2].replace("-", "+")

            inverted_diff_split_by_lines.append(" ".join(l_components) + "\n")
        else:
            inverted_diff_split_by_lines.append(l)

    inverted_diff = "".join(inverted_diff_split_by_lines)
    
    return inverted_diff

_no_eol = "\ No newline at end of file"
_hdr_pat = re.compile("^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@$")

def apply_patch(s,patch,revert=False):
  """
  Apply patch to string s to recover newer string.
  If revert is True, treat s as the newer string, recover older string.
  """
  s = s.splitlines(True)
  p = patch.splitlines(True)
  t = ''
  i = sl = 0
  (midx,sign) = (1,'+') if not revert else (3,'-')
  while i < len(p) and p[i].startswith(("---","+++")): i += 1 # skip header lines
  while i < len(p):
    m = _hdr_pat.match(p[i])
    if not m: raise Exception("Bad patch -- regex mismatch [line "+str(i)+"]")
    l = int(m.group(midx))-1 + (m.group(midx+1) == '0')
    if sl > l or l > len(s):
      raise Exception("Bad patch -- bad line num [line "+str(i)+"]")
    t += ''.join(s[sl:l])
    sl = l
    i += 1
    while i < len(p) and p[i][0] != '@':
      if i+1 < len(p) and p[i+1][0] == '\\': line = p[i][:-1]; i += 2
      else: line = p[i]; i += 1
      if len(line) > 0:
        if line[0] == sign or line[0] == ' ': t += line[1:]
        sl += (line[0] != sign)
  t += ''.join(s[sl:])
  return t

import tempfile
import subprocess

def revert_patch(postedit_source, patch):
    with tempfile.NamedTemporaryFile() as source_temp_file:
        source_temp_file.write(postedit_source.encode('utf-8'))
 
        patch_data = patch.encode('utf-8')

        subprocess.run(
            ["patch", "-R", source_temp_file.name], 
            input=patch_data,  # pass patch data via stdin
            # stdout=subprocess.DEVNULL
        )

        source_temp_file.seek(0)
        updated = source_temp_file.read().decode('utf-8')
        return updated
   

# %%
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

def check_if_equal(n1, n2):
    if n1.type != n2.type:
        return False

    return True

def traverse_subtree(n1, n2, ignore_func=None):
    root_nodes_equal = check_if_equal(n1, n2)
    if not root_nodes_equal:
        return False

    n1_children = n1.children
    n2_children = n2.children

    # Filter out nodes of comment type.
    filtered_n1_children = [n for n in n1_children if not ignore_func(n)]
    filtered_n2_children = [n for n in n2_children if not ignore_func(n)]

    if len(filtered_n1_children) != len(filtered_n2_children):
        return False

    for child1, child2 in zip(filtered_n1_children, filtered_n2_children):
        if not traverse_subtree(child1, child2, ignore_func=ignore_func):
            return False
    
    return True

def traverse_tree(t1, t2, ignore_func=lambda n: n.type == 'comment'):
    return traverse_subtree(t1.root_node, t2.root_node, ignore_func=ignore_func)

    

# %%

semantically_meaningful_edits = []

pull_number_to_pre_and_postedit_files = dict()

for pull_number, file_to_source in pull_number_to_postedit_files.items():
    df_row = df[df['pull_number'] == pull_number].iloc[0]

    patch = df_row['patch']
    edits = raw_diff_to_details(patch)

    filename_to_diffs = {
        f: diff for f, _, diff in edits
    }

    filename_to_preedit = dict()
    for f in filename_to_diffs:
        post_edit_source = file_to_source[f]
        diff = filename_to_diffs[f]
        inverse_diff = invert_diff(diff)
        
        # preedit_source = revert_patch(post_edit_source, diff)  
        preedit_source = apply_patch(post_edit_source, inverse_diff)   
        filename_to_preedit[f] = preedit_source

        assert preedit_source.strip() != post_edit_source.strip(), "pre and post edit is the same"

    equiv_statuses = []
    
    for f in filename_to_preedit:
        preedit_source = filename_to_preedit[f]
        postedit_source = file_to_source[f]
        diff = filename_to_diffs[f]
        
        # Run both through tree-sitter.
        preedit_tree = parser.parse(
            bytes(preedit_source, "utf8"))
        postedit_tree = parser.parse(
            bytes(postedit_source, "utf8"),
        )

        check_serialized_equiv = str(preedit_tree.root_node) == str(postedit_tree.root_node)
        check_tree_equiv = traverse_tree(preedit_tree, postedit_tree)
        equiv_statuses.append(check_tree_equiv)

    # All edits do not meaningfully transform the syntax tree.
    if all(equiv_statuses):
        continue

    # Otherwise, track this.
    semantically_meaningful_edits.append(pull_number)
    
    pull_number_to_pre_and_postedit_files[pull_number] = {
        'preedit': filename_to_preedit,
        'postedit': file_to_source
    }

       
semantically_meaningful_edits_df = filtered_df[filtered_df['pull_number'].isin(semantically_meaningful_edits)]

print(len(semantically_meaningful_edits_df))



# %%

KEYWORDS = ['performance', 'speed', 'optimize', 'fast']

counter = 0 
for i, e in semantically_meaningful_edits_df.iterrows():
    
    pull_number = e['pull_number']
    pr_info = pr_df[pr_df['number'] == pull_number].iloc[0]
    
    # is performance related
    perf_in_title = any(kw in pr_info['title'].lower() if pr_info['title'] else False for kw in KEYWORDS)
    perf_in_body = any(kw in pr_info['body'].lower() if pr_info['body'] else False for kw in KEYWORDS)
    
    if not perf_in_title and not perf_in_body:
        continue
    
    print("=" * 100)
    print("PR number:", pull_number)
    print(pr_info['title'])
    print(pr_info['body']) 
    
    counter += 1
print(counter)
   

# %%

pr_df

# %%

pull_number_to_pre_and_postedit_files[9856]

INSTRUCTION = """You are an excellent performance engineer. Please identify opportunities for performance optimization in the following source code files."""

PER_FILE_TEMPLATE = """
File: {filename}
```
{source}
```

"""

def get_preedit_prompt(pull_number):
    preedit_files = pull_number_to_pre_and_postedit_files[pull_number]['preedit']
    
    components = [INSTRUCTION]
    
    for f, source in preedit_files.items():
        components.append(PER_FILE_TEMPLATE.format(filename=f, source=source))

    return "\n\n".join(components)

print(get_preedit_prompt(9856))
# %%
