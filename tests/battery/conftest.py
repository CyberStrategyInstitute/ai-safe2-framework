# The battery is a standalone harness (tests/battery/run.py), not a pytest suite.
# Its fixtures include deliberately hostile code and servers; never collect them.
collect_ignore_glob = ["*"]
