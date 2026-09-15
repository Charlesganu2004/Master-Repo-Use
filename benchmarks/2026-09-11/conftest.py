# This directory holds benchmark inputs and model-written outputs, not the
# repository's tests. Agent answers include files that look like tests, and a
# bare `pytest` from the repo root would otherwise collect and run them.
collect_ignore_glob = ["*"]
