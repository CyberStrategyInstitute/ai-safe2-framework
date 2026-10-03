"""Provider-neutral adapter contracts and conformance evaluation."""

from .conformance import AdapterError, evaluate_conformance, load_json_regular

__all__ = ["AdapterError", "evaluate_conformance", "load_json_regular"]
