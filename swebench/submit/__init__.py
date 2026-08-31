"""Submission tooling: prepare, publish, and register a run's results.

Two independent destinations live here:

* the SWE-bench leaderboard, via github.com/SWE-bench/experiments (``package``,
  ``publish``, ``register``, ``verify``)
* HuggingFace's community eval-results system (``hf``)

Nothing in this package is imported by the harness; it only reads what a finished
evaluation left on disk.
"""
