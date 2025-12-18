def run_instances_beam(*args, **kwargs):
    """Lazy import wrapper for run_instances_beam."""
    from swebench.harness.beam_eval.run_evaluation_beam import run_instances_beam as _run_instances_beam
    return _run_instances_beam(*args, **kwargs)


def validate_beam_credentials():
    """Lazy import wrapper for validate_beam_credentials."""
    from swebench.harness.beam_eval.utils import validate_beam_credentials as _validate_beam_credentials
    return _validate_beam_credentials()


__all__ = [
    "run_instances_beam",
    "validate_beam_credentials",
]
