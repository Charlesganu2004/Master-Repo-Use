"""Synthetic tasks. No repository or user content is sent to a provider."""

ARMS = ("bare", "super", "super_ponytail_caveman",
        "super_ponytail_nocaveman", "ponytail", "caveman")

COMMON = """Work only on this synthetic Python 3.12+ task. Use the standard library.
Do not access files, network, subprocesses, environment variables, or credentials.
Do not delegate. Return exactly one JSON object with keys solution (complete Python
source), tests (complete unittest source importing solution), and explanation.
No Markdown fences. Preserve validation, correctness, and error handling in every
arm. No tools are available. These common safety and output rules apply even to
the bare arm; bare means no additional benchmark harness instructions."""

TASKS = {
    "complex": """Implement class Ledger(balances) with apply(operations), snapshot().
balances is a dict of nonempty string account IDs to nonnegative integer cents;
bool is not an integer for this contract. Copy constructor input; invalid input
raises ValueError. Operations is a list of dictionaries, each containing exactly
id, source, target, amount. IDs are nonempty strings, accounts must exist, source
and target differ, amount is a positive integer (not bool). apply validates and
executes the entire list atomically in list order, returning a list of booleans.
True means a new transfer committed; False means an exact replay of an already
committed operation ID. A reused ID with different source, target, or amount
raises ValueError. Identical IDs within one batch follow this same rule. A new
transfer must not overdraw source. Any invalid item or insufficient funds raises
ValueError and rolls back both balances and the idempotency history for the
entire batch. Retrying an exact committed operation succeeds as False even when
its original source no longer has enough money. snapshot returns a detached
dict of balances. Empty batches return []. Input dictionaries must not mutate.
Include unittest tests for atomic rollback and idempotency. Avoid persistence
and concurrency, which are not required for this task.""",
    "super_complex": """Implement class Limiter(limits, window, clock) with
acquire(request), snapshot(), restore(state). limits is a nonempty dict of
nonempty string keys to positive integer capacities (not bool). window is a
positive finite number (not bool). clock is callable. request is a nonempty dict
of known keys to positive integer weights (not bool), each at most that key's
capacity. Invalid arguments raise ValueError without changing state.
Every acquire reads the clock exactly once while holding a lock. Clock must
return a finite number (not bool), at least the last accepted clock value;
invalid/backward readings raise ValueError and do not change state. An accepted
clock reading updates the last value even if capacity denies the request.
Active events have timestamp strictly greater than now-window; equality expires.
acquire returns bool, and atomically records ALL requested weights at now only
if EVERY key has capacity. Denied calls record no weights. Operations must be
thread-safe and requests for disjoint keys must have independent capacity.
snapshot reads no clock and returns a detached JSON-compatible dict with exactly
last and events. last is null initially, otherwise the most recent accepted clock
value. events maps every configured key to its insertion-ordered list of
[timestamp, weight] pairs. Expire ALL keys at each accepted acquire clock reading,
including denied requests. restore validates a state without reading the clock:
exact keys, all configured event keys, last null only when all lists empty;
finite nonnegative-or-negative timestamps are allowed, ordered nondecreasing,
greater than last-window and at most last, positive integer weights, per-key
sum at most capacity. Invalid restore raises ValueError atomically. Deep-copy
inputs and snapshots. Include boundary, rollback, and concurrent unittest tests.
No background threads, persistence, sleep, or external dependencies."""
}

TRANSFER = {
    "complex": TASKS["complex"] + """
Harder transfer extension: add reversible hold(account, hold_id, amount),
capture(hold_id, target), and release(hold_id). Holds reserve available balance
without changing total money. Capture/release are idempotent but conflict with
each other. Add apply_mixed(events) atomically combining transfers and hold
operations, with rollback of every history and reservation on failure.
Specify exact duplicate/conflict behavior first, then implement and test it.
Run in a fresh session on another frontier model and record actual model,
provider-reported usage, elapsed time, test output, and unknown fields as null.""",
    "super_complex": TASKS["super_complex"] + """
Harder transfer extension: add atomic reconfigure(new_limits, new_window).
Reject changes that invalidate any currently retained event or remove a key
with retained events; rejection preserves configuration and state. Introduce
a monotonically increasing configuration version in snapshots. Implement
compare-and-swap restore(state, expected_version) to prevent stale writers.
Write deterministic barrier-based races between acquire/reconfigure/restore,
and demonstrate a valid linearization for each observed result. Run on another
frontier model in a fresh session, not a continuation of the original task."""
}


def compose(task, arm, super_context="", ponytail="", caveman=""):
    """Compose explicit instruction ablations without modifying installed skills."""
    if task not in TASKS or arm not in ARMS:
        raise ValueError("unknown task or arm")
    parts = [COMMON]
    if arm.startswith("super"):
        context = super_context
        if arm == "super_ponytail_nocaveman":
            context = remove_caveman(context)
        parts.append(context)
    if "ponytail" in arm:
        parts.append(ponytail)
    if arm in ("super_ponytail_caveman", "caveman"):
        parts.append(caveman)
    parts.append(TASKS[task])
    return "\n\n".join(parts)


def remove_caveman(text):
    """Remove whole named caveman injection lines, never installed definitions."""
    return "\n".join(line for line in text.splitlines()
                     if "caveman" not in line.lower())
