#!/usr/bin/env bash

# If you'd like to parallelize, do the following:
# * Create a .env file in this folder
# * Declare GITHUB_TOKENS=token1,token2,token3...

# python get_tasks_pipeline.py \
#     --repos 'scikit-learn/scikit-learn', 'pallets/flask' \
#     --path_prs '<path to folder to save PRs to>' \
#     --path_tasks '<path to folder to save tasks to>'

# python get_tasks_pipeline.py \
#     --repos  'pydata/xarray' \
#     --path_prs '/home/jeffreyma/scratch/swebench/pull_requests/' \
#     --path_tasks '/home/jeffreyma/scratch/swebench/tasks/'

python get_tasks_pipeline.py \
    --repos  'scikit-learn/scikit-learn', 'astropy/astropy', 'django/django', 'matplotlib/matplotlib', 'mwaskom/seaborn', 'psf/requests', 'pylint-dev/pylint', 'sympy/sympy', 'sphinx-doc/sphinx' \
    --path_prs '/home/jeffreyma/scratch/swebench/pull_requests/' \
    --path_tasks '/home/jeffreyma/scratch/swebench/tasks/'
